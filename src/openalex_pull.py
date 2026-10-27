"""
Phase 1, Step 1.4 — Pull all matching works from OpenAlex (paginated).

Run from the repo root (venv active, `requests` + `tqdm` installed):

    python src/openalex_pull.py           # full pull
    python src/openalex_pull.py --count   # just print the count and exit

Uses CURSOR paging (the correct way to page >10k results in OpenAlex).
Saves a slimmed-down record per work (only the fields we need) to:

    data/raw/openalex_works.jsonl         # one JSON object per line
    data/raw/pull_metadata.json           # date, query, total, settings

JSONL (one JSON per line) is used so the ~24k works stream to disk safely
and can be re-read without loading everything into memory at once.
"""

import sys
import json
import time
from datetime import date

import requests
from tqdm import tqdm

sys.path.insert(0, "src")
import config

# How long to pause between pages (seconds). OpenAlex is happiest ~1 req/sec.
PAGE_PAUSE = 1.0
# Retry settings for transient errors (429 rate-limit, 401 throttle, 5xx).
MAX_RETRIES = 6
RETRYABLE_STATUS = {401, 429, 500, 502, 503, 504}


def get_with_retry(url: str, params: dict) -> requests.Response:
    """GET with exponential backoff on transient errors (429/401/5xx)."""
    delay = 2.0
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(url, params=params, timeout=90)
        if resp.status_code not in RETRYABLE_STATUS:
            resp.raise_for_status()
            return resp
        # transient: wait and retry
        wait = delay * attempt
        tqdm.write(
            f"  {resp.status_code} from OpenAlex — backing off {wait:.0f}s "
            f"(attempt {attempt}/{MAX_RETRIES})"
        )
        time.sleep(wait)
    # out of retries
    resp.raise_for_status()
    return resp

RAW_PATH = "data/raw/openalex_works.jsonl"
META_PATH = "data/raw/pull_metadata.json"

# Only request the fields we actually use (smaller + faster responses).
SELECT_FIELDS = ",".join([
    "id",
    "title",
    "publication_year",
    "cited_by_count",
    "authorships",            # authors + institutions + countries
    "primary_location",       # venue (source) + ISSN
    "concepts",               # subject tags for clustering
    "topics",
])


def slim(work: dict) -> dict:
    """Keep a compact, analysis-ready record from a full OpenAlex work."""
    # Authorships -> list of {author, institutions, countries}
    authorships = []
    for a in work.get("authorships", []) or []:
        authorships.append({
            "author_id": (a.get("author") or {}).get("id"),
            "author_name": (a.get("author") or {}).get("display_name"),
            "institutions": [
                {"id": inst.get("id"),
                 "name": inst.get("display_name"),
                 "country": inst.get("country_code")}
                for inst in (a.get("institutions") or [])
            ],
            "countries": a.get("countries") or [],
        })

    source = (work.get("primary_location") or {}).get("source") or {}

    return {
        "id": work.get("id"),
        "title": work.get("title"),
        "year": work.get("publication_year"),
        "cited_by_count": work.get("cited_by_count"),
        "venue_name": source.get("display_name"),
        "venue_id": source.get("id"),
        "issn_l": source.get("issn_l"),
        "issn": source.get("issn") or [],
        "authorships": authorships,
        "concepts": [
            {"name": c.get("display_name"), "score": c.get("score")}
            for c in (work.get("concepts") or [])
        ],
        "topics": [t.get("display_name") for t in (work.get("topics") or [])],
    }


def pull() -> None:
    base = {
        "filter": config.build_filter(),
        "per-page": 200,              # max page size
        "select": SELECT_FIELDS,
        "mailto": config.MAILTO,
    }

    # First request: get total + first cursor.
    params = dict(base, cursor="*")
    r = get_with_retry(config.OPENALEX_WORKS_URL, params)
    payload = r.json()
    total = payload["meta"]["count"]

    print(f"Pulling {total:,} works (scope {config.SCOPE_NAME}, from {config.FROM_DATE})")

    written = 0
    with open(RAW_PATH, "w", encoding="utf-8") as fh, \
            tqdm(total=total, unit="work") as bar:
        while True:
            results = payload.get("results", [])
            if not results:
                break
            for work in results:
                fh.write(json.dumps(slim(work), ensure_ascii=False) + "\n")
                written += 1
            bar.update(len(results))

            next_cursor = payload["meta"].get("next_cursor")
            if not next_cursor:
                break

            time.sleep(PAGE_PAUSE)  # be polite — ~1 request/second
            params = dict(base, cursor=next_cursor)
            r = get_with_retry(config.OPENALEX_WORKS_URL, params)
            payload = r.json()

    meta = {
        "pulled_on": str(date.today()),
        "total_reported": total,
        "total_written": written,
        "scope": config.SCOPE_NAME,
        "from_date": config.FROM_DATE,
        "filter": config.build_filter(),
    }
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

    print(f"Done. Wrote {written:,} works to {RAW_PATH}")
    print(f"Metadata saved to {META_PATH}")
    if written != total:
        print(f"NOTE: wrote {written} but API reported {total} — re-run if this gap is large.")


def count_only() -> None:
    params = {"filter": config.build_filter(), "per-page": 1, "mailto": config.MAILTO}
    r = get_with_retry(config.OPENALEX_WORKS_URL, params)
    print(f"{r.json()['meta']['count']:,} works match the filter.")


if __name__ == "__main__":
    if "--count" in sys.argv:
        count_only()
    else:
        pull()
