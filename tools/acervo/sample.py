"""Maps the Casa do Choro acervo records to the FRBR model.

The acervo does not separate work, expression, manifestation and item: each
"Partitura" published on the record of a work is, in practice, one copy of a
score.  The mapping below reorganises those records into the MeLODy chain:

``work`` (*melod:Work*)
    The composition.  One work per record of the acervo.

``expression`` (*melod:Expression*)
    A version of the work.  Scores with different arrangers or different
    score types (piano, melody, cifra…) are different expressions; a type
    that declares an arrangement without naming its arranger forms an
    anonymous arrangement.  The other scores form the "original" expression.

``manifestation`` (*melod:Manifestation*)
    An edition.  Scores of the same format and the same edition — for
    instance the four manuscript copies of "A baianinha" — form one
    manifestation, and each copy is an item.

``item`` (*melod:Item*)
    A physical copy.  Each "Partitura" of the acervo record corresponds to
    an item, with the copyist, the date and the provenance the record
    registers.

Modelling rules
---------------

* The acervo stores the place of birth as "Cidade - UF".  The model has a
  single level of containment, so the city is contained in the country and
  the federal unit stays in the description of the place.
* The free-text field "Cópia" is broken down into the type of the copy, the
  copyist, the editor and the provenance by
  :func:`tools.acervo.fetch.parse_copy`.
* A name of the field "Cópia" that is registered as an institution of the
  dataset is a publishing house and not an editor: the edition is then
  published by that house.
* The people the acervo mentions without giving them a card in the
  encyclopedia are registered anyway, with the identification noted as
  provisional.
* Dates in the acervo's format (``dd.mm.yyyy``) become ``xsd:date``.

Usage::

    python3 -m tools.acervo.sample --out .
"""

from __future__ import annotations

import argparse
import os
import re
import unicodedata
from pathlib import Path

from . import ids
from .fetch import parse_copy
from .ttl import Graph, IRI, Literal, Prefixed, blank_node

__all__ = ["build", "main"]

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XSD = "http://www.w3.org/2001/XMLSchema#"

LANG = "pt"

#: The institution that keeps the acervo and whose editions bear its name.
KEEPER = "Instituto Casa do Choro"

#: How the acervo writes the editor of its own editions.
PUBLISHER_ALIASES = {
    "casa do choro": KEEPER,
    "instituto casa do choro": KEEPER,
}

#: Spellings of the same publishing house in the acervo.  The key is the
#: normalised name; the value is the name under which the house is modelled.
#: The houses that are not curated are derived from the name, so the value
#: must be the canonical spelling that becomes the institution.
INSTITUTION_ALIASES = {
    "e. s. mangione": "E.S. Mangione",
    "narciso e arthur napoleao": "Narciso & Arthur Napoleão",
    "arthur napoleao & c": "Arthur Napoleão & Cia",
    "por victor prealle": "Victor Préalle",
}


def institution_name(name: str) -> str:
    """The canonical spelling of a publishing house."""
    return INSTITUTION_ALIASES.get(normalize(name), name.strip())


def publisher_name(copy: dict, institutions_by_name: dict) -> str | None:
    """The publishing house of an edition, if its name is known.

    The acervo writes in the field “Cópia” the name of the editor, which may
    be a person (“editada por A. Di Franco”) or a publishing house (“editada
    por Irmãos Vitale”).  A name that is registered as an institution of the
    dataset is a publisher, not an editor.
    """
    for name in (copy.get("publisher"), copy.get("editor")):
        if not name:
            continue
        canonical = institution_name(name)
        alias = PUBLISHER_ALIASES.get(normalize(canonical))
        if alias:
            return alias
        institution = institutions_by_name.get(normalize(canonical))
        if institution:
            return institution["name"]
    return None


# ---------------------------------------------------------------------------
# utilities
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Lower case, without accents, with the whitespace collapsed."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped.lower()).strip()


def parse_date(text: str) -> str | None:
    """Turns ``dd.mm.yyyy`` (the acervo's format) into ``xsd:date``."""
    match = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", (text or "").strip())
    if not match:
        return None
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def place_key(value: str) -> str | None:
    """Turns the place of birth of the acervo into the name of the place.

    The acervo writes the place of birth as ``"Cidade - UF"``; the model
    separates the city (which is the place) from the federal unit (which
    goes to the description).  Values that designate no place ("Local não
    identificado", "Compositor estrangeiro") are returned intact, so that
    the caller decides what to do with them.
    """
    text = (value or "").strip()
    if not text:
        return None
    match = re.match(r"^(.*?)\s*[-–]\s*([A-Z]{2})\s*$", text)
    if match:
        return match.group(1).strip()
    if " - " in text:
        return text.split(" - ", 1)[0].strip()
    return text


def split_name(inverted: str, fallback: str) -> tuple[str, str]:
    """Splits the inverted name of the acervo into family and given name.

    ``"Silva, Viriato Figueira da"`` → ``("Silva", "Viriato Figueira da")``.
    Some records carry the display name between brackets
    (``"Berredo (Guimarães, Durval Berredo)"``); the bracket takes
    precedence.  Names the acervo does not invert fall back to the display
    name.
    """
    text = (inverted or "").strip()
    parenthetical = re.search(r"\(([^)]*)\)", text)
    if parenthetical:
        text = parenthetical.group(1).strip()
    if "," in text:
        family, given = text.split(",", 1)
        return family.strip(), given.strip()
    return fallback.strip(), ""


# ---------------------------------------------------------------------------
# person register
# ---------------------------------------------------------------------------

class People:
    """Index of the people of the acervo, with the resolution of free names."""

    def __init__(self, cards, extra_persons, aliases=None, merged=None):
        self.people: dict[str, dict] = {}
        self.index: dict[str, str] = {}
        self.by_card: dict[str, str] = {}
        self.aliases = dict(aliases or {})
        self.merged = dict(merged or {})

        secondary = {
            card
            for group in self.merged.values()
            for card in group
            if card not in self.merged
        }

        for card in cards:
            key = card["id"]
            if key in secondary:
                continue
            person = dict(card)
            person["key"] = key
            person["cards"] = list(self.merged.get(key, [key]))
            person["extra_cards"] = [c for c in person["cards"] if c != key]
            person.setdefault("alternate", [])
            person.setdefault("note", "")
            self.people[key] = person
            self._register(key, card.get("name"), card.get("inverted"))
            for card_id in person["cards"]:
                self.by_card[card_id] = key

        for person in extra_persons:
            record = dict(person)
            record["key"] = person["id"]
            record["cards"] = []
            record["extra_cards"] = []
            record.setdefault("alternate", [])
            record.setdefault("note", "")
            self.people[person["id"]] = record
            self._register(person["id"], person.get("name"), person.get("inverted"))

        for alias, key in self.aliases.items():
            self.index.setdefault(normalize(alias), key)

    def _register(self, key: str, name: str | None, inverted: str | None) -> None:
        for value in (name, inverted):
            if value:
                self.index.setdefault(normalize(value), key)
        if inverted:
            family, given = split_name(inverted, "")
            if given:
                self.index.setdefault(normalize(f"{given} {family}"), key)

    def resolve(self, name: str) -> str | None:
        """Returns the key of the person a free name refers to."""
        if not name:
            return None
        return self.index.get(normalize(name))

    def resolve_card(self, card_id: str) -> str | None:
        """Returns the key of the person a card of the acervo corresponds to."""
        return self.by_card.get(str(card_id))

    def iri(self, key: str) -> str:
        return ids.person(key)


# ---------------------------------------------------------------------------
# building the entities
# ---------------------------------------------------------------------------

class Builder:
    """Accumulates the files to be written, one per entity."""

    def __init__(self, people: People, place_keys=(), instrumentation_labels=None,
                 instrument_terms=None, bibliography=(), institutions=(),
                 countries=None):
        self.people = people
        self.place_keys = set(place_keys)
        self.countries = dict(countries or {})
        self.instrumentation_labels = instrumentation_labels or {}
        self.instrument_terms = instrument_terms or {}
        self.bibliography = list(bibliography)
        self.institutions: dict[str, dict] = {}
        for institution in institutions:
            record = dict(institution)
            for name in (record.get("name"), record.get("key")):
                if name:
                    self.institutions[normalize(name)] = record
        self.files: dict[tuple[str, str], str] = {}

    def institution_by_name(self, name: str) -> dict | None:
        """The institution registered under ``name``, when there is one."""
        return self.institutions.get(normalize(name))

    def institution_location(self, name: str) -> str | None:
        """The place where the institution is, for the publication event."""
        record = self.institution_by_name(name)
        return record.get("location") if record else None

    def write(self, folder: str, iri: str, graph: Graph) -> None:
        name = iri.rsplit("/", 1)[-1]
        self.files[(folder, name)] = graph.render()

    # -- persons ----------------------------------------------------------
    def person(self, key: str) -> None:
        person = self.people.people[key]
        graph = Graph()
        iri = ids.person(key)

        family, given = split_name(person.get("inverted", ""), person.get("name", ""))
        graph.type(iri, "melod:Person")
        graph.add(iri, "schema:familyName", Literal(family))
        if given:
            graph.add(iri, "schema:givenName", Literal(given))
        for name in self.alternate_names(person, family, given):
            graph.add(iri, "schema:alternateName", Literal(name))
        # The acervo records no gender.  The model admits only three values,
        # so it is only asserted for the records that carry it explicitly;
        # the bulk ingestion does not guess it.
        if person.get("gender"):
            graph.add(iri, "schema:gender", Literal(person["gender"]))
        for field, predicate in (("birth", "schema:birthDate"),
                                 ("death", "schema:deathDate")):
            value = parse_date(person.get(field, ""))
            if value:
                graph.add(iri, predicate, Literal(value, datatype=XSD + "date"))
        place = place_key(person.get("birth_place"))
        if place and place in self.place_keys:
            graph.add(iri, "schema:birthPlace", IRI(ids.place(place)))
        for occupation in person.get("roles") or []:
            graph.add(iri, "schema:hasOccupation", Literal(occupation))
        description = self.person_description(person)
        if description:
            graph.add(iri, "schema:description", Literal(description))
        for link in self.person_links(person):
            graph.add(iri, "owl:sameAs", IRI(link))
        graph.add(iri, "dct:conformsTo", Prefixed("melod:Person"))
        self.write("persons", iri, graph)

    @staticmethod
    def alternate_names(person: dict, family: str, given: str) -> list[str]:
        """Alternative names: the declared ones and the display name."""
        names = []
        full = normalize(f"{given} {family}")
        display = person.get("name")
        if display and normalize(display) != full:
            names.append(display)
        for name in person.get("alternate") or []:
            if normalize(name) not in {normalize(n) for n in names}:
                names.append(name)
        return names

    def person_description(self, person: dict) -> str:
        parts = [(person.get("bio") or "").strip()]
        sources = [s for s in (person.get("sources") or "").split("\n") if s.strip()]
        if sources:
            parts.append(
                "<p><strong>Fontes de pesquisa</strong></p>\n<ol>\n"
                + "\n".join(f"<li>{s.strip()}</li>" for s in sources)
                + "\n</ol>"
            )
        if person.get("extra_cards"):
            extra = ", ".join(person["extra_cards"])
            main = person["cards"][0]
            parts.append(
                f'<p>Record in the archive: <a href="https://acervo.casadochoro.com.br/'
                f'cards/view/{main}">card {main}</a> and homonymous card {extra}. '
                f"Both cards have the same activities and the same place of birth "
                f"and were merged into a single person; the merge is provisional.</p>"
            )
        naturality = (person.get("birth_place") or "").strip()
        if naturality and place_key(naturality) not in self.place_keys:
            parts.append(f"<p>Naturality recorded in the archive: {naturality}.</p>")
        if person.get("note"):
            parts.append(f"<p>{person['note']}</p>")
        return "\n\n".join(p for p in parts if p)

    @staticmethod
    def person_links(person: dict) -> list[str]:
        links = [f"https://acervo.casadochoro.com.br/cards/view/{card}"
                 for card in person.get("cards", [])]
        if person.get("wikidata"):
            links.append(f"https://www.wikidata.org/wiki/{person['wikidata']}")
        return links

    # -- places -----------------------------------------------------------
    def place(self, place: dict) -> None:
        graph = Graph()
        iri = ids.place(place["key"])
        graph.type(iri, "melod:Place")
        graph.add(iri, "schema:name", Literal(place["name"]))
        if place.get("description"):
            graph.add(iri, "schema:description", Literal(place["description"]))
        if place.get("geonames"):
            graph.add(iri, "owl:sameAs",
                      IRI(f"https://www.geonames.org/{place['geonames']}"))
        country = self.countries.get(place.get("country"))
        if country:
            # The countries are not entities of this repository: the place
            # shape declares them as individuals of melod:Country (one per
            # geonames id), so the place points at that IRI and the editor
            # offers them in its country menu.
            graph.add(iri, "schema:containedInPlace",
                      IRI(f"https://www.geonames.org/{country['geonames']}"))
        self.write("places", iri, graph)

    # -- institutions -----------------------------------------------------
    @staticmethod
    def same_as(value) -> list[str]:
        """The external references of an entity: one string or a list."""
        if not value:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def institution(self, institution: dict) -> None:
        graph = Graph()
        iri = ids.institution(institution["key"])
        graph.type(iri, "melod:Institution")
        graph.add(iri, "schema:name", Literal(institution["name"]))
        if institution.get("abbreviation"):
            graph.add(iri, "melod:hasAbbreviation",
                      Literal(institution["abbreviation"]))
        if institution.get("address"):
            graph.add(iri, "schema:address", Literal(institution["address"]))
        if institution.get("location"):
            graph.add(iri, "schema:location", IRI(ids.place(institution["location"])))
        for link in self.same_as(institution.get("sameAs")):
            graph.add(iri, "owl:sameAs", IRI(link))
        if institution.get("founding_date"):
            date = blank_node(f"{iri}#foundingDate")
            graph.type(date, "melod:ExactDate")
            graph.add(date, "melod:isodate",
                      Literal(institution["founding_date"], datatype=XSD + "date"))
            if institution.get("founding_description"):
                graph.add(date, "schema:description",
                          Literal(institution["founding_description"]))
            graph.add(iri, "schema:foundingDate", date)
        if institution.get("description"):
            graph.add(iri, "schema:description", Literal(institution["description"]))
        self.write("institutions", iri, graph)

    # -- instrumentations --------------------------------------------------
    def instrumentation(self, instruments: list[str]) -> str:
        signature = tuple(normalize(i) for i in instruments)
        label = self.instrumentation_labels.get(signature)
        key = label or ", ".join(instruments)
        iri = ids.instrumentation(key)

        graph = Graph()
        graph.type(iri, "melod:Instrumentation")
        if label:
            # a label written for this dataset: English, no language tag
            graph.add(iri, "rdfs:label", Literal(label))
        else:
            # the list of instruments exactly as the acervo publishes it
            graph.add(iri, "rdfs:label", Literal(key, lang=LANG))
        for position, name in enumerate(instruments, start=1):
            detail = blank_node(f"{iri}#detail{position}")
            graph.type(detail, "melod:InstrumentationDetail")
            graph.add(detail, "schema:position",
                      Literal(str(position), datatype=XSD + "integer"))
            graph.add(detail, "schema:description", Literal(name))
            term = self.instrument_terms.get(normalize(name))
            if not term:
                # numbered parts ("Flauta 1", "Violino 2") use the term of
                # the instrument itself
                term = self.instrument_terms.get(re.sub(r"\s+\d+$", "", normalize(name)))
            if term:
                # The instrument may have no term in the MeLODy vocabulary
                # (the accordion, for example): the Library of Congress code
                # is still recorded; the shape allows a custom instrument as
                # a string or another SKOS concept, but terms:Choir is a
                # Classification, not an Instrument.
                if term[0] and term[0] != "terms:Choir":
                    graph.add(detail, "mus:U2_foresees_use_of_medium_of_performance",
                              Prefixed(term[0]))
                graph.add(detail, "owl:sameAs", IRI(
                    "https://www.loc.gov/standards/valuelist/marcmusperf.html#"
                    + term[1]))
            graph.add(detail, "mus:U30_foresees_quantity_of_medium_of_performance",
                      Literal("1", datatype=XSD + "integer"))
            graph.add(iri, "melod:hasInstrumentationDetail", detail)
        self.write("instrumentations", iri, graph)
        return iri

    # -- bibliography ------------------------------------------------------
    def bibliography_entity(self, entry: dict) -> None:
        graph = Graph()
        iri = ids.bibliography(entry["key"])
        graph.type(iri, "melod:Bibliography")
        if entry.get("genre"):
            graph.add(iri, "schema:genre", Prefixed(entry["genre"]))
        title = blank_node(f"{iri}#title")
        graph.type(title, "melod:Title")
        graph.add(title, "rdfs:label", Literal(entry["title"], lang=LANG))
        graph.add(title, "melod:hasTitleType", Prefixed("terms:MainTitle"))
        graph.add(iri, "melod:hasTitle", title)
        graph.add(iri, "melod:hasAbbreviation", Literal(entry["abbreviation"]))
        publication = blank_node(f"{iri}#publication")
        graph.type(publication, "schema:PublicationEvent")
        if entry.get("start_date"):
            graph.add(publication, "schema:startDate",
                      Literal(entry["start_date"], datatype=XSD + "date"))
        if entry.get("location"):
            graph.add(publication, "schema:location",
                      IRI(ids.place(entry["location"])))
        if entry.get("description"):
            graph.add(publication, "schema:description",
                      Literal(entry["description"]))
        graph.add(iri, "schema:publication", publication)
        self.write("bibliography", iri, graph)


# ---------------------------------------------------------------------------
# works
# ---------------------------------------------------------------------------

class WorkBuilder:
    """Builds the FRBR chain of a work of the acervo."""

    def __init__(self, builder: Builder, people: People):
        self.builder = builder
        self.people = people

    # -- grouping ----------------------------------------------------------
    def expressions(self, work: dict) -> list[dict]:
        """Groups the scores of the work into expressions.

        Scores with different declared arrangers are different expressions.
        Scores with no declared arranger are the original version, unless
        their type declares an anonymous arrangement ("Partitura arranjo").
        The score type is part of the expression as well: a piano score and
        a melody score are different versions, not two manifestations of the
        same version.
        """
        groups: dict[tuple[str, str], dict] = {}
        for score in work["scores"]:
            arranger = (score.get("details", {}).get("Arranjo") or [None])[0]
            score_type = score.get("type") or ""
            if arranger:
                variant = f"arranger:{arranger}"
                descriptor = f"arrangement by {arranger}"
            elif "arranjo" in score_type.lower():
                variant = "anonymous-arrangement"
                descriptor = "anonymous arrangement"
            else:
                variant = "original"
                descriptor = "original version"
            group = groups.setdefault(
                (variant, score_type),
                {"arranger": arranger, "descriptor": descriptor, "scores": []},
            )
            group["scores"].append(score)
        result = []
        for (variant, score_type), group in groups.items():
            result.append({
                "key": f"{variant}:{score_type}",
                "arranger": group["arranger"],
                "label": f"{work['title']} ({group['descriptor']}, {score_type})",
                "scores": group["scores"],
            })
        return result

    def manifestations(self, expression: dict) -> list[dict]:
        """Groups the scores of an expression into manifestations.

        The key is the pair (edition, format): scores of the same format and
        the same editor form one manifestation, even when they are several
        different manuscript copies.
        """
        groups: dict[tuple[str, str], list[dict]] = {}
        for score in expression["scores"]:
            copy = self.copy_of(score)
            key = (self.edition_key(copy), score.get("type") or "")
            groups.setdefault(key, []).append(score)
        result = []
        for (edition, score_type), scores in groups.items():
            result.append({
                "expression": expression["key"],
                "edition": edition,
                "type": score_type,
                "copy": self.copy_of(scores[0]),
                "scores": scores,
            })
        return result

    @staticmethod
    def copy_of(score: dict) -> dict:
        raw = (score.get("details", {}).get("Cópia") or [""])[0]
        return parse_copy(raw)

    @staticmethod
    def edition_key(copy: dict) -> str:
        """Identifier of the edition a score belongs to."""
        if copy.get("publisher"):
            return normalize(copy["publisher"])
        if copy.get("editor"):
            return normalize(copy["editor"])
        return copy.get("kind") or "unknown"

    # -- emitting ----------------------------------------------------------
    def build(self, work: dict) -> None:
        work_iri = ids.work(work["id"])
        graph = Graph()
        graph.type(work_iri, "melod:Work")

        title = blank_node(f"{work_iri}#title")
        graph.type(title, "melod:Title")
        graph.add(title, "rdfs:label", Literal(work["title"], lang=LANG))
        graph.add(title, "melod:hasTitleType", Prefixed("terms:MainTitle"))
        graph.add(work_iri, "melod:hasTitle", title)

        identifier = blank_node(f"{work_iri}#identifier")
        graph.type(identifier, "melod:Identifier")
        graph.add(identifier, "rdfs:label", Literal("Acervo Casa do Choro"))
        graph.add(identifier, "owl:hasValue", Literal(work["id"]))
        graph.add(work_iri, "melod:hasIdentifier", identifier)

        for genre in work.get("fields", {}).get("Gênero", []):
            graph.add(work_iri, "melod:hasClassification", Literal(genre))

        graph.add(work_iri, "owl:sameAs", IRI(work["url"]))

        for composer in work.get("composers", []):
            key = self.people.resolve_card(composer["card"])
            if key is None:
                continue
            graph.add(work_iri, "melod:hasContribution", self.contribution(
                graph, self.people.iri(key), "terms:Composer", "terms:HighCertainty",
                f"{work_iri}#composer{composer['card']}"))

        citation = self.primary_source(work)
        if citation:
            graph.add(work_iri, "schema:citation", IRI(ids.bibliography(citation)))

        for expression in self.expressions(work):
            expression_iri = self.expression(work, expression)
            graph.add(work_iri, "lrmoo:R3_is_realised_in", IRI(expression_iri))
            for manifestation in self.manifestations(expression):
                manifestation_iri = self.manifestation(work, expression, manifestation)
                for score in manifestation["scores"]:
                    self.item(work, manifestation, score)

        annotation = blank_node(f"{work_iri}#annotation")
        graph.type(annotation, "melod:Annotation")
        graph.add(annotation, "rdfs:label", Literal("Record in the archive"))
        graph.add(annotation, "melod:paragraph",
                  Literal(self.work_note(work), datatype=RDF + "HTML"))
        graph.add(work_iri, "melod:hasAnnotation", annotation)

        graph.add(work_iri, "dct:conformsTo", Prefixed("melod:Work"))
        self.builder.write("works", work_iri, graph)

    @staticmethod
    def work_note(work: dict) -> str:
        genre = ", ".join(work.get("fields", {}).get("Gênero", []))
        meter = ", ".join(work.get("fields", {}).get("Compasso", []))
        return (f'<p>Record in the archive: <a href="{work["url"]}">{work["url"]}</a>. '
                f"Gênero: {genre}. Compasso: {meter}. "
                f"The acervo does not show the composition date on the record.</p>")

    def primary_source(self, work: dict) -> str | None:
        """The first source cited on the record of the composer, if any."""
        for composer in work.get("composers", []):
            key = self.people.resolve_card(composer["card"])
            person = self.people.people.get(key) if key else None
            if not person:
                continue
            for source in (person.get("sources") or "").split("\n"):
                source = source.strip()
                if not source:
                    continue
                for entry in self.builder.bibliography:
                    tokens = entry.get("match") or [entry["abbreviation"]]
                    if all(normalize(t) in normalize(source) for t in tokens):
                        return entry["key"]
        return None

    @staticmethod
    def contribution(graph: Graph, agent_iri, role, certainty, seed):
        node = blank_node(seed)
        graph.type(node, "melod:Contribution")
        graph.add(node, "melod:hasAgent", IRI(agent_iri))
        graph.add(node, "melod:hasRole", Prefixed(role))
        if certainty:
            graph.add(node, "melod:hasCertainty", Prefixed(certainty))
        return node

    # -- expression --------------------------------------------------------
    def expression(self, work: dict, expression: dict) -> str:
        iri = ids.expression(work["id"], expression["key"])
        graph = Graph()
        graph.type(iri, "melod:Expression")
        graph.add(iri, "rdfs:label", Literal(expression["label"]))
        for genre in work.get("fields", {}).get("Gênero", []):
            graph.add(iri, "melod:hasClassification", Literal(genre))
        graph.add(iri, "melod:inLanguage", Prefixed("terms:Portuguese"))

        meter = self.meter(work)
        if meter:
            node = blank_node(f"{iri}#meter")
            graph.type(node, "melod:Meter")
            graph.add(node, "melod:hasMeterCount",
                      Literal(str(meter[0]), datatype=XSD + "integer"))
            graph.add(node, "melod:inMeterUnit",
                      Literal(str(meter[1]), datatype=XSD + "integer"))
            graph.add(node, "schema:description", Literal(meter[2]))
            graph.add(iri, "melod:hasMeter", node)

        instruments = []
        for score in expression["scores"]:
            instruments = score.get("details", {}).get("Instrumentação") or []
            if instruments:
                break
        if instruments:
            graph.add(iri, "melod:hasInstrumentation",
                      IRI(self.builder.instrumentation(instruments)))

        if expression["arranger"]:
            key = self.people.resolve(expression["arranger"])
            if key:
                graph.add(iri, "melod:hasContribution", self.contribution(
                    graph, self.people.iri(key), "terms:Arranger",
                    "terms:MediumCertainty", f"{iri}#arranger"))

        for score in expression["scores"]:
            lyricist = (score.get("details", {}).get("Letra") or [None])[0]
            if not lyricist:
                continue
            name = re.sub(r"^Letra de\s+", "", lyricist).strip().rstrip(".")
            key = self.people.resolve(name)
            if key:
                graph.add(iri, "melod:hasContribution", self.contribution(
                    graph, self.people.iri(key), "terms:Librettist",
                    "terms:MediumCertainty", f"{iri}#lyricist{score['index']}"))

        graph.add(iri, "dct:conformsTo", Prefixed("melod:Expression"))
        self.builder.write("expressions", iri, graph)
        return iri

    @staticmethod
    def meter(work: dict) -> tuple[int, int, str] | None:
        """The metre of the acervo ("2/4") as count, unit and description."""
        for value in work.get("fields", {}).get("Compasso", []):
            match = re.match(r"^(\d+)\s*/\s*(\d+)$", value.strip())
            if match:
                return int(match.group(1)), int(match.group(2)), value.strip()
        return None

    # -- manifestation -----------------------------------------------------
    def manifestation(self, work: dict, expression: dict, manifestation: dict) -> str:
        edition = manifestation["edition"]
        score_type = manifestation["type"]
        iri = ids.manifestation(work["id"], expression["key"], edition, score_type)
        graph = Graph()
        graph.type(iri, "melod:Manifestation")

        title = blank_node(f"{iri}#title")
        graph.type(title, "melod:Title")
        graph.add(title, "rdfs:label",
                  Literal(self.manifestation_label(work, manifestation)))
        graph.add(title, "melod:hasTitleType", Prefixed("terms:MainTitle"))
        graph.add(iri, "melod:hasTitle", title)

        graph.add(iri, "lrmoo:R4_embodies",
                  IRI(ids.expression(work["id"], expression["key"])))

        graph.add(iri, "melod:hasClassificationOfManifestation", Literal(score_type))
        copy = manifestation["copy"]
        if copy.get("kind") == "manuscript":
            graph.add(iri, "melod:hasClassificationOfManifestation",
                      Prefixed("terms:Manuscript"))
        elif copy.get("kind") == "print":
            graph.add(iri, "melod:hasClassificationOfManifestation",
                      Prefixed("terms:Print"))
        elif copy.get("kind") == "digital":
            graph.add(iri, "melod:hasClassificationOfManifestation",
                      Literal("Digital transcription"))

        publisher = self.publisher(copy)
        if publisher:
            graph.add(iri, "melod:hasContribution", self.contribution(
                graph, ids.institution(publisher), "terms:Publisher", None,
                f"{iri}#publisher"))
        editor = copy.get("editor")
        if publisher and editor and normalize(editor) == normalize(publisher):
            # the name of a publishing house, not the name of an editor
            editor = None
        if editor:
            key = self.people.resolve(editor)
            if key:
                graph.add(iri, "melod:hasContribution", self.contribution(
                    graph, self.people.iri(key), "terms:Editor",
                    "terms:MediumCertainty", f"{iri}#editor"))

        if publisher:
            # The shape of the publication event requires both the publisher
            # and the place; without a place the event cannot be modelled, so
            # only the publisher contribution is written (see § 4.6).
            location = self.builder.institution_location(publisher)
            if location:
                publication = blank_node(f"{iri}#publication")
                graph.type(publication, "schema:PublicationEvent")
                graph.add(publication, "schema:publishedBy",
                          IRI(ids.institution(publisher)))
                graph.add(publication, "schema:location", IRI(ids.place(location)))
                graph.add(iri, "schema:publication", publication)

        graph.add(iri, "dct:conformsTo", Prefixed("melod:Manifestation"))
        self.builder.write("manifestations", iri, graph)
        return iri

    def manifestation_label(self, work: dict, manifestation: dict) -> str:
        score_type = manifestation["type"]
        copy = manifestation["copy"]
        publisher = self.publisher(copy)
        editor = copy.get("editor")
        if publisher:
            suffix = f" (edition {publisher})"
        elif editor:
            suffix = f" (edition by {editor})"
        elif copy.get("kind") == "manuscript":
            suffix = " (manuscript)"
        elif copy.get("kind") == "print":
            suffix = " (printed edition)"
        elif copy.get("kind") == "digital":
            suffix = " (digital transcription)"
        else:
            suffix = ""
        return f"{work['title']} — {score_type}{suffix}"

    def publisher(self, copy: dict) -> str | None:
        """The publishing house of an edition.

        The names are resolved against the institutions of the dataset (see
        :func:`publisher_name`).
        """
        return publisher_name(copy, self.builder.institutions)

    # -- item --------------------------------------------------------------
    def item(self, work: dict, manifestation: dict, score: dict) -> None:
        iri = ids.item(work["id"], score["index"])
        graph = Graph()
        graph.type(iri, "melod:Item")

        reference = score.get("pdf")
        label = (f"{work['title']} — {score['type']} "
                 f"({reference or 'no digitisation'})")
        graph.add(iri, "rdfs:label", Literal(label))
        graph.add(iri, "lrmoo:R7_exemplifies",
                  IRI(ids.manifestation(work["id"], manifestation["expression"],
                                        manifestation["edition"],
                                        manifestation["type"])))
        graph.add(iri, "melod:hasClassificationOfManifestation",
                  Literal(self.copy_classification(score)))
        graph.add(iri, "cidoc:P50_has_current_keeper", IRI(ids.institution(KEEPER)))

        if reference:
            identifier = blank_node(f"{iri}#identifier")
            graph.type(identifier, "melod:Identifier")
            graph.add(identifier, "rdfs:label",
                      Literal("Acervo Casa do Choro — digitised score"))
            graph.add(identifier, "owl:hasValue", Literal(reference))
            graph.add(iri, "melod:hasIdentifier", identifier)
            # The acervo publishes no shelfmarks; the identifier of the
            # digitised surrogate is used provisionally as a reference.
            graph.add(iri, "melod:hasShelfmark", Literal(reference))
            graph.add(iri, "owl:sameAs", IRI(
                f"https://acervo.casadochoro.com.br/files/uploads/scores/{reference}.pdf"))

        copy = self.copy_of(score)
        if copy.get("copyist"):
            key = self.people.resolve(copy["copyist"])
            if key:
                hand = blank_node(f"{iri}#hand")
                graph.type(hand, "melod:Hand")
                graph.add(hand, "melod:hasAgent", IRI(self.people.iri(key)))
                graph.add(hand, "melod:hasHandType", Prefixed("terms:Writer"))
                graph.add(hand, "schema:description",
                          Literal(f"manuscrita por {copy['copyist']}"))
                graph.add(iri, "melod:hasHand", hand)

        date = (score.get("details", {}).get("Data") or [None])[0]
        iso = parse_date(date) if date else None
        transcriber = copy.get("transcriber")
        if iso or copy.get("former_owner") or transcriber:
            event = blank_node(f"{iri}#provenance")
            graph.type(event, "melod:Event")
            label = ("Provenance of the copy" if iso or copy.get("former_owner")
                     else "Digital transcription")
            graph.add(event, "rdfs:label", Literal(label))
            if iso:
                exact = blank_node(f"{event}#date")
                graph.type(exact, "melod:ExactDate")
                graph.add(exact, "melod:isodate", Literal(iso, datatype=XSD + "date"))
                graph.add(exact, "schema:description", Literal(date))
                graph.add(event, "melod:hasEventDate", exact)
            if copy.get("former_owner"):
                graph.add(event, "schema:description", Literal(copy.get("note") or ""))
            for role, name in (("terms:FormerOwner", copy.get("former_owner")),
                               ("terms:Donor", copy.get("donor")),
                               ("terms:Transcriber", transcriber)):
                if not name:
                    continue
                key = self.people.resolve(name)
                if not key:
                    continue
                node = blank_node(f"{event}#{role.rsplit(':', 1)[-1]}")
                graph.type(node, "melod:Contribution")
                graph.add(node, "melod:hasAgent", IRI(self.people.iri(key)))
                graph.add(node, "melod:hasRole", Prefixed(role))
                graph.add(event, "melod:hasContribution", node)
            graph.add(iri, "melod:hasProvenance", event)

        if score.get("restriction"):
            annotation = blank_node(f"{iri}#annotation")
            graph.type(annotation, "melod:Annotation")
            graph.add(annotation, "rdfs:label",
                      Literal("Access restriction"))
            graph.add(annotation, "melod:paragraph",
                      Literal(f"<p>{score['restriction']}</p>", datatype=RDF + "HTML"))
            graph.add(iri, "melod:hasAnnotation", annotation)

        graph.add(iri, "dct:conformsTo", Prefixed("melod:Item"))
        self.builder.write("items", iri, graph)

    @staticmethod
    def copy_classification(score: dict) -> str:
        copy = parse_copy((score.get("details", {}).get("Cópia") or [""])[0])
        if copy.get("kind") == "manuscript":
            return "Manuscript copy"
        if copy.get("kind") == "print":
            return "Printed copy"
        return "Copy"


# ---------------------------------------------------------------------------
# assembling the set
# ---------------------------------------------------------------------------

def build(works, cards, extra_persons, places, institutions, bibliography,
          instrumentation_labels=None, instrument_terms=None, aliases=None,
          merged=None, countries=None, out_dir=".", verbose=True) -> dict[tuple[str, str], str]:
    """Writes one file per entity and returns the ``(folder, name) → text`` map."""
    people = People(cards, extra_persons, aliases=aliases, merged=merged)
    builder = Builder(
        people,
        place_keys={place["key"] for place in places},
        instrumentation_labels=instrumentation_labels,
        instrument_terms=instrument_terms,
        bibliography=bibliography,
        institutions=institutions,
        countries=countries,
    )

    for place in places:
        builder.place(place)
    for institution in institutions:
        builder.institution(institution)
    for entry in bibliography:
        builder.bibliography_entity(entry)
    for key in people.people:
        builder.person(key)

    work_builder = WorkBuilder(builder, people)
    for work in works:
        work.setdefault("url",
                        f"https://acervo.casadochoro.com.br/works/view/{work['id']}")
        work_builder.build(work)

    for (folder, name), text in builder.files.items():
        target = Path(out_dir) / folder / f"{name}.ttl"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        if verbose:
            print(f"{folder}/{name}.ttl")
    return builder.files


def main(argv=None) -> int:
    from . import sample_data

    parser = argparse.ArgumentParser(description="Export the acervo to MeLODy.")
    parser.add_argument("--out", default=".", help="target directory")
    parser.add_argument("--quiet", action="store_true", help="do not list the files")
    args = parser.parse_args(argv)

    build(
        sample_data.WORKS,
        sample_data.CARDS,
        sample_data.EXTRA_PERSONS,
        sample_data.PLACES,
        sample_data.INSTITUTIONS,
        sample_data.BIBLIOGRAPHY,
        instrumentation_labels=sample_data.INSTRUMENTATION_LABELS,
        instrument_terms=sample_data.INSTRUMENT_TERMS,
        aliases=sample_data.ALIASES,
        merged=sample_data.MERGED_CARDS,
        countries=sample_data.COUNTRIES,
        out_dir=os.path.abspath(args.out),
        verbose=not args.quiet,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
