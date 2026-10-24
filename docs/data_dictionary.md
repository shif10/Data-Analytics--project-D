# Data Dictionary

Plain-language description of every field used, plus download provenance for the
manually-fetched external lists. Fill in as the pipeline develops.

---

## External file provenance (record on download)

| File | Source URL | Downloaded on | Downloaded by | Notes |
|---|---|---|---|---|
| SCImago SJR list | _TODO_ | _YYYY-MM-DD_ | Shifa | Blocks automated download — fetched by hand |
| Scopus source list | _TODO_ | _YYYY-MM-DD_ | Shifa | Blocks automated download — fetched by hand |

---

## OpenAlex fields used

> Each team member should write ~10 fields in their own words (Week-1 task).

| Field (OpenAlex path) | Plain-language meaning | Used for |
|---|---|---|
| `id` | Unique OpenAlex work ID | deduplication, keys |
| `publication_year` | Year the work was published | trends, 2020+ filter |
| `authorships[].author` | Author identity | co-authorship network |
| `authorships[].institutions` | Author's institution(s) | institution network, affiliations |
| `authorships[].countries` | Country of affiliation | EU filter, country baseline |
| `primary_location.source.issn` | ISSN(s) of the venue | join to SCImago / Scopus |
| `primary_location.source.display_name` | Venue / journal name | top venues |
| `concepts` / `topics` | Subject tags | topic clustering |
| `title` | Work title | keyword hand-check |
| _..._ | _..._ | _..._ |

---

## Derived fields (built by the pipeline)

| Field | Definition |
|---|---|
| `layer` | `ALL` or `STRICT` (STRICT = source in Scopus list) |
| `has_eu_coauthor` | True if ≥1 authorship affiliation is in the EU scope list |
| `country_missing` | True if the work lost its country during cleaning |
| _..._ | _..._ |
