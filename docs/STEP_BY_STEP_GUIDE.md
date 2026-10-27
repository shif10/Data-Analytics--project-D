# Project D — Step-by-Step Guide

**Who Drives AI-in-Education Research in Europe?**
Data Analytics · MDE-CO-02 · Fall 2026

**Research question:** Which European institutions and venues drive research on AI in education since 2020, and do they form one collaboration community or several?

This guide takes you from an empty repo to the final submission. Follow it in order.
Each step says **what to do**, **why**, and **how to check it worked**.

---

## PHASE 0 — Set up (Week 1)

### Step 0.1 — Set up your computer
You need, on a machine with internet:
- **Python 3.11** (check: `python --version`)
- **Git** (check: `git --version`)
- A code editor (VS Code is fine) and Jupyter for notebooks

### Step 0.2 — Clone the repo
```bash
git clone https://github.com/shif10/Data-Analytics--project-D.git
cd Data-Analytics--project-D
```

### Step 0.3 — Create the folder structure
```
Data-Analytics--project-D/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/          # OpenAlex pulls (not committed — too big)
│   ├── external/     # SCImago + Scopus files (committed by hand)
│   └── processed/    # ALL + STRICT layers (not committed — rebuilt)
├── notebooks/        # Jupyter notebooks
├── src/              # Python pipeline code
└── docs/             # checklist, data dictionary, AI-use log
```

### Step 0.4 — Make a virtual environment and install packages
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install pandas numpy requests tqdm networkx python-louvain scikit-learn matplotlib seaborn jupyter openpyxl pyarrow
pip freeze > requirements.txt
```

### Step 0.5 — Everyone reads the OpenAlex docs
Open https://docs.openalex.org/api-entities/works and each team member writes
**10 fields in their own words** (you need this in the report). Save to `docs/data_dictionary.md`.

### Step 0.6 — Fix the research question to one sentence
Write it at the top of the README. Done above.

**✅ Check Phase 0:** repo cloned, folders exist, packages install, question written.

---

## PHASE 1 — Get the data into your hands (Week 1 → 2)

> The brief is strict: **get the COUNT first, before building any pipeline.**

### Step 1.1 — Make one working OpenAlex call
OpenAlex is free, no key. Be polite: add your email (`mailto`).
Try one call in a notebook:
```python
import requests
url = "https://api.openalex.org/works"
params = {"filter": "publication_year:2024", "per-page": 1, "mailto": "you@example.com"}
r = requests.get(url, params=params)
print(r.json()["meta"]["count"])   # should print a big number
```

### Step 1.2 — Build your filter and GET THE COUNT
Your filter has three parts:
1. **Year ≥ 2020** → `from_publication_date:2020-01-01`
2. **At least one EU-affiliated co-author** → `institutions.country_code:` + EU list
3. **About AI in education** → a keyword search

Example count query (no pipeline yet, just the number):
```python
EU = "be|bg|cz|dk|de|ee|ie|gr|es|fr|hr|it|cy|lv|lt|lu|hu|mt|nl|at|pl|pt|ro|si|sk|fi|se"
params = {
  "filter": f"from_publication_date:2020-01-01,"
            f"institutions.country_code:{EU},"
            f"title_and_abstract.search:artificial intelligence education",
  "per-page": 1,
  "mailto": "you@example.com",
}
r = requests.get("https://api.openalex.org/works", params=params)
print(r.json()["meta"]["count"])   # <-- write this number down
```
**Decision point:** EU-27 only, or broader Europe (add `gb|no|ch|is`)? Document your choice.

### Step 1.3 — Draft the keyword query (Shifa + Mabango)
A starting query (keep it editable in `src/config.py`):
```
("artificial intelligence" OR "machine learning" OR "deep learning"
 OR "ChatGPT" OR "large language model" OR "intelligent tutoring"
 OR "learning analytics" OR "adaptive learning")
AND (education OR learning OR teaching OR student OR classroom OR school OR university)
```
You will refine this with Mabango's hand-check (Phase 7).

### Step 1.4 — Pull the data (paginated)
Only after the count looks sane. Use **cursor paging** (`cursor=*`) to page through all
results, 200 per page, saving raw JSON to `data/raw/`. Record the **pull date**, the
**exact query**, and the **total count**.

### Step 1.5 — Fetch the external lists BY HAND (one time)
SCImago and Scopus block automated download:
1. **SCImago SJR**: https://www.scimagojr.com → download the journal rankings CSV.
2. **Scopus source list**: Elsevier's "Scopus source list" spreadsheet.
3. Save both into `data/external/`.
4. **Record the source URL + download date** in `docs/data_dictionary.md`.

**✅ Check Phase 1:** you have a count, a raw pull in `data/raw/`, and the two external files committed.

> ⚠️ If you cannot load the data in Week 1, change project. Do not discover this in Week 3.

---

## PHASE 2 — Understand the data (Week 2)

### Step 2.1 — Read the codebook / field docs
For every field you will use, write what it means in plain words in `docs/data_dictionary.md`:
`id`, `publication_year`, `authorships`, `institutions`, `countries`, `issn`,
`primary_location.source`, `concepts`/`topics`, `title`.

### Step 2.2 — Note the known traps
- OpenAlex affiliation data is incomplete → some works lose their country.
- ISSN formats differ across OpenAlex / SCImago / Scopus → you must normalise before joining.

**✅ Check Phase 2:** data dictionary has ≥10 fields explained; you know how ISSNs will join.

---

## PHASE 3 — Prepare the data (Week 2) — *Shifa · graded 15%*

### Step 3.1 — Flatten each work into a table
From each raw work extract: year, authors, institutions, countries, venue name, ISSN, concepts.

### Step 3.2 — Clean
- Remove duplicate works (by OpenAlex `id`).
- Normalise institution and country names.
- Normalise ISSNs (strip hyphens, uppercase) so joins work.

### Step 3.3 — Handle missing data
Decide and document a rule for works with missing country/affiliation
(e.g. keep but flag `country_missing = True`). **Count how many.**

### Step 3.4 — Join the external lists on ISSN
- Join **SCImago SJR** (adds SJR quartile/rank).
- Join **Scopus source list** (flags whether the venue is Scopus-indexed).

### Step 3.5 — Build the two layers
- **ALL** = everything from OpenAlex.
- **STRICT** = only works whose venue is in the Scopus list.
- Save both to `data/processed/`.

### Step 3.6 — Make it re-runnable
The whole pipeline must run top-to-bottom on a clean clone (`openalex_pull → clean → enrich`).
Test it by deleting `data/processed/` and re-running.

**✅ Check Phase 3:** ALL and STRICT files exist; you can state how many works lost country and how many matched Scopus.

---

## PHASE 4 — Explore / describe (Week 3) — *Dev · RQ1, RQ2*

### Step 4.1 — Top lists
Compute top **institutions**, **countries**, **venues** — for ALL and for STRICT.

### Step 4.2 — Trend over time
Works per year 2020 → now. Plot it.

### Step 4.3 — ALL vs STRICT comparison (RQ2)
Put the two side by side. Does the leaderboard change? By how much? Make tables + figures.

**✅ Check Phase 4:** you can answer "who dominates and has it shifted" with figures to back it.

---

## PHASE 5 — Collaboration networks (Week 3) — *Keerthana · RQ3*

### Step 5.1 — Build networks (networkx)
- **Co-authorship network**: nodes = authors, edge = co-wrote a paper.
- **Institution network**: nodes = institutions, edge = co-authored across institutions.

### Step 5.2 — Analyse
- **Community detection** (Louvain) → how many communities?
- **Centrality** (degree, betweenness, eigenvector) → who/what is central?

### Step 5.3 — Visualise
Bibliometric maps of the networks.

**✅ Check Phase 5:** you can say "one community or several" and show the map.

---

## PHASE 6 — Clustering & interpretation (Week 3) — *John · RQ3, graded 30%*

### Step 6.1 — Topic clustering
Cluster works by their concepts/keywords (e.g. TF-IDF + KMeans, or on concept vectors).

### Step 6.2 — Compare to a "just country" baseline
Does clustering by topic tell you more than simply grouping by country? Show the difference.

### Step 6.3 — Argue and evaluate the method
Say *why* you chose this clustering method and evaluate it (e.g. silhouette score vs baseline).

### Step 6.4 — Interpret
What do the clusters MEAN? (Not "cluster 1 has 40 papers" — what is cluster 1 *about*?)
Compare topic clusters against the network communities (with Keerthana).

**✅ Check Phase 6:** clusters have names/meanings, method is justified, baseline compared.

---

## PHASE 7 — Search validation & limitations (Week 3→4) — *Mabango · RQ4, graded 20%*

### Step 7.1 — Hand-check a sample
Take ~50 random works your query returned. By hand, mark each as truly
"AI in education" or not → measure **over-capture** (false positives).

### Step 7.2 — Check for misses
Find known AI-in-education papers and check whether your query caught them →
measure **under-capture** (false negatives).

### Step 7.3 — Quantify missing affiliations
How many works lost their country? What share of the data is that?

### Step 7.4 — Write the limitations
What the analysis does NOT show, who is missing, and **what would change the conclusion**.

**✅ Check Phase 7:** you have numbers for over/under-capture and missing affiliations.

---

## PHASE 8 — Interpretation (Week 4) — *John, Dev · graded 30%*

Answer each research question in words, backed by your results:
1. Which institutions/venues dominate, and has it shifted since 2020?
2. How much does ALL vs STRICT change the picture?
3. One collaboration community, or several?
4. What does the keyword search miss?

> Do NOT just restate numbers. Say what they mean.

---

## PHASE 9 — Write up & present (Week 4) — *graded 15%*

### Step 9.1 — Report (Mabango edits/proofreads)
Notebook mixing code + text, OR a report with code in an appendix. Include tables + figures.

### Step 9.2 — Slides (Dev) — 10 min + 5 min Q&A
- **Slide 1: who you are + who did what** (required).
- Then: the project · your approach · results & conclusions (+demo) · what you'd do next.

### Step 9.3 — AI-use log (Shifa)
Record prompts, model, configuration, and cost/effort in `docs/ai_use_log.md`.
Declared, thoughtful AI use counts in your favour.

### Step 9.4 — Final reproducibility check (Shifa)
Clone fresh, follow the README, confirm everything re-runs.

### Step 9.5 — Submit
**At least 2 days before your presentation day.**

---

## How your work is graded (keep this in view)

| Component | Weight | Owner |
|---|---|---|
| Data preparation & reproducibility | 15% | Shifa |
| Method choice & execution | 20% | Keerthana, John |
| Interpretation of results | 30% | John, Dev |
| Limitations & what would change the conclusion | 20% | Mabango |
| Communication | 15% | Dev (slides), Mabango (report) |

**Half the marks are interpretation + limitations.** Start thinking about meaning
from Week 2, not at the end.

---

## Git workflow (every time you make a change)

```bash
git checkout -b your-feature-branch      # new branch for your work
# ... make changes ...
git add <files>
git commit -m "clear message of what you did"
git push origin your-feature-branch      # push to GitHub
# then open a Pull Request on GitHub for the team to review
```

Commit small and often. Write messages that say *what changed and why*.
