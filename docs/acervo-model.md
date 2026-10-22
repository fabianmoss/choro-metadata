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
arrangers** are different expressions of the same work.  The scores with no
declared arrangement form the “original” expression.  It receives the metre
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
`male` and `diverse`.  The agents catalogued so far are all men, which
follows from the given names; the value `male` was assigned on that basis.
It is an inference, not a datum of the acervo.

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
  schema:containedInPlace → Brazil (geonames 3469034, a melod:Country)
```

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

### 4.12 Derived types

The shapes of MeLODy do not reference the entities by their base type
(`melod:Work`, `melod:Person`…), but by their derived type
(`melod:WorkEntity`, `melod:PersonEntity`…).  The validator does not do RDFS
entailment, so the derived type has to be declared in the file itself.  All
the files of the repository — those of the acervo and those of the MeLODy
model — declare both types.

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

## 5. Corrections in the data of the MeLODy model

The example files that came with the MeLODy template did not pass the
validation: 27 files, 123 violations.  The corrections are of content, not
of style:

| file | correction |
|------|------------|
| 40 files | declaration of the `melod:*Entity` type (§ 4.12) |
| `works/1031334055.ttl` | the literal of `schema:description` was not closed — the file was not valid Turtle and was left out of the validation |
| `instrumentations/*.ttl` | `schema:position` and `schema:description` in each `melod:InstrumentationDetail`; MARC code of the double bass corrected (`#ke` → `#sd`, which is the one of the *basso continuo*); `www.loac.gov` → `www.loc.gov` |
| `expressions/926630544.ttl` | the instrumentation pointed to `urn:uuid:1134679629`, an IRI that does not exist — it now points to `urn:uuid:instrumentations/1134679629` |
| `expressions/1298183696.ttl` | the key of the recitative had only `schema:description`; it receives key, alteration and mode — E-flat major, the tonality of the other movements of the *Kantaten-Jahrgang*, since the key signature of the *incipit* is empty and the movement is “modulierend” (the description records the inference) |
| `expressions/2293419636.ttl`, `expressions/2372423187.ttl` | date spans filled in (§ 4.13); `melod:MediumCertainty` (which does not exist in the ontology) corrected to `terms:MediumCertainty`; annotation paragraph typed as `rdf:HTML` |
| `items/244351973.ttl` | the two provenance events had no `rdfs:label`, required by the `melod:Event` shape |
| `manifestations/893513144.ttl` | the title page had no `cidoc:P2_has_type` and the paragraph was not `rdf:HTML` |
| `performanceEvents/3395291370.ttl`, `4019778394.ttl`, `603545879.ttl` | the three pointed to `urn:uuid:venues/2096486337`, which does not exist in the venues namespace (it is the IRI of the place Hamburg); they now point to the St. Catharinen venue, as the event of 1742 does |
| `bibliography/268258228.ttl` | the `melod:hasAbbreviation` was missing, and it is mandatory: “HenzelC 2004” — Christoph Henzel, *Das Konzertleben in der preußischen Hauptstadt 1740-1786 im Spiegel der Berliner Presse*, SIM-Jahrbuch 2004, p. 216-291, following the pagination of the record itself |

After the corrections, `npm test` passes on the 123 files of the repository,
with no violation at all.

## 6. What is missing

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

## 7. How to regenerate

```bash
# the sample, written into the entity folders of the repository
python3 -m tools.acervo.sample --out .

# validation against the SHACL shapes of MeLODy
npm test

# the projections (indexes) that the editor loads in its dropdowns
pip install rdflib
python3 -m tools.datasets --out indexes
```

The CI generates the same projections with the `static-publishing-backend`,
which runs inside a container; `tools/datasets.py` does the same work
locally, with `rdflib`.  The CI publishes the result in `public/datasets/`
(which the editor loads, according to the `datasetBaseUrl` of
`configuration/config.json`); `indexes/` keeps a versioned copy of the same
content.

`tools/acervo/` contains six modules:

| file             | function |
|------------------|----------|
| `fetch.py`       | harvests the records of the acervo and returns verbatim dictionaries |
| `harvest.py`     | drives the full, resumable harvest into JSONL files |
| `ids.py`         | derives the deterministic IRIs |
| `ttl.py`         | minimal deterministic Turtle writer |
| `sample_data.py` | the transcribed sample and the decisions that are not automatic |
| `sample.py`      | applies the FRBR mapping and writes the files |

The harvesting respects the `Crawl-delay: 10` requested by the `robots.txt`
of the acervo.
