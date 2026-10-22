"""Generates the projections (indexes) that the editor loads in its dropdowns.

The CI uses the ``static-publishing-backend``, which runs inside a container
and is not available outside it.  This script does the same work locally,
with ``rdflib``:

    python3 -m tools.datasets --out indexes

Every SPARQL module in ``modules/datasets-generator`` is a projection: the
input is a folder of entities, the output is a Turtle file with the search
label (``skos:prefLabel``) and the links (``skos:related``, ``skos:broader``)
the editor uses to build the menus.

The order of the triples is irrelevant to the editor — the file is a graph —
but it is deterministic here so that the diff stays readable.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

try:
    from rdflib import BNode, Graph, Literal, URIRef
except ImportError:  # pragma: no cover - optional dependency
    sys.exit(
        "This script needs rdflib: pip install rdflib"
    )

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = os.path.join(ROOT, "modules", "datasets-generator")

# Module -> input folders, as in the CI's ``datasets-generator.sh``.
# The CI's globs are wide (``[wp]*/*.ttl``); the queries filter by type, so
# the extra folders do not change the result — here each module reads only
# the folders it cares about.
PROJECTIONS = (
    ("persons", ("persons",)),
    ("institutions", ("institutions",)),
    ("places", ("places",)),
    ("venues", ("venues",)),
    ("performanceEvents", ("performanceEvents",)),
    ("instrumentations", ("instrumentations",)),
    ("works", ("works",)),
    ("expressions", ("expressions",)),
    ("manifestations", ("manifestations",)),
    ("items", ("items",)),
    ("bibliography", ("bibliography",)),
)

ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def escape_literal(value: str) -> str:
    """Escapes a literal for the Turtle syntax."""
    return "".join(ESCAPES.get(character, character) for character in value)


def term(term) -> str:
    """Serialises an rdflib term in the Turtle syntax."""
    if isinstance(term, URIRef):
        return f"<{term}>"
    if isinstance(term, BNode):
        return f"_:{term}"
    if isinstance(term, Literal):
        text = f'"{escape_literal(str(term))}"'
        if term.language:
            return f"{text}@{term.language}"
        if term.datatype:
            return f"{text}^^<{term.datatype}>"
        return text
    raise TypeError(f"unexpected term: {term!r}")


def load(folders: tuple[str, ...]) -> Graph:
    """Reads the Turtle files of the given folders into a single graph."""
    graph = Graph()
    for folder in folders:
        for path in sorted(glob.glob(os.path.join(ROOT, folder, "*.ttl"))):
            graph.parse(path, format="turtle")
    return graph


def read_query(name: str) -> str:
    """Reads the SPARQL module of the given projection."""
    with open(os.path.join(MODULES, f"{name}.sparql"), encoding="utf-8") as handle:
        return handle.read()


def project(name: str, folders: tuple[str, ...]) -> Graph:
    """Runs the SPARQL module of the given projection over the given folders."""
    graph = Graph()
    graph += load(folders).query(read_query(name))
    return graph


def write(graph: Graph, path: str) -> None:
    """Writes the graph as Turtle, one triple per line, in a stable order."""
    lines = []
    for subject, predicate, obj in graph:
        lines.append(f"{term(subject)} {term(predicate)} {term(obj)} .")
    lines.sort()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=os.path.join(ROOT, "indexes"),
        help="output folder for the indexes (default: indexes/)",
    )
    arguments = parser.parse_args()

    os.makedirs(arguments.out, exist_ok=True)
    for name, folders in PROJECTIONS:
        graph = project(name, folders)
        path = os.path.join(arguments.out, f"{name}.ttl")
        write(graph, path)
        print(f"{name}: {len(graph)} triples → {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
