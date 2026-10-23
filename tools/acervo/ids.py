"""Deterministic IRIs for the entities derived from the acervo.

The acervo publishes no IRIs of its own, only numeric identifiers
(``/works/view/771``, ``/cards/view/1127``).  For the exported files to be
stable — re-running the exporter must produce exactly the same bytes — the
IRIs are derived by hashing the acervo identifier together with the role the
entity plays.

Scheme
------

===========================  ==========================================
``urn:uuid:works/<n>``       musical work
``urn:uuid:expressions/<n>`` expression (version, arrangement)
``urn:uuid:manifestations/`` manifestation (edition / format)
``urn:uuid:items/<n>``       item (digitised physical copy)
``urn:uuid:persons/<n>``     person
``urn:uuid:places/<n>``      place
``urn:uuid:institutions/``   institution
``urn:uuid:instrumentations`` instrumentation
``urn:uuid:bibliography/``   bibliographic reference
===========================  ==========================================

The hash key is ``int(sha1(key).hexdigest()[:10], 16) % (9 * 10**8) +
10**9``, which produces a ten-digit number — the same format used by the
MeLODy model files.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "h",
    "work",
    "expression",
    "manifestation",
    "item",
    "person",
    "place",
    "institution",
    "instrumentation",
    "bibliography",
    "slug",
]


def h(key: str) -> int:
    """Deterministic hash of ``key`` to a ten-digit number.

    The result lies in ``[1.000.000.000, 1.899.999.999]`` — the same
    format as the MeLODy model files.  The modulus is ``9 * 10**8``, so
    the ten digits are filled by the hash and not by leading zeros.
    """
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return int(digest, 16) % (9 * 10**8) + 10**9


def slug(text: str) -> str:
    """Normalises a free text for use in hash keys.

    Accents are removed, the text is lowercased and everything that is not
    alphanumeric becomes ``_``, so that "Partitura melodia e cifra" and
    "partitura melodia e cifra" produce the same key.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"_+", "_", re.sub(r"[^0-9A-Za-z]+", "_", stripped.lower())).strip("_")


def work(acervo_id: str) -> str:
    return f"urn:uuid:works/{h('work:' + acervo_id)}"


def expression(acervo_id: str, variant: str) -> str:
    """``variant`` identifies the version (arranger and score type)."""
    return f"urn:uuid:expressions/{h('expr:' + acervo_id + ':' + slug(variant))}"


def manifestation(acervo_id: str, variant: str, edition: str, score_type: str) -> str:
    """``variant``, ``edition`` and ``score_type`` identify the publication.

    The variant (the arranger and score type, or the original version) is part
    of the key because a manifestation embodies exactly one expression: the
    manuscript of an arrangement and the manuscript of the original work are
    different manifestations even when both are manuscripts of the same format.
    """
    key = ('man:' + acervo_id + ':' + slug(variant) + ':' + slug(edition)
           + ':' + slug(score_type))
    return f"urn:uuid:manifestations/{h(key)}"


def item(acervo_id: str, index: int) -> str:
    """``index`` is the position of the copy in the acervo record (0-based)."""
    return f"urn:uuid:items/{h('item:' + acervo_id + ':' + str(index))}"


def person(key: str) -> str:
    """``key`` is the id of the acervo card, or a normalised name."""
    return f"urn:uuid:persons/{h('person:' + key)}"


def place(name: str) -> str:
    return f"urn:uuid:places/{h('place:' + name)}"


def institution(name: str) -> str:
    return f"urn:uuid:institutions/{h('inst:' + name)}"


def instrumentation(name: str) -> str:
    return f"urn:uuid:instrumentations/{h('instr:' + name)}"


def bibliography(key: str) -> str:
    return f"urn:uuid:bibliography/{h('bib:' + key)}"
