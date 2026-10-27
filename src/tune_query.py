"""
Phase 1 helper — compare candidate keyword queries by their OpenAlex counts.

Run:  python src/tune_query.py

It does NOT download works — only counts — so it's fast and cheap.
Use the output to choose a query that is neither huge (over-capture)
nor tiny (under-capture), then paste the winner into src/config.py.
"""

import sys
import requests

sys.path.insert(0, "src")
import config

# Candidate queries. "search" matches over title + abstract.
# The goal: capture "AI *in education*", not all AI and not all education.
CANDIDATES = {
    # A) Current (loose) query — kept for comparison.
    "A_loose": (
        '("artificial intelligence" OR "machine learning" OR "deep learning" '
        'OR "ChatGPT" OR "large language model" OR "intelligent tutoring" '
        'OR "learning analytics" OR "adaptive learning") '
        'AND (education OR learning OR teaching OR student OR classroom '
        'OR school OR university)'
    ),

    # B) Tighter — AI terms AND explicit EDUCATION terms (drops bare "learning").
    "B_tight": (
        '("artificial intelligence" OR "machine learning" OR "ChatGPT" '
        'OR "large language model" OR "generative AI" OR "intelligent tutoring" '
        'OR "learning analytics" OR "adaptive learning") '
        'AND ("education" OR "educational" OR "teaching" OR "classroom" '
        'OR "e-learning" OR "higher education" OR "students\' learning")'
    ),

    # C) Tightest — specific AI-in-education phrases only (high precision).
    "C_phrases": (
        '"artificial intelligence in education" OR "AI in education" '
        'OR "AIED" OR "intelligent tutoring system" OR "learning analytics" '
        'OR "adaptive learning system" OR "educational data mining" '
        'OR "AI-powered learning" OR "ChatGPT in education" '
        'OR "generative AI in education"'
    ),
}


def count_for(search_query: str) -> int:
    filt = (
        f"from_publication_date:{config.FROM_DATE},"
        f"institutions.country_code:{'|'.join(config.SCOPE)},"
        f"title_and_abstract.search:{search_query}"
    )
    params = {"filter": filt, "per-page": 1, "mailto": config.MAILTO}
    r = requests.get(config.OPENALEX_WORKS_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json()["meta"]["count"]


def main() -> None:
    print(f"Scope: {config.SCOPE_NAME}, from {config.FROM_DATE}")
    print("=" * 55)
    for name, q in CANDIDATES.items():
        try:
            n = count_for(q)
            print(f"{name:12s} -> {n:>10,} works")
        except Exception as e:
            print(f"{name:12s} -> ERROR: {e}")
    print("=" * 55)
    print("Pick the query that is focused (roughly a few thousand to")
    print("a few tens of thousands) and paste it into src/config.py KEYWORDS.")


if __name__ == "__main__":
    main()
