"""
Phase 1, Step 1.2 — Get the COUNT for our filter, before building any pipeline.

Run from the repo root (with your venv active and `requests` installed):

    python src/openalex_count.py

It prints:
  - the total number of works matching the filter
  - the works-per-year breakdown (2020 -> now)
It writes nothing to disk and pulls no records — it only asks "how many?".
"""

import sys
import requests

# allow running as `python src/openalex_count.py` from the repo root
sys.path.insert(0, "src")
import config


def get_total_count() -> int:
    """Ask OpenAlex how many works match our filter (per-page=1 is enough)."""
    params = {
        "filter": config.build_filter(),
        "per-page": 1,
        "mailto": config.MAILTO,
    }
    r = requests.get(config.OPENALEX_WORKS_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json()["meta"]["count"]


def get_counts_by_year() -> list[dict]:
    """Use OpenAlex group_by to get works-per-year without downloading works."""
    params = {
        "filter": config.build_filter(),
        "group_by": "publication_year",
        "mailto": config.MAILTO,
    }
    r = requests.get(config.OPENALEX_WORKS_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json()["group_by"]


def main() -> None:
    print(f"Scope:    {config.SCOPE_NAME}  ({len(config.SCOPE)} countries)")
    print(f"From:     {config.FROM_DATE}")
    print("Filter:   (title+abstract search for AI-in-education keywords)")
    print("-" * 50)

    total = get_total_count()
    print(f"TOTAL matching works: {total:,}")
    print("-" * 50)

    print("Works per year:")
    rows = get_counts_by_year()
    # group_by returns {"key": "2020", "count": N}; sort by year
    for row in sorted(rows, key=lambda x: x["key"]):
        print(f"  {row['key']}: {row['count']:,}")

    print("-" * 50)
    print("Write this total + today's date into docs/data_dictionary.md.")
    print("If the number looks sane (not millions, not zero), proceed to the pull.")


if __name__ == "__main__":
    main()
