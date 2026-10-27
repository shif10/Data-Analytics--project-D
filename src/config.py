"""
Project D — central configuration.
Edit the values here; the rest of the pipeline imports from this file.
"""

# --- Politeness: OpenAlex asks you to identify yourself (the "polite pool"). ---
# Put a real email here. It only identifies you for rate-limiting; no key needed.
MAILTO = "you@example.com"   # <-- CHANGE THIS

# --- Scope: which countries count as "European" for the co-author filter. ---
# Default = EU-27. To use a broader "Europe", add e.g. "gb", "no", "ch", "is".
EU27 = [
    "be", "bg", "cz", "dk", "de", "ee", "ie", "gr", "es", "fr",
    "hr", "it", "cy", "lv", "lt", "lu", "hu", "mt", "nl", "at",
    "pl", "pt", "ro", "si", "sk", "fi", "se",
]
# Broader Europe (uncomment to use instead):
# EUROPE_BROAD = EU27 + ["gb", "no", "ch", "is", "li"]

SCOPE = EU27                      # <-- switch here if you change scope
SCOPE_NAME = "EU-27"              # for labelling outputs

# --- Time window ---
FROM_DATE = "2020-01-01"          # works published on/after this date

# --- Keyword search (AI in education). Editable — refine with Mabango later. ---
# OpenAlex "search" does a full-text match over title + abstract.
# Chosen query = "B_tight": 24,127 works (EU-27, 2020+, counted 2026-10-24).
# Requires an AI term AND an explicit education term — best recall/precision
# balance vs the loose query (284k, over-capture) and phrase-only (5k, under-capture).
KEYWORDS = (
    '("artificial intelligence" OR "machine learning" OR "ChatGPT" '
    'OR "large language model" OR "generative AI" OR "intelligent tutoring" '
    'OR "learning analytics" OR "adaptive learning") '
    'AND ("education" OR "educational" OR "teaching" OR "classroom" '
    'OR "e-learning" OR "higher education")'
)

# --- API endpoint ---
OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def build_filter() -> str:
    """Compose the OpenAlex `filter` string from the settings above."""
    country_list = "|".join(SCOPE)
    return (
        f"from_publication_date:{FROM_DATE},"
        f"institutions.country_code:{country_list},"
        f"title_and_abstract.search:{KEYWORDS}"
    )
