"""Harvests the Casa do Choro acervo into JSONL files.

The harvest is long (~14 thousand pages) and therefore **resumable**: every
record is written as soon as it is transcribed, and the downloaded HTML is
cached on disk (``$ACERVO_CACHE``, by default ``.cache/acervo``).  Running
the command again only finishes what was missing.

    python3 -m tools.acervo.harvest listing   # only the listing of ids
    python3 -m tools.acervo.harvest works     # the work records
    python3 -m tools.acervo.harvest cards     # the person records
    python3 -m tools.acervo.harvest all       # everything

Options: ``--workers`` (threads), ``--delay`` (seconds between the requests
of each thread) and ``--limit`` (for testing).

The acervo asks for ``Crawl-delay: 10`` in its ``robots.txt``; that is the
default of the module, with four threads.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Iterable

from . import fetch

DATA_DIR = os.environ.get("ACERVO_DATA", fetch.CACHE_DIR)


def data_path(name: str) -> str:
    """Path of a data file inside the harvest directory."""
    return os.path.join(DATA_DIR, name)


def append_record(path: str, record: dict) -> None:
    """Appends a JSON record to a file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def collected_ids(path: str) -> set[str]:
    """Ids already in the file — the harvest resumes from there.

    A record that failed is **not** counted as collected: the next run
    retries it, and the successful record replaces the error in the
    ingestion.
    """
    collected: set[str] = set()
    if not os.path.exists(path):
        return collected
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("error"):
                continue
            collected.add(str(record.get("id")))
    return collected


def save_ids(name: str, ids: Iterable[str]) -> None:
    """Writes the listing of ids, one per line."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(data_path(name), "w", encoding="utf-8") as handle:
        for item_id in ids:
            handle.write(item_id + "\n")


def read_ids(name: str) -> list[str]:
    """Reads the listing of ids that was written."""
    with open(data_path(name), encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


# ---------------------------------------------------------------------------
# listing
# ---------------------------------------------------------------------------

def collect_listing(workers: int, delay: float) -> None:
    """Walks the listings of works and of persons."""
    print("listing the works…", flush=True)
    start = time.time()
    works = list(fetch.iter_work_ids(workers=workers, delay=delay))
    save_ids("work_ids.txt", works)
    print(f"  {len(works)} works in {time.time() - start:.0f}s", flush=True)

    print("listing the persons…", flush=True)
    start = time.time()
    people = list(fetch.iter_card_ids(workers=workers, delay=delay))
    save_ids("card_ids.txt", people)
    print(f"  {len(people)} persons in {time.time() - start:.0f}s", flush=True)


# ---------------------------------------------------------------------------
# records
# ---------------------------------------------------------------------------

def collect_records(kind: str, ids: list[str], workers: int, delay: float) -> None:
    """Harvests the records of one kind of entity, resuming what exists."""
    path = data_path(f"{kind}.jsonl")
    already = collected_ids(path)
    missing = [i for i in ids if i not in already]
    print(f"{kind}: {len(missing)} records to harvest ({len(already)} already collected)", flush=True)

    collector = fetch.iter_works if kind == "works" else fetch.iter_cards
    start = time.time()
    for n, record in enumerate(collector(missing, workers=workers, delay=delay), start=1):
        append_record(path, record)
        if n % 50 == 0 or n == len(missing):
            elapsed = time.time() - start
            remaining = (elapsed / n) * (len(missing) - n)
            print(
                f"  {n}/{len(missing)} — {elapsed / 60:.1f} min elapsed, "
                f"~{remaining / 60:.0f} min remaining",
                flush=True,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=["listing", "works", "cards", "all"])
    parser.add_argument("--workers", type=int, default=fetch.WORKERS)
    parser.add_argument("--delay", type=float, default=fetch.CRAWL_DELAY)
    parser.add_argument("--limit", type=int, default=0, help="harvest only N records (testing)")
    arguments = parser.parse_args()

    if arguments.target in ("listing", "all"):
        collect_listing(arguments.workers, arguments.delay)

    if arguments.target in ("works", "all"):
        ids = read_ids("work_ids.txt")
        if arguments.limit:
            ids = ids[:arguments.limit]
        collect_records("works", ids, arguments.workers, arguments.delay)

    if arguments.target in ("cards", "all"):
        ids = read_ids("card_ids.txt")
        if arguments.limit:
            ids = ids[:arguments.limit]
        collect_records("cards", ids, arguments.workers, arguments.delay)

    return 0


if __name__ == "__main__":
    sys.exit(main())
