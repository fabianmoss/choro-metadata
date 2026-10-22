"""Tools for modelling the Casa do Choro acervo in MerMEId/MeLODy.

The package contains four parts:

``fetch``
    Harvests (scrapes) the work and person records of the acervo
    <https://acervo.casadochoro.com.br/> and returns dictionaries holding
    the verbatim data of the site.

``harvest``
    Drives a full harvest of the acervo into JSONL files, resumable and
    backed by an on-disk cache of the downloaded HTML.

``ids``
    Derives deterministic IRIs from the acervo identifiers, so that
    re-running the exporter produces exactly the same files.

``sample``
    Applies the FRBR mapping (work → expression → manifestation → item) to
    the collected records and writes one Turtle file per entity.

The mapping is documented in ``docs/acervo-model.md``.
"""

__all__ = ["fetch", "harvest", "ids", "sample"]
