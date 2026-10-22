"""Minimal Turtle writer for the MeLODy entity files.

The exporter writes one file per entity, so all that is needed is:
prefixed names for predicates, IRIs, blank nodes and literals with an
optional language tag or datatype.

The output is deterministic.  The labels of the blank nodes are computed
from the IRI of the entity and the role the node plays, so that two runs
produce byte-identical files — and that blank node labels never collide
between different files (the validator loads all files into a single
graph).
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

__all__ = ["IRI", "BNode", "Prefixed", "Literal", "Graph", "PREFIXES", "blank_node"]

PREFIXES: list[tuple[str, str]] = [
    ("cidoc", "http://www.cidoc-crm.org/cidoc-crm/"),
    ("dct", "http://purl.org/dc/terms/"),
    ("lrmoo", "http://iflastandards.info/ns/lrm/lrmoo/"),
    ("melod", "https://lod.academy/melod/vocab/ontology#"),
    ("mus", "http://data.doremus.org/ontology#"),
    ("owl", "http://www.w3.org/2002/07/owl#"),
    ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
    ("schema", "https://schema.org/"),
    ("sh", "http://www.w3.org/ns/shacl#"),
    ("skos", "http://www.w3.org/2004/02/skos/core#"),
    ("terms", "https://lod.academy/melod/vocab/terms#"),
    ("xsd", "http://www.w3.org/2001/XMLSchema#"),
]

#: Namespace used to derive the blank node labels.
BNODE_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


class IRI(str):
    """Absolute IRI in object position."""


class BNode(str):
    """Blank node label."""


class Prefixed(str):
    """Prefixed name in object position (e.g. ``melod:Person``)."""


@dataclass(frozen=True)
class Literal:
    """Simple RDF literal, with an optional language or datatype."""

    value: str
    lang: str | None = None
    datatype: str | None = None

    def render(self) -> str:
        out = '"' + escape(self.value) + '"'
        if self.lang:
            return out + "@" + self.lang
        if self.datatype:
            return out + "^^" + prefixed(self.datatype)
        return out


def prefixed(iri: str) -> str:
    """Turns a known IRI into a prefixed name.

    Returns the IRI itself between angle brackets when its namespace is
    not among the declared prefixes.
    """
    for prefix, namespace in PREFIXES:
        if iri.startswith(namespace):
            local = iri[len(namespace):]
            if local and not local[0].isdigit():
                return f"{prefix}:{local}"
    return f"<{iri}>"


def escape(text: str) -> str:
    """Escapes a string for use in a Turtle literal."""
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


def blank_node(seed: str) -> BNode:
    """Deterministic blank node label derived from ``seed``."""
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return BNode("b" + str(uuid.UUID(digest[:32])))


def render_object(obj) -> str:
    if isinstance(obj, Literal):
        return obj.render()
    if isinstance(obj, Prefixed):
        return str(obj)
    if isinstance(obj, BNode):
        return "_:" + obj
    return "<" + str(obj) + ">"


class Graph:
    """Simple Turtle graph: a list of subject → predicate → object."""

    def __init__(self) -> None:
        self._subjects: dict[str, list[tuple[str, object]]] = {}
        self._order: list[str] = []
        self._bnode_labels: set[str] = set()

    # -- writing ---------------------------------------------------------
    def add(self, subject, predicate: str, obj) -> None:
        key = str(subject)
        if isinstance(subject, BNode):
            self._bnode_labels.add(key)
        if key not in self._subjects:
            self._subjects[key] = []
            self._order.append(key)
        self._subjects[key].append((predicate, obj))

    def add_many(self, subject, predicate: str, objects) -> None:
        for obj in objects:
            self.add(subject, predicate, obj)

    def type(self, subject, *types: str) -> None:
        for name in types:
            self.add(subject, "a", Prefixed(name))

    # -- reading ---------------------------------------------------------
    def has(self, subject, predicate: str) -> bool:
        return any(p == predicate for p, _ in self._subjects.get(str(subject), []))

    # -- output -----------------------------------------------------------
    def render(self, prefixes=PREFIXES) -> str:
        lines = [f"@prefix {prefix}: <{uri}>." for prefix, uri in prefixes]
        lines.append("")
        for key in self._order:
            props = self._subjects[key]
            if not props:
                continue
            grouped: dict[str, list] = {}
            for predicate, obj in props:
                grouped.setdefault(predicate, []).append(obj)
            subject = "_:" + key if key in self._bnode_labels else "<" + key + ">"
            block: list[str] = []
            for predicate, objects in grouped.items():
                rendered = ", ".join(render_object(o) for o in objects)
                block.append(f"{subject} {predicate} {rendered}" if not block
                             else f"    {predicate} {rendered}")
            for i, line in enumerate(block):
                lines.append(line + ("." if i == len(block) - 1 else ";"))
            lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"
