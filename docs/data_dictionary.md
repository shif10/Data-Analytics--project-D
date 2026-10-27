# Data Dictionary

Plain-language description of every field used, plus download provenance for the
manually-fetched external lists.

---

## Query decision & counts (Phase 1)

**Decided 2026-10-24.** Compared three candidate keyword queries at the count stage
(no records pulled), scope EU-27, from 2020-01-01:

| Query | Works | Verdict |
|---|---|---|
| A (loose) | 284,033 | Over-captures — bare "learning"/"university" pull in generic AI/CS |
| **B (tight) — CHOSEN** | **24,127** | Needs an AI term AND an explicit education term; best recall/precision |
| C (phrases only) | 5,156 | High precision but under-captures |

**Chosen filter total: 24,127 works.** Works per year:
2020: 968 · 2021: 1,141 · 2022: 1,274 · 2023: 2,291 · 2024: 4,139 · 2025: 6,819 · 2026: 7,495 (partial).

To be hand-validated for over/under-capture by Mabango (RQ4).

---

## External file provenance (fill in when you download)

| File | Source URL | Downloaded on | By | Notes |
|---|---|---|---|---|
| SCImago SJR list | _TODO_ | _YYYY-MM-DD_ | Shifa | Blocks automated download — fetched by hand |
| Scopus source list | _TODO_ | _YYYY-MM-DD_ | Shifa | Blocks automated download — fetched by hand |

---

## OpenAlex fields — 10 fields in our own words (Phase 0, Step 0.5)

> Source: https://docs.openalex.org/api-entities/works
> Each team member should confirm / expand these.

| # | Field (OpenAlex path) | In our own words | We use it for |
|---|---|---|---|
| 1 | `id` | The permanent OpenAlex ID for a single publication (a URL). | De-duplicating works; as the key. |
| 2 | `publication_year` | The year the work came out. | The 2020+ filter and time trends. |
| 3 | `title` | The title of the paper. | Keyword hand-check (Phase 7). |
| 4 | `authorships` | The list of authors on the work, each with their affiliations. | Co-authorship network. |
| 5 | `authorships[].institutions` | The universities/organisations an author belongs to for this work. | Institution network, "who drives it". |
| 6 | `authorships[].countries` | The country code(s) of each author's affiliation. | EU filter and the country baseline. |
| 7 | `primary_location.source` | The venue (journal/conference) the work appeared in. | Top venues. |
| 8 | `primary_location.source.issn` | The ISSN code(s) of that venue. | Joining to SCImago and Scopus. |
| 9 | `concepts` / `topics` | OpenAlex's subject tags describing what the work is about. | Topic clustering (Phase 6). |
| 10 | `cited_by_count` | How many times the work has been cited. | Optional: impact/weighting. |

---

## Derived fields (built by the pipeline in Phase 3)

| Field | Definition |
|---|---|
| `layer` | `ALL` or `STRICT` (STRICT = venue present in the Scopus list). |
| `has_eu_coauthor` | True if ≥1 affiliation is in the EU scope list. |
| `country_missing` | True if the work lost its country during cleaning. |
| `issn_norm` | ISSN with hyphens stripped and upper-cased, for joining. |
