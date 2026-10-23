"""Tests of the bulk ingestion (``python3 -m unittest``).

The tests build a miniature harvest in a temporary directory: one work with
a score that mentions a copyist the acervo does not record, so that the
provisional-person path and the pruning of a later run are exercised.
"""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.acervo import ids, ingest


def work_record() -> dict:
    return {
        "id": "1",
        "url": "https://acervo.casadochoro.com.br/works/view/1",
        "title": "Test work",
        "fields": {"Gênero": ["Choro"], "Compasso": ["2/4"]},
        "composers": [{"card": "1", "name": "Test Composer"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura melodia",
                "pdf": "score_1",
                "details": {
                    "Cópia": ["manuscrita por Unknown Copyist"],
                    "Data": ["01.02.1950"],
                },
                "editorada": False,
                "restriction": None,
            }
        ],
    }


def card_record() -> dict:
    return {
        "id": "1",
        "url": "https://acervo.casadochoro.com.br/cards/view/1",
        "name": "Test Composer",
        "inverted": "Composer, Test",
        "roles": ["Compositor"],
        "birth": "01.01.1900",
        "death": "",
        "birth_place": "Rio de Janeiro - RJ",
        "sources": "",
        "bio": "",
        "nworks": 1,
    }


class IngestionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.harvest = self.root / "harvest"
        self.out = self.root / "out"
        self.harvest.mkdir()
        self.out.mkdir()

        with open(self.harvest / "works.jsonl", "w", encoding="utf-8") as handle:
            handle.write(json.dumps(work_record(), ensure_ascii=False) + "\n")
        with open(self.harvest / "cards.jsonl", "w", encoding="utf-8") as handle:
            handle.write(json.dumps(card_record(), ensure_ascii=False) + "\n")

        self.issues_md = self.root / "issues.md"
        self.issues_csv = self.root / "issues.csv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_ingest(self, prune: bool = True) -> dict:
        with redirect_stdout(io.StringIO()):
            return ingest.ingest(
                str(self.harvest),
                str(self.out),
                str(self.issues_md),
                str(self.issues_csv),
                verbose=False,
                prune=prune,
            )

    def test_digitised_requires_a_pdf(self) -> None:
        self.assertTrue(ingest.digitised(work_record()))
        self.assertFalse(ingest.digitised({"scores": [{"pdf": None}]}))

    def test_work_expression_manifestation_item(self) -> None:
        self.run_ingest()
        work_iri = ids.work("1")
        work_file = self.out / "works" / f"{work_iri.rsplit('/', 1)[-1]}.ttl"
        self.assertTrue(work_file.exists())
        text = work_file.read_text(encoding="utf-8")
        self.assertIn("a melod:Work", text)
        self.assertIn("Test work", text)

        manifestations = [
            path.read_text(encoding="utf-8")
            for path in (self.out / "manifestations").glob("*.ttl")
        ]
        self.assertTrue(any("Test work" in text for text in manifestations))

        items = [
            path.read_text(encoding="utf-8")
            for path in (self.out / "items").glob("*.ttl")
        ]
        self.assertTrue(any("score_1" in text for text in items))

    def test_unknown_copyist_becomes_a_provisional_person(self) -> None:
        self.run_ingest()
        key = "name:" + ingest.normalize("Unknown Copyist")
        person_iri = ids.person(key)
        person_file = self.out / "persons" / f"{person_iri.rsplit('/', 1)[-1]}.ttl"
        self.assertTrue(person_file.exists())
        text = person_file.read_text(encoding="utf-8")
        self.assertIn("provisional", text)

        with open(self.issues_csv, encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(
            any(row["category"] == "provisional_person" for row in rows),
            rows,
        )

    def test_a_known_name_does_not_become_provisional(self) -> None:
        record = work_record()
        record["scores"][0]["details"]["Cópia"] = [
            "manuscrita por Test Composer"
        ]
        with open(self.harvest / "works.jsonl", "w", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        self.run_ingest()
        key = "name:" + ingest.normalize("Test Composer")
        provisional = self.out / "persons" / f"{ids.person(key).rsplit('/', 1)[-1]}.ttl"
        self.assertFalse(provisional.exists())

    def test_pruning_keeps_the_template_documents(self) -> None:
        template = next(
            line.strip()
            for line in ingest.TEMPLATE_MANIFEST.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        )
        template_path = self.out / template
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text("# upstream template\n", encoding="utf-8")

        stale = self.out / "persons" / "9999999999.ttl"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("# stale\n", encoding="utf-8")

        context = self.run_ingest()
        self.assertFalse(stale.exists())
        self.assertTrue(template_path.exists())
        self.assertEqual(context["stale_removed"], 1)

    def test_no_prune_keeps_the_documents_of_an_earlier_run(self) -> None:
        stale = self.out / "persons" / "9999999999.ttl"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("# stale\n", encoding="utf-8")
        self.run_ingest(prune=False)
        self.assertTrue(stale.exists())

    def test_harvest_complete_requires_every_listed_record(self) -> None:
        self.assertFalse(ingest.harvest_complete(self.harvest))
        (self.harvest / "work_ids.txt").write_text("1\n", encoding="utf-8")
        (self.harvest / "card_ids.txt").write_text("1\n", encoding="utf-8")
        self.assertTrue(ingest.harvest_complete(self.harvest))
        (self.harvest / "work_ids.txt").write_text("1\n2\n", encoding="utf-8")
        self.assertFalse(ingest.harvest_complete(self.harvest))

    def test_missing_cards_are_reported_in_english(self) -> None:
        with open(self.harvest / "cards.jsonl", "w", encoding="utf-8"):
            pass
        os.remove(self.harvest / "cards.jsonl")
        self.run_ingest()
        with open(self.issues_csv, encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        categories = {row["category"] for row in rows}
        self.assertIn("composer_card_not_harvested", categories)
        for row in rows:
            self.assertFalse(row["category"][0].isupper(), row)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
