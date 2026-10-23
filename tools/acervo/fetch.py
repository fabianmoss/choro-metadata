"""Harvests the work and person records of the Casa do Choro acervo.

The acervo is the primary source: <https://acervo.casadochoro.com.br/>.  This
module only **harvests and transcribes** — it returns dictionaries holding the
verbatim values of the site, without any modelling decision.  The mapping to
the FRBR model lives in :mod:`tools.acervo.sample`.

URLs
----

``/works/view/<id>``        work record
``/cards/view/<id>``        person record
``/Works/index?letra=A``    alphabetical listing (15 works per page)
``/Cards/index?name=..``    person listing

Politeness
----------

The ``robots.txt`` of the acervo asks for ``Crawl-delay: 10``.  The harvesting
functions respect that interval by default; :func:`iter_works` uses four
threads and ``time.sleep`` between the requests of each thread.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Iterator

__all__ = [
    "ACERVO",
    "WORK_URL",
    "CARD_URL",
    "CACHE_DIR",
    "get",
    "parse_work",
    "parse_card",
    "iter_work_ids",
    "iter_card_ids",
    "iter_works",
    "iter_cards",
    "parse_copy",
]

ACERVO = "https://acervo.casadochoro.com.br"
WORK_URL = ACERVO + "/works/view/{0}"
CARD_URL = ACERVO + "/cards/view/{0}"

USER_AGENT = "choro-metadata/1.0 (acervo harvesting for metadata; contact: github.com/fabianmoss/choro)"

#: Where the cache of the downloaded HTML lives.  A full harvest is ~14
#: thousand pages; keeping the HTML lets the mapping be re-run without
#: touching the acervo again.
CACHE_DIR = os.environ.get(
    "ACERVO_CACHE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), ".cache", "acervo"),
)

#: Minimum interval between requests to the same host, in seconds.
#: The ``robots.txt`` of the acervo asks for ``Crawl-delay: 10``.
CRAWL_DELAY = 10.0

#: Number of simultaneous requests.  The acervo is a small server; the
#: default is deliberately modest so as not to overload it.
WORKERS = 4


def _cache_path(url: str) -> str:
    """Path of the cache file of a URL."""
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{digest}.html")


def is_cached(url: str) -> bool:
    """True when the page is already in the local cache."""
    return os.path.exists(_cache_path(url))


#: Per-thread mark of whether the last :func:`get` went to the network.  The
#: workers use it to apply the crawl delay only to real requests: replaying a
#: cached harvest must not wait ten seconds per page.
_fetch_state = threading.local()


def get(url: str, timeout: int = 60, cache: bool = True,
        attempts: int = 3) -> str:
    """Downloads a page and returns the decoded HTML.

    The HTML is cached on disk (``ACERVO_CACHE``): an interrupted harvest
    resumes without repeating the requests already made.  A transient
    network error is retried a few times with a growing pause; a 4xx answer
    is not retried.
    """
    path = _cache_path(url)
    if cache and os.path.exists(path):
        _fetch_state.downloaded = False
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    _fetch_state.downloaded = True
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as error:
            if error.code < 500:
                raise
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)

    if cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as handle:
            handle.write(body)
        os.replace(temporary, path)
    return body


def _text(fragment: str) -> str:
    """Plain text of an HTML fragment, with the whitespace normalised."""
    without_tags = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def _lines(fragment: str) -> str:
    """Plain text preserving the line breaks.

    The "Fonte de pesquisa" field lists the references one per line; without
    preserving the breaks the list would become a single block.
    """
    without_tags = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(without_tags)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


# ---------------------------------------------------------------------------
# works
# ---------------------------------------------------------------------------

def parse_work(work_id: str, page: str | None = None) -> dict:
    """Transcribes the record of a work.

    Returns the title, the discriminating fields (genre, metre), the
    composers (with the id of their person card) and the list of scores,
    each with its type, the identifier of the PDF, the details (copy, date,
    arrangement, instrumentation, lyrics) and the restriction notices.
    """
    if page is None:
        page = get(WORK_URL.format(work_id))

    record: dict = {
        "id": work_id,
        "url": WORK_URL.format(work_id),
        "title": None,
        "fields": {},
        "composers": [],
        "scores": [],
    }

    heading = re.search(r'<h2 class="color">(.*?)</h2>', page, re.S)
    if heading:
        record["title"] = _text(heading.group(1))

    for match in re.finditer(
        r"<h3>(.*?)</h3>(.*?)(?=<h3>|</div>\s*</div>\s*<div class=\"content_inside_secundary\">)",
        page,
        re.S,
    ):
        label = _text(match.group(1))
        values = [_text(v) for v in re.findall(r"<span[^>]*>(.*?)</span>", match.group(2), re.S)]
        values = [v for v in values if v]
        if values:
            record["fields"].setdefault(label, []).extend(values)
    record["fields"].pop("Dica de uso", None)

    record["composers"] = [
        {"card": card, "name": name.strip()}
        for card, name in re.findall(r'/cards/view/(\d+)">\s*([^<]*?)\s*<', page)
    ]

    starts = [m.start() for m in re.finditer(r'<li class="block_scores_in_works', page)]
    blocks = [
        page[start:(starts[i + 1] if i + 1 < len(starts) else len(page))]
        for i, start in enumerate(starts)
    ]

    for index, block in enumerate(blocks):
        score: dict = {"index": index, "type": None, "pdf": None, "details": {},
                       "editorada": False, "restriction": None}
        kind = re.search(r'<span class="title">(.*?)</span>', block, re.S)
        if kind:
            score["type"] = _text(kind.group(1))
        pdf = re.search(r'/files/uploads/scores/([^"]+)\.pdf', block)
        if pdf:
            score["pdf"] = pdf.group(1)
        for detail in re.finditer(r"(?s)<h5>(.*?)</h5>\s*<ul>(.*?)</ul>", block):
            label = _text(detail.group(1))
            values = [_text(v) for v in re.findall(r"(?s)<li>(.*?)</li>", detail.group(2))]
            values = [v for v in values if v]
            if values:
                score["details"].setdefault(label, []).extend(values)
        for key in [k for k in list(score["details"]) if k.lower().startswith("instrumenta")]:
            score["details"]["Instrumentação"] = score["details"].pop(key)
        score["editorada"] = "Editorada" in block
        notice = re.search(r'(?s)<p class="aviso">(.*?)</p>', block)
        if notice:
            score["restriction"] = _text(notice.group(1))
        record["scores"].append(score)

    return record


# ---------------------------------------------------------------------------
# persons
# ---------------------------------------------------------------------------

def parse_card(card_id: str, page: str | None = None) -> dict:
    """Transcribes the record of a person.

    Returns the inverted name, the activities, the biography, the dates of
    birth and death, the place of birth, the research sources and the number
    of works.
    """
    if page is None:
        page = get(CARD_URL.format(card_id))

    start = page.find("content_inside_primary")
    segment = page[start:start + 12000] if start >= 0 else page

    record: dict = {
        "id": card_id,
        "url": CARD_URL.format(card_id),
        "encyclopedia": None,
        "name": None,
        "inverted": None,
        "roles": [],
        "bio": "",
        "nworks": None,
    }

    def grab(pattern: str, group: int = 1):
        match = re.search(pattern, segment, re.S)
        return _text(match.group(group)) if match else None

    record["encyclopedia"] = grab(r'<p class="encyclopedia">(.*?)</p>')
    record["name"] = grab(r'<h2 class="font-special-bold">(.*?)</h2>')
    record["inverted"] = grab(r"<h5>(.*?)</h5>")

    activities = re.search(r'(?s)<ul class="list_activities">(.*?)</ul>', segment)
    if activities:
        record["roles"] = [
            _text(item).lstrip("∙ ").strip()
            for item in re.findall(r"(?s)<li>(.*?)</li>", activities.group(1))
        ]

    biography = re.search(r'(?s)<div class="content_txt">(.*?)</div>', segment)
    if biography:
        record["bio"] = biography.group(1).strip()
        record["bio_text"] = _text(biography.group(1))

    for label, key in (
        ("Data detalhada de nascimento", "birth"),
        ("Data detalhada de falecimento", "death"),
        ("Natural", "birth_place"),
        ("Fonte de pesquisa", "sources"),
    ):
        pattern = r"(?s)<h3>" + label + r"</h3>\s*<span>(.*?)</span>"
        match = re.search(pattern, segment, re.S)
        if not match:
            continue
        if key == "sources":
            record[key] = _lines(match.group(1))
        else:
            record[key] = _text(match.group(1))

    works = re.search(r'/works\?card_id=\d+"[^>]*>(\d+)\s+Obras', segment)
    if works:
        record["nworks"] = int(works.group(1))

    return record


# ---------------------------------------------------------------------------
# listings
# ---------------------------------------------------------------------------

def _total_pages(page: str) -> int:
    """How many pages the listing has, from the link to the last page."""
    numbers = [int(n) for n in re.findall(r'page:(\d+)', page)]
    return max(numbers) if numbers else 1


def _ids_in_listing(page: str, pattern: str) -> list[str]:
    """Ids of the entities linked in a listing page."""
    return sorted(set(re.findall(pattern, page)), key=int)


def _work_letters() -> Iterator[str]:
    for code in range(ord("A"), ord("Z") + 1):
        yield chr(code)


def _parallel_pages(urls: list[str], workers: int, delay: float) -> Iterator[str]:
    """Downloads the listing pages in parallel, with the interval between them.

    Each thread waits ``delay`` seconds between its requests; the total
    stays around ``workers / delay`` requests per second.  Pages that are
    already cached are replayed without any pause.
    """
    def worker(url: str) -> str:
        page = get(url)
        if getattr(_fetch_state, "downloaded", True):
            time.sleep(delay)
        return page

    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(worker, urls)


def iter_work_ids(letter: str | None = None, workers: int = WORKERS,
                  delay: float = CRAWL_DELAY) -> Iterator[str]:
    """Walks the alphabetical listing and returns the work ids.

    The listing of the acervo shows 15 works per page; the pagination is
    ``/Works/index/page:N?letra=X`` and the number of pages is in the link
    to the last page.

    With ``letter=None`` it walks every letter from ``A`` to ``Z``.
    """
    letters = [letter] if letter else list(_work_letters())
    for current in letters:
        base = f"{ACERVO}/Works/index?letra={urllib.parse.quote(current)}"
        first = get(base)
        seen: set[str] = set()
        for work_id in _ids_in_listing(first, r"/works/view/(\d+)"):
            seen.add(work_id)
            yield work_id
        total = _total_pages(first)
        urls = [
            f"{ACERVO}/Works/index/page:{number}?letra={urllib.parse.quote(current)}"
            for number in range(2, total + 1)
        ]
        for page in _parallel_pages(urls, workers, delay):
            new_ids = [i for i in _ids_in_listing(page, r"/works/view/(\d+)") if i not in seen]
            seen.update(new_ids)
            yield from new_ids


def iter_card_ids(workers: int = WORKERS, delay: float = CRAWL_DELAY) -> Iterator[str]:
    """Walks the person listing and returns the card ids.

    The full listing is at ``/Cards/index?name=`` (the empty search), with
    15 cards per page; the pagination is
    ``/Cards/index/page:N/sort:Card.artistic_name/direction:ASC?name=``.
    """
    suffix = "sort:Card.artistic_name/direction:ASC?name="
    first = get(f"{ACERVO}/Cards/index?name=")
    seen: set[str] = set()
    for card_id in _ids_in_listing(first, r"/cards/view/(\d+)"):
        seen.add(card_id)
        yield card_id
    total = _total_pages(first)
    urls = [f"{ACERVO}/Cards/index/page:{number}/{suffix}" for number in range(2, total + 1)]
    for page in _parallel_pages(urls, workers, delay):
        new_ids = [i for i in _ids_in_listing(page, r"/cards/view/(\d+)") if i not in seen]
        seen.update(new_ids)
        yield from new_ids


def iter_details(ids: Iterable[str], parser, workers: int = WORKERS,
                 delay: float = CRAWL_DELAY) -> Iterator[dict]:
    """Harvests the given records, with a few workers.

    Each thread waits ``delay`` seconds between requests, so that the load
    on the acervo is about ``workers / delay`` requests per second.  A
    failure on one record does not abort the harvest: it is emitted with the
    ``error`` field filled in.
    """
    items = list(ids)

    def worker(item_id: str) -> dict:
        try:
            record = parser(item_id)
        except Exception as error:  # noqa: BLE001 - the harvest must not abort
            record = {"id": item_id, "error": str(error)}
        if getattr(_fetch_state, "downloaded", True):
            time.sleep(delay)
        return record

    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(worker, items)


def iter_works(work_ids: Iterable[str], workers: int = WORKERS,
               delay: float = CRAWL_DELAY) -> Iterator[dict]:
    """Harvests the records of the given works."""
    return iter_details(work_ids, parse_work, workers=workers, delay=delay)


def iter_cards(card_ids: Iterable[str], workers: int = WORKERS,
               delay: float = CRAWL_DELAY) -> Iterator[dict]:
    """Harvests the records of the given persons."""
    return iter_details(card_ids, parse_card, workers=workers, delay=delay)


# ---------------------------------------------------------------------------
# transcription of the free-text field "Cópia"
# ---------------------------------------------------------------------------

COPY_PATTERNS = [
    # (regular expression, fields it fills; the numeric values are capture
    #  groups, the others are literals)
    (re.compile(r"^manuscrita\s*-\s*Obtida do Sr\.\s*(.+?)\s*\((?:arquivo de|acervo de)\s*(.+?)\)\s*$", re.I),
     {"kind": "manuscript", "former_owner": 1, "donor": 2}),
    (re.compile(r"^c[oó]pia\s+de\s+(.+?)(?:\s*\([^)]*\))?\s*$", re.I),
     {"kind": "manuscript", "copyist": 1}),
    (re.compile(r"^manuscrita\s+por\s+(.+)$", re.I),
     {"kind": "manuscript", "copyist": 1}),
    (re.compile(r"^manuscrita\s*$", re.I),
     {"kind": "manuscript"}),
    (re.compile(r"^editorada\s+(.+)$", re.I),
     {"kind": "print", "publisher": 1}),
    (re.compile(r"^editada\s+por\s+(.+)$", re.I),
     {"kind": "print", "editor": 1}),
    (re.compile(r"^editada\s*$", re.I),
     {"kind": "print"}),
]


def parse_copy(text: str) -> dict:
    """Structures the free value of the acervo's ``Cópia`` field.

    The acervo uses the same field for different things: the type of the
    copy (manuscript or print), the copyist, the editor and the
    provenance.  This function separates those elements; whatever fits no
    pattern is preserved in ``note``.
    """
    result: dict = {
        "kind": None,
        "copyist": None,
        "publisher": None,
        "editor": None,
        "former_owner": None,
        "donor": None,
        "note": (text or "").strip(),
    }
    stripped = (text or "").strip()
    if not stripped:
        return result
    for pattern, fields in COPY_PATTERNS:
        match = pattern.match(stripped)
        if not match:
            continue
        for key, value in fields.items():
            if isinstance(value, int):
                result[key] = match.group(value).strip()
            else:
                result[key] = value
        break
    return result


if __name__ == "__main__":  # pragma: no cover - command line utility
    import sys

    kind = sys.argv[1] if len(sys.argv) > 1 else "work"
    wanted = sys.argv[2].split(",")
    parser = parse_work if kind == "work" else parse_card
    print(json.dumps([parser(i) for i in wanted], ensure_ascii=False, indent=1))
