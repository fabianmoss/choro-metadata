import { readFileSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { Store, Parser, DataFactory } from 'n3'
import { Validator } from 'shacl-engine'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = join(__dirname, '..')                                 // Bestimmt die Wurzel der Javascript Validator Datei

const SHAPES_BASE_URL =
    'https://raw.githubusercontent.com/Music-Metadata-Tools/MerMEId-MeLODy/main/configuration/'

const TERMS_URL =
    'https://mermeid-data-model-efbf77.pages.gitlab.rlp.net/melod-terms.ttl'

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

// Parsed ttl Datei und gibt es als Javascript Objekt zurück
async function fetchAndParse(url) {
    const r = await fetch(url)
    if (!r.ok) throw new Error(`Could not fetch ${url}: HTTP ${r.status}`)
    return new Parser().parse(await r.text())
}

// Liest Shacl-Shapes ein
const shapeCache = {}
function loadShape(shapeFile) {
    if (!shapeCache[shapeFile]) {
        shapeCache[shapeFile] = fetchAndParse(SHAPES_BASE_URL + shapeFile)
            .then(quads => new Store(quads))
    }
    return shapeCache[shapeFile]
}

// ── Phase 1: alle Dateien laden ───────────────────────────────────────────────

// Subject-IRI → Datei-Label (damit Violations später der richtigen Datei zugeordnet werden)
const iriToFile = new Map()
const allQuads = [...await fetchAndParse(TERMS_URL)]
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
            for (const quad of quads) {
                if (!iriToFile.has(quad.subject.value)) {
                    iriToFile.set(quad.subject.value, label)
                }
            }
            allQuads.push(...quads)
        } catch (e) {
            console.error(`✗ ${label}: ${e.message}`)
            hasErrors = true
        }
    }
}

const combinedStore = new Store(allQuads)

// ── Phase 2: validieren ───────────────────────────────────────────────────────

// Violations gruppiert nach Datei sammeln
const violationsByFile = new Map()

for (const [folder, shapeFile] of Object.entries(FOLDER_TO_SHAPE)) {
    const shapesStore = await loadShape(shapeFile)
    const validator = new Validator(shapesStore, { factory: DataFactory })
    const report = await validator.validate({ dataset: combinedStore })

    for (const r of report.results) {
        const fileLabel = iriToFile.get(r.focusNode?.value)
        if (!fileLabel?.startsWith(folder + '/')) continue

        if (!violationsByFile.has(fileLabel)) violationsByFile.set(fileLabel, [])
        violationsByFile.get(fileLabel).push(r)
    }
}

// ── Phase 3: ausgeben ─────────────────────────────────────────────────────────

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

        if (violations.length === 0) {
            console.log(`✓ ${label}`)
        } else {
            console.error(`✗ ${label}`)
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
            hasErrors = true
        }
    }
}

if (hasErrors) process.exit(1)
