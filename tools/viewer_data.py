"""Builds the data files of the local graph viewer.

The viewer does not parse the Turtle files itself.  This script reads every
entity document once and writes two small JSONL files:

``viewer/data/nodes.jsonl``
    One record per entity: IRI, type, label and the relative path of the
    Turtle document.  The viewer fetches that document when the node is
    selected, so the information panel can show the complete metadata without
    inflating the graph file.

``viewer/data/edges.jsonl``
    One record per relationship.  The ``kind`` field tells the viewer which
    shape the edge has in the display tree; all remaining edges are drawn as
    dashed cross-links.

The output is deterministic: re-running the script over the same documents
produces the same bytes, except for the order of labels inside a document
(which the model does not use).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from rdflib import Graph, Namespace, RDF, RDFS, URIRef
except ImportError:  # pragma: no cover - optional dependency
    sys.exit("This script needs rdflib: pip install rdflib")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "viewer" / "data"

MELOD = Namespace("https://lod.academy/melod/vocab/ontology#")
TERMS = Namespace("https://lod.academy/melod/vocab/terms#")
LRMOO = Namespace("http://iflastandards.info/ns/lrm/lrmoo/")
SCHEMA = Namespace("https://schema.org/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
CIDOC = Namespace("http://www.cidoc-crm.org/cidoc-crm/")

FOLDERS = (
    "works",
    "expressions",
    "manifestations",
    "items",
    "persons",
    "institutions",
    "places",
    "instrumentations",
    "bibliography",
    "venues",
    "performanceEvents",
)

FOLDER_TYPE = {
    "works": "Work",
    "expressions": "Expression",
    "manifestations": "Manifestation",
    "items": "Item",
    "persons": "Person",
    "institutions": "Institution",
    "places": "Place",
    "instrumentations": "Instrumentation",
    "bibliography": "Bibliography",
    "venues": "Venue",
    "performanceEvents": "PerformanceEvent",
}

KNOWN_TYPES = {f"{MELOD}{name}" for name in FOLDER_TYPE.values()}

ROLE_LABELS = {
    "Composer": ("composer", "composer"),
    "Arranger": ("arranger", "arranger"),
    "Librettist": ("librettist", "librettist"),
    "Publisher": ("publisher", "publisher"),
    "Writer": ("copyist", "copyist"),
    "FormerOwner": ("former owner", "provenance"),
    "Donor": ("donor", "provenance"),
    "Editor": ("editor", "contribution"),
}

DIRECT_EDGES = {
    LRMOO.R3_is_realised_in: ("realises", "has expression"),
    LRMOO.R4_embodies: ("embodies", "embodies"),
    LRMOO.R7_exemplifies: ("exemplifies", "exemplifies"),
    MELOD.hasWorkPart: ("work part", "has work part"),
    MELOD.hasExpressionPart: ("expression part", "has expression part"),
    MELOD.hasManifestationPart: ("manifestation part", "has manifestation part"),
    MELOD.hasItemPart: ("item part", "has item part"),
    MELOD.hasInstrumentation: ("instrumentation", "instrumentation"),
    MELOD.memberOfDataCollection: ("collection", "member of collection"),
    MELOD.hasPerformance: ("performance", "has performance"),
    MELOD.hasHistoricEvent: ("event", "has historic event"),
    MELOD.hasVenue: ("venue", "venue"),
    SCHEMA.firstPerformance: ("performance", "first performance"),
    SCHEMA.citation: ("citation", "cites"),
    SCHEMA.locationCreated: ("place", "place of creation"),
    SCHEMA.includedComposition: ("included composition", "includes composition"),
    CIDOC.P50_has_current_keeper: ("keeper", "kept by"),
    SCHEMA.containedInPlace: ("place", "contained in place"),
}

PREFIXES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "schema": "https://schema.org/",
    "melod": str(MELOD),
    "terms": str(TERMS),
    "lrmoo": str(LRMOO),
    "cidoc": str(CIDOC),
    "owl": "http://www.w3.org/2002/07/owl#",
}


def local_name(value: object) -> str:
    text = str(value)
    for separator in ("#", "/"):
        if separator in text:
            text = text.rsplit(separator, 1)[-1]
    return text or str(value)


def space_name(value: object) -> str:
    text = local_name(value)
    out = []
    for index, char in enumerate(text):
        if char.isupper() and index and not text[index - 1].isupper():
            out.append(" ")
        out.append(char)
    return "".join(out).lower()


def compact(value: object) -> str:
    text = str(value)
    for prefix, namespace in PREFIXES.items():
        if text.startswith(namespace):
            return f"{prefix}:{text[len(namespace):]}"
    return text


def term_text(value: object) -> str:
    """A human readable string for a literal or IRI."""
    return str(value).strip()


def first_literal(graph: Graph, subject, predicates) -> str | None:
    for predicate in predicates:
        for value in graph.objects(subject, predicate):
            if isinstance(value, URIRef):
                continue
            text = term_text(value)
            if text:
                return text
    return None


def title_label(graph: Graph, subject) -> str | None:
    """The main title of a work, manifestation or bibliography."""
    titles = list(graph.objects(subject, MELOD.hasTitle))
    for title in titles:
        types = set(graph.objects(title, MELOD.hasTitleType))
        if TERMS.MainTitle in types:
            label = first_literal(graph, title, (RDFS.label,))
            if label:
                return label
    for title in titles:
        label = first_literal(graph, title, (RDFS.label,))
        if label:
            return label
    return None


def label_for(graph: Graph, subject: URIRef, type_name: str) -> str:
    if type_name == "Person":
        family = first_literal(graph, subject, (SCHEMA.familyName,))
        given = first_literal(graph, subject, (SCHEMA.givenName,))
        if family and given:
            return f"{family}, {given}"
        if family or given:
            return family or given or local_name(subject)

    if type_name in {"Work", "Manifestation", "Bibliography"}:
        label = title_label(graph, subject)
        if label:
            return label

    label = first_literal(
        graph,
        subject,
        (
            SCHEMA.name,
            SKOS.prefLabel,
            RDFS.label,
            SCHEMA.title,
            MELOD.hasAbbreviation,
        ),
    )
    if label:
        return label

    if type_name == "Bibliography":
        return local_name(subject)
    return local_name(subject)


def subject_of(graph: Graph, folder: str) -> URIRef | None:
    candidates: list[URIRef] = []
    for subject in set(graph.subjects()):
        if not isinstance(subject, URIRef) or not str(subject).startswith("urn:uuid:"):
            continue
        types = set(graph.objects(subject, RDF.type))
        if types & KNOWN_TYPES:
            candidates.append(subject)
    if candidates:
        # Every document has exactly one entity subject; if a template document
        # contains something unexpected, prefer the subject in the folder's
        # namespace.
        folder_prefix = f"urn:uuid:{folder}/"
        for candidate in candidates:
            if str(candidate).startswith(folder_prefix):
                return candidate
        return sorted(candidates, key=str)[0]

    for subject in graph.subjects():
        if isinstance(subject, URIRef) and str(subject).startswith("urn:uuid:"):
            return subject
    return None


def type_of(graph: Graph, subject: URIRef, folder: str) -> str:
    for value in graph.objects(subject, RDF.type):
        if value in KNOWN_TYPES:
            return local_name(value)
    return FOLDER_TYPE.get(folder, "Entity")


def role_info(graph: Graph, node) -> tuple[str, str]:
    for role in graph.objects(node, MELOD.hasRole):
        name = local_name(role)
        return ROLE_LABELS.get(name, (space_name(role), "contribution"))
    for hand_type in graph.objects(node, MELOD.hasHandType):
        name = local_name(hand_type)
        if name == "Writer":
            return "copyist", "copyist"
        return space_name(hand_type), "copyist"
    return "contribution", "contribution"


class Edges:
    def __init__(self) -> None:
        self._edges: dict[tuple[str, str, str, str], dict] = {}

    def add(
        self,
        source: URIRef,
        target: URIRef,
        predicate,
        kind: str,
        label: str,
    ) -> None:
        key = (str(source), str(target), compact(predicate), kind)
        if key in self._edges:
            return
        self._edges[key] = {
            "source": str(source),
            "target": str(target),
            "predicate": compact(predicate),
            "kind": kind,
            "label": label,
        }

    def sorted(self) -> list[dict]:
        return [self._edges[key] for key in sorted(self._edges)]


def add_direct_edges(graph: Graph, subject: URIRef, edges: Edges) -> None:
    for predicate, (kind, label) in DIRECT_EDGES.items():
        for target in graph.objects(subject, predicate):
            if isinstance(target, URIRef) and str(target).startswith("urn:uuid:"):
                edges.add(subject, target, predicate, kind, label)


def add_contribution_edges(graph: Graph, subject: URIRef, edges: Edges) -> None:
    for contribution in graph.objects(subject, MELOD.hasContribution):
        label, kind = role_info(graph, contribution)
        for agent in graph.objects(contribution, MELOD.hasAgent):
            if isinstance(agent, URIRef) and str(agent).startswith("urn:uuid:"):
                edges.add(subject, agent, MELOD.hasContribution, kind, label)


def add_hand_edges(graph: Graph, subject: URIRef, edges: Edges) -> None:
    for hand in graph.objects(subject, MELOD.hasHand):
        label, kind = role_info(graph, hand)
        for agent in graph.objects(hand, MELOD.hasAgent):
            if isinstance(agent, URIRef) and str(agent).startswith("urn:uuid:"):
                edges.add(subject, agent, MELOD.hasHand, kind, label)


def add_provenance_edges(graph: Graph, subject: URIRef, edges: Edges) -> None:
    for provenance in graph.objects(subject, MELOD.hasProvenance):
        for contribution in graph.objects(provenance, MELOD.hasContribution):
            label, _ = role_info(graph, contribution)
            for agent in graph.objects(contribution, MELOD.hasAgent):
                if isinstance(agent, URIRef) and str(agent).startswith("urn:uuid:"):
                    edges.add(subject, agent, MELOD.hasProvenance, "provenance", label)


def add_publication_edges(graph: Graph, subject: URIRef, edges: Edges) -> None:
    for publication in graph.objects(subject, SCHEMA.publication):
        for publisher in graph.objects(publication, SCHEMA.publishedBy):
            if isinstance(publisher, URIRef) and str(publisher).startswith("urn:uuid:"):
                edges.add(subject, publisher, SCHEMA.publication, "publisher", "publisher")
        for place in graph.objects(publication, SCHEMA.location):
            if isinstance(place, URIRef) and str(place).startswith("urn:uuid:"):
                edges.add(subject, place, SCHEMA.publication, "publication place", "publication place")


def add_fallback_edges(graph: Graph, subject: URIRef, edges: Edges) -> None:
    """Adds relationships that have no special mapping above.

    The known predicates are handled separately because their blank-node
    structures carry a role.  Everything else is still a relationship between
    two local entities and should be visible in the graph.
    """
    handled = set(DIRECT_EDGES)
    handled.update({MELOD.hasContribution, MELOD.hasHand, MELOD.hasProvenance, SCHEMA.publication})
    for predicate, target in graph.predicate_objects(subject):
        if predicate in handled:
            continue
        if isinstance(target, URIRef) and str(target).startswith("urn:uuid:"):
            edges.add(subject, target, predicate, "related", space_name(predicate))


def read_entity(path: Path, folder: str, edges: Edges) -> dict | None:
    try:
        graph = Graph().parse(path, format="turtle")
    except Exception as exc:  # pragma: no cover - corrupt input is reported
        print(f"warning: {path}: {exc}", file=sys.stderr)
        return None

    subject = subject_of(graph, folder)
    if subject is None:
        print(f"warning: {path}: no entity subject", file=sys.stderr)
        return None

    type_name = type_of(graph, subject, folder)
    add_direct_edges(graph, subject, edges)
    add_contribution_edges(graph, subject, edges)
    add_hand_edges(graph, subject, edges)
    add_provenance_edges(graph, subject, edges)
    add_publication_edges(graph, subject, edges)
    add_fallback_edges(graph, subject, edges)

    return {
        "id": str(subject),
        "type": type_name,
        "label": label_for(graph, subject, type_name),
        "path": f"{folder}/{path.name}",
    }


def build(out_dir: Path) -> tuple[int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    edges = Edges()
    nodes: list[dict] = []
    for folder in FOLDERS:
        directory = ROOT / folder
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.ttl")):
            node = read_entity(path, folder, edges)
            if node is not None:
                nodes.append(node)

    nodes.sort(key=lambda node: node["id"])
    edge_list = edges.sorted()

    with open(out_dir / "nodes.jsonl", "w", encoding="utf-8") as handle:
        for node in nodes:
            handle.write(json.dumps(node, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    with open(out_dir / "edges.jsonl", "w", encoding="utf-8") as handle:
        for edge in edge_list:
            handle.write(json.dumps(edge, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    return len(nodes), len(edge_list)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output directory (default: viewer/data)")
    args = parser.parse_args()
    nodes, edges = build(args.out)
    print(f"{nodes} nodes, {edges} edges -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
