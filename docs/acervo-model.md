# Modelling the Casa do Choro acervo in MeLODy

This document describes how the records of the acervo of the [Casa do
Choro](https://acervo.casadochoro.com.br/) are turned into entities of the
[MerMEId-MeLODy](https://music-metadata-tools.github.io/MerMEId-MeLODy/)
model, and which decisions were taken at each point.

The acervo is the primary source.  The editor is MeLODy, a conceptual model
based on the [LRM](https://www.ifla.org/standards/lrm/) and on FRBR, with its
own vocabulary (`melod:`) and the SHACL shapes that validate it.

## 1. Source

For each work the acervo publishes a record at `/works/view/<id>` with:

| field of the acervo         | content                                         |
|-----------------------------|-------------------------------------------------|
| title                       | name of the composition                         |
| Gênero                      | Polca, Choro, Valsa, Canção Maxixe, Rancheira…   |
| Compasso                    | `2/4`, `3/4`…                                   |
| Compositores                | link to the person record `/cards/view/<id>`    |
| Partituras                  | a list of copies, each with a type, a PDF and the fields “Cópia”, “Data”, “Arranjo”, “Instrumentação”, “Letra” |

The acervo does **not** distinguish work, expression, manifestation and item:
each entry of the “Partituras” list is, in practice, one copy of a score.
The modelling below is what reconstructs that hierarchy.

## 2. The FRBR chain

```
work (melod:Work)
  └── lrmoo:R3_is_realised_in → expression (melod:Expression)
        └── lrmoo:R4_embodies → manifestation (melod:Manifestation)
              └── lrmoo:R7_exemplifies → item (melod:Item)
```

| acervo                                    | entity         | key of the IRI                         |
|-------------------------------------------|----------------|----------------------------------------|
| work record                               | work           | `work:<id>`                            |
| set of scores with the same arranger      | expression     | `expr:<id>:<arranger>`                 |
| set of scores with the same format and the same edition | manifestation | `man:<id>:<edition>:<format>` |
| each entry of the “Partituras” list        | item           | `item:<id>:<index>`                    |
| person record                             | person         | `person:<id of the record>`            |
| place of birth                            | place          | `place:<name>`                         |
| publisher / keeper                         | institution    | `inst:<name>`                          |
| field “Instrumentação”                    | instrumentation | `instr:<label>`                        |
| “Fonte de pesquisa”                       | bibliography   | `bib:<citation>`                       |

**Work.**  One work per record of the acervo.  It receives the title
(`melod:hasTitle` with `terms:MainTitle`), the genre
(`melod:hasClassification`, free string), the authorship
(`melod:hasContribution` → `terms:Composer`, `terms:HighCertainty`) and the
source that grounds the attribution (`schema:citation`).

**Expression.**  A version of the work.  Scores with **different declared
arrangers** or **different score types** (a piano score, a melody score, a
cifra…) are different expressions of the same work.  A score whose type
declares an arrangement but names no arranger forms an **anonymous
arrangement** expression.  The remaining scores with no declared
arrangement form the “original” expression.  It receives the metre
(`melod:hasMeter`), the language (`melod:inLanguage` →
`terms:Portuguese`), the instrumentation (`melod:hasInstrumentation`) and the
agents of the version — arranger (`terms:Arranger`) and librettist
(`terms:Librettist`), both with `terms:MediumCertainty`.

**Manifestation.**  An edition.  Scores of the **same format and the same
edition** form one manifestation, even when they are several different
manuscript copies: the four manuscript copies of “A baianinha” are a single
manifestation with four items.  It receives the format
(`melod:hasClassificationOfManifestation`, with the string of the acervo and
the term `terms:Manuscript` or `terms:Print`), the publisher
(`melod:hasContribution` → `terms:Publisher`) and the publication event
(`schema:publication`).

**Item.**  A physical copy.  One entry of the “Partituras” list of the acervo.
It receives the copyist (`melod:hasHand` → `melod:Hand` with `terms:Writer`),
the date of the copy (`melod:hasProvenance` → `melod:Event` with
`melod:ExactDate`), the provenance (`melod:hasProvenance` with
`terms:FormerOwner` and `terms:Donor`), the access restriction
(`melod:hasAnnotation`) and the keeping institution
(`cidoc:P50_has_current_keeper`).

## 3. IRIs

The acervo publishes no IRIs, only numeric identifiers.  The IRIs are
derived by hash, so that re-running the exporter produces exactly the same
files:

```python
H(key) = int(sha1(key).hexdigest()[:10], 16) % (9 * 10**8) + 10**9
```

The result has ten digits and falls in `[1.000.000.000, 1.899.999.999]` — the
same format as the model files of MeLODy.  The IRIs have the form
`urn:uuid:works/1177196623`, `urn:uuid:persons/1372428005` etc.

The labels of the blank nodes are deterministic as well (uuid5 from the IRI
of the entity and the role of the node), which guarantees that the files are
byte-identical between runs and that two files never share a blank node —
the validator loads all the files into a single graph.

## 4. Modelling decisions

### 4.1 Gender

The acervo records no gender for the people.  The model admits only `female`,
`male` and `diverse`.  The property is asserted only when it is known from the
curated records — Maria Souto is recorded as a woman, the other people of the
sample as men.  The bulk ingestion leaves it out rather than guessing it from
names.  The values of the sample are an inference, not a datum of the acervo.

### 4.2 Names

The acervo gives the inverted name (`"Silva, Viriato Figueira da"`) and the
display name (`"Candinho Trombone"`).  The inverted one becomes
`schema:familyName` + `schema:givenName`; the display one becomes
`schema:alternateName` when it differs from the given name concatenated to
the family name.  Names such as “Candinho Trombone” or “Marcelo Tupinambá”
are stage names, not civil names — that is why they do not go to
`schema:givenName`.

The record of Berredo gives the inverted name between brackets
(`"Berredo (Guimarães, Durval Berredo)"`); the content of the brackets
prevails.

### 4.3 Places

The acervo records the place of birth as `"Cidade - UF"`.  MeLODy provides a
single level of containment (`schema:containedInPlace` with at most one
`melod:Country`), so the city is contained in the country and the federal
unit stays in the `schema:description` of the place:

```
Rio de Janeiro (geonames 3451190)
  schema:description "Rio de Janeiro - RJ, Brazil."
  schema:containedInPlace → https://www.geonames.org/3469034
```

The countries are not entities of this repository.  The place shape of
MeLODy declares them as individuals of `melod:Country` (Brazil is the
geonames id 3469034), so `schema:containedInPlace` points at that IRI and the
editor offers the countries in the menu of the field.  The alternative — a
country document of our own — would need a second type for the same entity
(`melod:Place` and `melod:Country`) and would break the editor, which accepts
exactly one entity type per document (§ 4.12).

Places of birth that designate no place (“Local não identificado”,
“Compositor estrangeiro”) produce no entity: the information stays in the
description of the person.

### 4.4 Metre

`melod:usesMeterSymbol` admits only “common” and “cut”, insufficiently
granular for the acervo.  The metre of the acervo (`2/4`) is recorded as
`melod:hasMeterCount` 2 + `melod:inMeterUnit` 4, with the original string in
the `schema:description` of the `melod:Meter`.

### 4.5 The field “Cópia”

The acervo uses a single free-text field for different things: the type of
the copy, the copyist, the editor and the provenance.  `fetch.parse_copy`
unpacks it:

| value in the acervo                                         | reading                              |
|-------------------------------------------------------------|--------------------------------------|
| `manuscrita`                                                | manuscript, unknown copyist           |
| `manuscrita por X`                                          | manuscript, copyist X                 |
| `manuscrita - Obtida do Sr. X (arquivo de Y)`               | manuscript, former owner X, donor Y   |
| `editorada X`                                               | print, publisher X                    |
| `editada por X`                                             | print, editor X                       |
| `editada`                                                   | print, unknown publisher              |
| `digitada`, `edição digital`                                | digital transcription                 |
| `digitada por X`, `edição digital por X`                    | digital transcription by X            |

A digital transcription is a Manifestation of its own: the acervo's
typescript of a manuscript or print is neither that manuscript nor that
print.  Its classification is the literal “Digital transcription”, because
the MeLODy vocabulary has no term for it, and the person who made it is a
`terms:Transcriber` contribution of the item's provenance event.

### 4.6 Publishing houses

The field “Cópia” also names the *publishing house* of a third-party
edition: “editada por Irmãos Vitale” — the edition of the piano score of
“Aurora”, by Zequinha de Abreu.  The pattern `editada por X` reads the name
as an editor, so the name is matched against the institutions of the
dataset: when it is one of them, the edition is published by that house
(`melod:hasContribution` → `terms:Publisher`, and `schema:publication` with
`schema:publishedBy`), and no editor is recorded.  The place of the
publication event is the place of the publisher, not a fixed one.

The institution itself receives the name, the address, the place, the
founding date (`schema:foundingDate` → `melod:ExactDate`) and the external
references (`owl:sameAs`) taken from the publisher's own site and from
authority files — Wikidata, VIAF and the Library of Congress for Irmãos
Vitale.  The description states where the identification comes from, since
the acervo names the house only in the free-text field.

In the bulk ingestion, a name in `editada por` / `editorada` that matches no
person becomes an Institution created from the name alone: the field usually
names a publishing house, and the edition must not lose its publisher.  These
institutions have no place of publication and no external reference, and they
are listed in the issue report (§ 6) for later enrichment.

### 4.7 Score without digitisation

“Amarga saudade” and “Aurora” have scores whose PDF is not published: the
acervo records that “Visualização e consulta não autorizadas pela editora.
Disponível somente na Casa do Choro”.  The item exists, without
`owl:sameAs` nor identifier, and the restriction stays in
`melod:hasAnnotation` (paragraph `rdf:HTML`).

### 4.8 Shelfmark

The acervo publishes no shelfmarks.  The identifier of the digitised
surrogate (`score_825`) is used provisionally in `melod:hasShelfmark` and in
`melod:hasIdentifier`, so that the editor can locate the copy; the same
value is linked to the PDF through `owl:sameAs`.

### 4.9 People with no record in the encyclopedia

The acervo mentions some people only in free-text fields:

| person                  | where it appears                      | treatment |
|-------------------------|---------------------------------------|------------|
| Baptista Júnior         | “Letra de Baptista Junior”            | person with a provisional identification noted in the description |
| Gerson Ferreira Pinto   | “arquivo de Gerson Ferreira Pinto”    | person with `owl:sameAs` to Wikidata (Q20048060) |
| A. Di Franco            | “editada por A. Di Franco”            | person with a provisional identification — the acervo does not say whether it is a person or a publishing house |
| Salvador Moraes         | “Letra de Salvador Moraes.”            | person with a provisional identification noted in the description |

The bulk ingestion extends this treatment to every free name it cannot
resolve against a person record: the name becomes a provisional Person, with
the IRI derived from the normalised name (`urn:uuid:persons/<hash>`) rather
than from a card, and the role and the work where the name appears are noted
in the description and in the issue report (§ 6).  A later harvest may bring
the record of the person: the next run then resolves the name to that record
and drops the provisional entity.

### 4.10 Homonymous records

The acervo has two records for “Miguel Rabello” — “Rabello, Miguel” (2326)
and “Bastos, Miguel Rabello” (2006) — with the same activities, the same
place of birth and no biography.  They are almost certainly the same person
registered twice, and so the two records were joined into a single entity,
with the two URLs in `owl:sameAs` and the merge noted in the description.
The merge is provisional.

The same applies to the two works titled “A baianinha” (771, by Candinho
Trombone, and 4138, by P. de Alcântara Bacellar): they are different works
and were kept separate.

### 4.11 Contributions and certainty

`melod:hasCertainty` tells apart what the acervo asserts from what it
suggests:

| contribution         | certainty                | why |
|----------------------|--------------------------|-----|
| composer             | `terms:HighCertainty`    | the acervo explicitly links the work to the person |
| arranger             | `terms:MediumCertainty`  | the acervo names the arranger in the field “Arranjo” |
| librettist           | `terms:MediumCertainty`  | idem, in the field “Letra” |
| editor               | `terms:MediumCertainty`  | idem, in the field “Cópia” |
| publisher (institution) | no value              | the acervo names the house in the field “Cópia”, but the house is certain anyway |

### 4.12 Entity types and the generated indexes

Every document declares **exactly one** type for its entity, and that type is
the base class of the ontology (`melod:Expression`, `melod:Person`…) — never
the derived `*Entity` class.  The editor requires it: when a document is
selected it runs

```sparql
select ?entity_iri ?entity_type where {
    ?entity_iri a ?entity_type .
    filter(strstarts(str(?entity_iri), "urn:uuid:"))
    filter(strstarts(str(?entity_type), "https://lod.academy/melod/vocab/ontology#"))
}
```

and refuses to open the document unless the query returns exactly one row.
Two types make the editor stop with “The selected document needs one
statement with entity IRI and entity type!”; conversely, the JSON-LD → MEI
converter is chosen by comparing the single `@type` with the base class, so
an array of types would also leave the document without a form.

The derived classes (`melod:WorkEntity`, `melod:PersonEntity`…) appear in the
**generated indexes**.  Every projection re-types the entities it selects:

```sparql
construct { ?expression_iri a melod:ExpressionEntity; skos:prefLabel ?label }
where     { ?expression_iri a melod:Expression . … }
```

The shapes reference the entities of a document by these derived types
(`sh:class melod:PersonEntity` on `melod:hasAgent`, and so on).  They are
satisfied because the editor validates a document against a store that
contains the shapes, their `owl:imports` (the melod terms) and the `indexes/`
folder of the repository; `tests/validation.js` mirrors that composition.
A consequence for the workflow: after changing entity documents, regenerate
the indexes (§ 8), otherwise the shapes cannot see the type of a referenced
entity.

### 4.13 Date spans

The `melod:Date` shape accepts a span of dates, but the `sh:xone` that
governs it is sensitive: both branches (`schema:startDate`/`schema:endDate`
and `melod:notBefore`/`melod:notAfter`) have only `sh:maxCount`, so a node
with none of the fields satisfies **both** branches and violates the
`sh:xone`.  A span is only valid if one of the branches is broken by a
datatype different from the expected one:

```turtle
_:d a melod:Date;
    melod:notBefore "1741"^^xsd:gYear;
    melod:notAfter "1744"^^xsd:gYear;
    schema:startDate "1741"^^xsd:gYear;   # breaks the exact-date branch
    melod:hasCertainty terms:MediumCertainty;
    schema:description "[1741]-1744".
```

The acervo has no date spans, so this shape only appears in the files of the
MeLODy model.

### 4.14 Expressions and score types

The “Partituras” list states a type for every score (`Partitura piano`,
`Partitura melodia`, `Partitura cifra`…).  The type is part of the
**expression**, not only of the manifestation: a piano score and a melody
score of the same work are different versions, and the model creates one
Expression for each type.  Scores with the same arranger *and* the same type
still share an expression; the copies of one edition remain one
Manifestation with several Items.

A type that declares an arrangement (`Partitura arranjo`,
`Partitura arranjo para banda`…) but whose “Arranjo” field is empty becomes
an anonymous arrangement expression.  Its IRI is derived from the type and
the marker `anonymous-arrangement`; no `terms:Arranger` contribution is
written, because the acervo names no arranger.  The ingestion records these
cases as `arrangement_without_arranger` in the issue report, so that a later
enrichment can identify the arranger.

The expression IRI therefore includes the arranger (or the anonymous/original
marker) **and** the score type:

```python
variant = f"arranger:{arranger}:{score_type}"
variant = f"anonymous-arrangement:{score_type}"
variant = f"original:{score_type}"
```

Changing the type of a score changes its Expression and, because the
expression is part of the manifestation key, its Manifestation as well; the
Item IRI stays keyed by the acervo record and the position of the score.

## 5. Corrections in the data of the MeLODy model

The example files that came with the MeLODy template did not pass the
validation: 27 files, 123 violations.  Part of them were content errors,
corrected here; the rest came from a validator that did not load the
generated indexes (§ 4.12).  The corrections are of content, not of style:

| file | correction |
|------|------------|
| `works/1031334055.ttl` | the literal of `schema:description` was not closed — the file was not valid Turtle and was left out of the validation |
| `instrumentations/*.ttl` | `schema:position` and `schema:description` in each `melod:InstrumentationDetail`; MARC code of the double bass corrected (`#ke` → `#sd`, which is the one of the *basso continuo*); `www.loac.gov` → `www.loc.gov` |
| `expressions/926630544.ttl` | the instrumentation pointed to `urn:uuid:1134679629`, an IRI that does not exist — it now points to `urn:uuid:instrumentations/1134679629` |
| `expressions/1298183696.ttl` | the key of the recitative had only `schema:description`; it receives key, alteration and mode — E-flat major, the tonality of the other movements of the *Kantaten-Jahrgang*, since the key signature of the *incipit* is empty and the movement is “modulierend” (the description records the inference) |
| `expressions/2293419636.ttl`, `expressions/2372423187.ttl` | date spans filled in (§ 4.13); `melod:MediumCertainty` (which does not exist in the ontology) corrected to `terms:MediumCertainty`; annotation paragraph typed as `rdf:HTML` |
| `items/244351973.ttl` | the two provenance events had no `rdfs:label`, required by the `melod:Event` shape |
| `manifestations/893513144.ttl` | the title page had no `cidoc:P2_has_type` and the paragraph was not `rdf:HTML` |
| `performanceEvents/3395291370.ttl`, `4019778394.ttl`, `603545879.ttl` | the three pointed to `urn:uuid:venues/2096486337`, which does not exist in the venues namespace (it is the IRI of the place Hamburg); they now point to the St. Catharinen venue, as the event of 1742 does |
| `bibliography/268258228.ttl` | the `melod:hasAbbreviation` was missing, and it is mandatory: “HenzelC 2004” — Christoph Henzel, *Das Konzertleben in der preußischen Hauptstadt 1740-1786 im Spiegel der Berliner Presse*, SIM-Jahrbuch 2004, p. 216-291, following the pagination of the record itself |

After the corrections, `npm test` passes on the 122 files of the repository,
with no violation at all.  The test also checks the editor's type contract of
§ 4.12, so a document with a second entity type fails the build.

## 6. Bulk ingestion

`tools/acervo/harvest.py` harvests the whole acervo into
`.cache/acervo/works.jsonl` and `cards.jsonl`; `tools/acervo/ingest.py` maps
those records to entities and writes the files into the same folders as the
curated sample.  The harvest is resumable and the ingestion can be re-run at
any time: it rewrites the same files deterministically and extends the set as
the harvest grows.

```bash
python3 -m tools.acervo.harvest listing   # the ids of works and persons
python3 -m tools.acervo.harvest works     # the work records
python3 -m tools.acervo.harvest cards     # the person records
python3 -m tools.acervo.ingest --out .    # entities + report
```

Only the works with at least one digitised *Partitura* are modelled; the
records of the curated sample are kept even when they have no digitisation
(§ 4.7).  During the harvest the ingestion can be re-run after each batch: it
always reflects the records collected so far.  Every free name — copyist,
arranger, lyricist, former owner, donor —
is resolved against the person records of the acervo.  A name with no record
becomes a provisional Person whose IRI is derived from the normalised name;
the identification is noted in the description of the person and in the
report.  The places are derived from the `"Cidade - UF"` field (§ 4.3), the
publishing houses from the `"Cópia"` field (§ 4.6), and each instrumentation
from the list of instruments of the score.

The report is written to `docs/acervo-ingest-issues.md` (summary) and
`docs/acervo-ingest-issues.csv` (one row per problem).  It records, among
other things, harvest failures, records skipped for lack of digitisation,
provisional persons, unstructured values of `"Cópia"`, arrangements whose type
names no arranger, dates the model cannot parse, places without a country or
without a GeoNames identifier, and instruments without a controlled term.  A
problem never stops the ingestion.

Because the ingestion deletes the documents it no longer generates — for
example a provisional person that a later harvest replaced with the real
record — pruning only happens on the canonical harvest directory
(`.cache/acervo`) once every id of the listings has a record.  While the
harvest is still growing, a work that has not been collected yet keeps the
documents of the earlier batches.  `--no-prune` keeps everything; `--prune`
forces the deletion when a different `--harvest` directory is used
deliberately, and `--limit` never prunes.  The template documents that come
from MerMEId are never deleted (`tools/acervo/template_files.txt`).

## 7. What is missing

* **Date of composition.**  The acervo does not show the date on the record
  of the work, although the search by period works.  The works of the acervo
  have no `schema:dateCreated`.
* **Catalogue numbers, publication conditions and publishing houses.**
  The editions of the acervo carry no catalogue number nor publication date;
  the `schema:startDate` of the publication was fixed on the first of January
  of the year, only to satisfy the model.
* **Page layout.**  The scores are digitised but not transcribed; there is no
  MEI nor incipit.
* **Performance events.**  The sample has no documented performances — the
  acervo does not publish them for the catalogued works.

## 8. How to regenerate

```bash
# the sample, written into the entity folders of the repository
python3 -m tools.acervo.sample --out .

# the projections (indexes): the editor loads them in its dropdowns, and the
# validation resolves the type of a referenced entity through them (§ 4.12)
pip install rdflib
python3 -m tools.datasets --out indexes

# validation against the SHACL shapes of MeLODy and the editor's type contract
npm test

# the local interactive graph viewer (optional): data for viewer/
python3 tools/viewer_data.py
```

The CI generates the same projections with the `static-publishing-backend`,
which runs inside a container; `tools/datasets.py` does the same work
locally, with `rdflib`.  The CI publishes the result in `public/datasets/`
(which the editor loads, according to the `datasetBaseUrl` of
`configuration/config.json`); `indexes/` keeps a versioned copy of the same
content.

`tools/acervo/` contains seven modules:

| file             | function |
|------------------|----------|
| `fetch.py`       | harvests the records of the acervo and returns verbatim dictionaries |
| `harvest.py`     | drives the full, resumable harvest into JSONL files |
| `ingest.py`      | maps the harvested records to entities and writes the issue report |
| `ids.py`         | derives the deterministic IRIs |
| `ttl.py`         | minimal deterministic Turtle writer |
| `sample_data.py` | the transcribed sample and the decisions that are not automatic |
| `sample.py`      | applies the FRBR mapping and writes the files |

The harvesting respects the `Crawl-delay: 10` requested by the `robots.txt`
of the acervo.

## 9. Local graph viewer

`viewer/` is a local inspection tool for the FRBR graph; it does not alter the
public viewer generated by the MeLODy template.  It reads the entity folders
and writes `viewer/data/nodes.jsonl` and `viewer/data/edges.jsonl` with:

```bash
python3 tools/viewer_data.py
```

The viewer shows a readable hierarchy from a Person or Work
(`Person → Work → Expression → Manifestation → Item`) and all remaining
relationships as dashed cross-links.  The copyist of an item, for example, is
a cross-link from the Item to the Person, not a second child of the Person.
Arrowheads follow the RDF direction even where the tree is drawn in the
opposite direction for readability.  The information panel fetches and parses
the complete Turtle document of the selected node.  See
[`viewer/README.md`](../viewer/README.md) for the server command and the
interactions.
