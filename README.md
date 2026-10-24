# Project D — Who Drives AI-in-Education Research in Europe?

**Data Analytics · MDE-CO-02 · Fall 2026 · Constructor University**

**Research question:** *Which European institutions and venues drive research on AI in education since 2020, and do they form one collaboration community or several?*

---

## Team & roles

| Person | Role | Covers |
|---|---|---|
| **Shifa Kayumbhai Bhari** | Data Processing & Reproducibility | OpenAlex pull, cleaning, ISSN joins, ALL/STRICT layers, repo, README, data dictionary |
| **Dev Charan** | Descriptive Analysis | RQ1, RQ2 — top institutions/countries/venues, trends, ALL vs STRICT |
| **Mabango Nyikuri** | Search Validation & Limitations | RQ4 — keyword query, over/under-capture, missing affiliations, limitations |
| **Panchumarthi Keerthana** | Collaboration Networks | RQ3 — co-authorship/institution networks, community detection, centrality |
| **Magaseng John Manchidi** | Clustering & Interpretation | RQ3 — topic clustering, country baseline, interpretation |

---

## Research questions

1. Which institutions and venues dominate, and has that shifted since 2020?
2. How much does the picture change between the **ALL** layer and the Scopus-only **STRICT** layer?
3. What clusters exist — by topic, by collaboration, or simply by country?
4. What does the keyword search miss, and how would we know?

---

## Data sources

| Source | Access | Notes |
|---|---|---|
| **OpenAlex API** | Free, no key | Works 2020+ with ≥1 EU-affiliated co-author, matching the AI-in-education query. Pulled by the pipeline. |
| **SCImago SJR** | Manual download | Blocks automated download — **fetch by hand once, commit to `data/external/`, record the date** in `docs/data_dictionary.md`. |
| **Scopus source list** | Manual download | Same as above. Used to build the STRICT layer. |

Joins between OpenAlex, SCImago, and Scopus are done on **ISSN**.

### Two layers
- **ALL** — everything retrieved from OpenAlex for the filter.
- **STRICT** — restricted to sources present in the Scopus list.

---

## Repository layout

```
Data-Analytics--project-D/
├── README.md                 # this file
├── requirements.txt          # pinned Python dependencies
├── .gitignore
├── data/
│   ├── raw/                  # OpenAlex pulls (gitignored — re-created by pipeline)
│   ├── external/             # SCImago SJR + Scopus list (committed by hand, with dates)
│   └── processed/            # ALL + STRICT layers (gitignored — build artifacts)
├── notebooks/                # counts, exploration, analysis
├── src/                      # reusable pipeline modules
└── docs/
    ├── CHECKLIST.md          # master task checklist
    ├── data_dictionary.md    # every field in plain words + download dates
    └── ai_use_log.md         # prompts, model, configuration, cost
```

---

## Scope setting

> **Default scope: EU-27.** This is an editable setting. If the team decides to use a
> broader definition of "European" (e.g. including the UK, Norway, Switzerland),
> change the country-code list in the pipeline config and note the decision here.

Current decision: **_(to be confirmed by the team — EU-27 vs broader Europe)_**

---

## How to re-run everything from scratch

> ⚠️ **Network note:** OpenAlex, SCImago, and Scopus are external services.
> Run these steps on a machine with internet access (a laptop or Google Colab).

### 1. Set up the environment
```bash
# clone
git clone https://github.com/shif10/Data-Analytics--project-D.git
cd Data-Analytics--project-D

# create and activate a virtual environment (Python 3.11)
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

### 2. Fetch the external lists by hand (one time)
1. Download the **SCImago SJR** list and the **Scopus source list**.
2. Save them into `data/external/`.
3. Record the exact source URL and download date in `docs/data_dictionary.md`.

### 3. Pull from OpenAlex
```bash
# (once the pipeline scripts land in src/)
# first: get the count for the filter BEFORE pulling everything
python src/openalex_pull.py --count-only

# then: run the full paginated pull
python src/openalex_pull.py
```

### 4. Build the ALL and STRICT layers
```bash
python src/clean.py      # clean + normalise, handle missing country/affiliation
python src/enrich.py     # join SCImago + Scopus on ISSN -> ALL and STRICT layers
```

### 5. Run the analysis notebooks
```bash
jupyter notebook
# open notebooks/ and run top to bottom
```

> The `src/` scripts above are being built incrementally. Until they exist, the
> step that matters first (per the brief) is getting **one working OpenAlex call
> and the count** — see `notebooks/01_openalex_counts.ipynb` when added.

---

## Reproducibility notes
- Large/raw data is **not** committed — it is re-created by the pipeline.
- External lists (SCImago/Scopus) **are** committed, with download dates recorded.
- All AI assistance is logged in `docs/ai_use_log.md` (prompts, model, configuration, cost).

## Status
Early setup. See `docs/CHECKLIST.md` for the full task list and progress.
