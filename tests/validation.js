import { readFileSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { Store, Parser, DataFactory } from 'n3'
import { Validator } from 'shacl-engine'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = join(__dirname, '..')

const SHAPES_BASE_URL =
    'https://raw.githubusercontent.com/Music-Metadata-Tools/MerMEId-MeLODy/main/configuration/'

const TERMS_URL =
    'https://mermeid-data-model-efbf77.pages.gitlab.rlp.net/melod-terms.ttl'

const RDF_TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
const MELOD_NAMESPACE = 'https://lod.academy/melod/vocab/ontology#'

const FOLDER_TO_SHAPE = {
    bibliography:      'bibliography.shacl',
    expressions:       'expression.shacl',
    institutions:      'institution.shacl',
    instrumentations:  'instrumentation.shacl',
    items:             'item.shacl',
    manifestations:    'manifestation.shacl',
    performanceEvents: 'performanceEvent.shacl',
    persons:           'person.shacl',
    places:            'place.shacl',
    venues:            'venue.shacl',
    works:             'work.shacl',
}

// The editor derives the shape of a document from its folder and the entity
// type from the document itself (see MerMEId-MeLODy, modules/entity-editor).
// A document whose type does not match its folder cannot be edited.
const FOLDER_TO_TYPE = {
    bibliography:      'melod:Bibliography',
    expressions:       'melod:Expression',
    institutions:      'melod:Institution',
    instrumentations:  'melod:Instrumentation',
    items:             'melod:Item',
    manifestations:    'melod:Manifestation',
    performanceEvents: 'melod:PerformanceEvent',
    persons:           'melod:Person',
    places:            'melod:Place',
    venues:            'melod:Venue',
    works:             'melod:Work',
}

// Parses a Turtle document and returns its quads.
async function fetchAndParse(url) {
    const r = await fetch(url)
    if (!r.ok) throw new Error(`Could not fetch ${url}: HTTP ${r.status}`)
    return new Parser().parse(await r.text())
}

const shapeCache = {}
function loadShape(shapeFile) {
    if (!shapeCache[shapeFile]) {
        shapeCache[shapeFile] = fetchAndParse(SHAPES_BASE_URL + shapeFile)
    }
    return shapeCache[shapeFile]
}

/**
 * Replicates the editor's entity type detection
 * (MerMEId-MeLODy, js/index.js: SparqlQueries.entity_type_detection).
 *
 *     select ?entity_iri ?entity_type where {
 *         ?entity_iri a ?entity_type .
 *         filter(strstarts(str(?entity_iri), "urn:uuid:"))
 *         filter(strstarts(str(?entity_type), ".../vocab/ontology#"))
 *     }
 *
 * The editor refuses to open a document unless the query returns exactly one
 * row, so an entity must be typed with exactly one class of the melod
 * ontology.  The *Entity classes (melod:ExpressionEntity and so on) belong to
 * the generated indexes, not to the entity documents.
 */
function entityTypeStatements(quads) {
    const rows = []
    for (const quad of quads) {
        if (quad.predicate.value !== RDF_TYPE) continue
        if (quad.subject.termType !== 'NamedNode') continue
        if (!quad.subject.value.startsWith('urn:uuid:')) continue
        if (quad.object.termType !== 'NamedNode') continue
        if (!quad.object.value.startsWith(MELOD_NAMESPACE)) continue
        rows.push({ iri: quad.subject.value, type: quad.object.value })
    }
    return rows
}

// ── Phase 1: load the entity documents ───────────────────────────────────────

// Subject IRI → file label, so that violations are attributed to their file.
const iriToFile = new Map()
const fileQuads = new Map()
const dataQuads = []
let hasErrors = false

for (const folder of Object.keys(FOLDER_TO_SHAPE)) {
    const folderPath = join(REPO_ROOT, folder)
    let files
    try {
        files = readdirSync(folderPath).filter(f => f.endsWith('.ttl'))
    } catch {
        continue
    }

    for (const file of files) {
        const label = `${folder}/${file}`
        try {
            const quads = new Parser().parse(readFileSync(join(folderPath, file), 'utf-8'))
            fileQuads.set(label, quads)
            for (const quad of quads) {
                if (!iriToFile.has(quad.subject.value)) {
                    iriToFile.set(quad.subject.value, label)
                }
            }
            dataQuads.push(...quads)
        } catch (e) {
            console.error(`✗ ${label}: ${e.message}`)
            hasErrors = true
        }
    }
}

// ── Phase 2: check the editor's entity type contract ─────────────────────────

const editorErrorsByFile = new Map()

for (const [label, quads] of fileQuads) {
    const folder = label.split('/')[0]
    const expected = FOLDER_TO_TYPE[folder]
    const rows = entityTypeStatements(quads)
    const errors = []

    if (rows.length !== 1) {
        errors.push(
            `${rows.length} statements with entity IRI and entity type ` +
            `(the editor requires exactly 1)`
        )
        for (const row of rows) {
            errors.push(`    ${row.iri} -> ${row.type.split('#').pop()}`)
        }
    } else if (expected && row_to_prefixed(rows[0]) !== expected) {
        errors.push(
            `entity type ${row_to_prefixed(rows[0])} does not belong to the ` +
            `${folder} folder (expected ${expected})`
        )
    }

    if (errors.length > 0) {
        editorErrorsByFile.set(label, errors)
        hasErrors = true
    }
}

function row_to_prefixed(row) {
    return 'melod:' + row.type.slice(MELOD_NAMESPACE.length)
}

// ── Phase 3: validate against the SHACL shapes ───────────────────────────────

// The editor validates a document against the shapes of its entity type and
// against a store that also contains the owl:imports of the shapes (the
// melod terms) and the generated indexes (see MerMEId-MeLODy,
// modules/entity-editor `_getShapeForPath`, and mermeid-shacl-form, which
// validates the whole store).  The shapes of the entity type are part of that
// store as well: the place shape, for instance, declares the countries of
// schema:containedInPlace.  This script mirrors that composition.
const baseQuads = [...await fetchAndParse(TERMS_URL), ...dataQuads]

const indexQuads = []
try {
    for (const file of readdirSync(join(REPO_ROOT, 'indexes')).filter(f => f.endsWith('.ttl'))) {
        indexQuads.push(...new Parser().parse(readFileSync(join(REPO_ROOT, 'indexes', file), 'utf-8')))
    }
} catch {
    console.error('✗ indexes/: missing — run `python3 -m tools.datasets --out indexes`')
    hasErrors = true
}

// Violations grouped by file.
const violationsByFile = new Map()

for (const [folder, shapeFile] of Object.entries(FOLDER_TO_SHAPE)) {
    const shapeQuads = await loadShape(shapeFile)
    const shapesStore = new Store(shapeQuads)
    const dataset = new Store([...baseQuads, ...indexQuads, ...shapeQuads])
    const validator = new Validator(shapesStore, { factory: DataFactory })
    const report = await validator.validate({ dataset })

    for (const r of report.results) {
        const fileLabel = iriToFile.get(r.focusNode?.value)
        if (!fileLabel?.startsWith(folder + '/')) continue

        if (!violationsByFile.has(fileLabel)) violationsByFile.set(fileLabel, [])
        violationsByFile.get(fileLabel).push(r)
    }
}

// ── Phase 4: report ──────────────────────────────────────────────────────────

// A SHACL violation is a failure of the suite, like a malformed document:
// the editor would refuse the data or store it in an invalid state.
if (violationsByFile.size > 0) hasErrors = true

for (const folder of Object.keys(FOLDER_TO_SHAPE)) {
    const folderPath = join(REPO_ROOT, folder)
    let files
    try {
        files = readdirSync(folderPath).filter(f => f.endsWith('.ttl'))
    } catch {
        continue
    }

    for (const file of files) {
        const label = `${folder}/${file}`
        const violations = violationsByFile.get(label) ?? []
        const editorErrors = editorErrorsByFile.get(label) ?? []

        if (violations.length === 0 && editorErrors.length === 0) {
            console.log(`✓ ${label}`)
            continue
        }

        console.error(`✗ ${label}`)
        for (const error of editorErrors) {
            console.error(`    editor: ${error}`)
        }
        for (const r of violations) {
            const path = r.path?.[0]?.predicates?.[0]?.value ?? '?'
            const focusNode = r.focusNode?.value ?? '?'
            const value = r.value?.value ?? ''
            const message = r.message?.[0]?.value
                ?? r.constraintComponent?.value?.replace('http://www.w3.org/ns/shacl#', '')
                ?? '?'
            console.error(`    node:  ${focusNode}`)
            console.error(`    path:  ${path}`)
            console.error(`    error: ${message}${value ? ` (value: ${value})` : ''}`)
            console.error()
        }
    }
}

if (hasErrors) process.exit(1)
