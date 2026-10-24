# Project D — Master Checklist

**Who Drives AI-in-Education Research in Europe?**
Data Analytics · MDE-CO-02 · Fall 2026

**Research question:** Which European institutions and venues drive research on AI in education since 2020, and do they form one collaboration community or several?

Legend: `[ ]` to do · `[~]` in progress · `[x]` done · **(Owner)**

---

## 0. Admin & setup (Week 1)

- [x] Team registered in the Teams sign-up table (names + Project D) — **deadline was 20 Oct**
- [ ] Confirm everyone is registered with Dr. Snigireva
- [x] Questions for the 20 Oct Q&A sent in advance (by 17 Oct)
- [x] Repo created with `data/`, `notebooks/`, `src/`, `docs/` folders **(Shifa)**
- [x] README with "re-run from scratch" instructions **(Shifa)**
- [x] `requirements.txt` / environment pinned **(Shifa)**
- [x] `.gitignore` (ignore large raw pulls, keep committed external files) **(Shifa)**
- [ ] Everyone reads OpenAlex field docs and writes 10 fields in their own words **(all)**
- [ ] Research question fixed to one sentence **(all)**

---

## 1. Problem definition

- [ ] One-sentence research question agreed and written in README
- [ ] Four RQs restated and assigned to owners
- [ ] Decide default scope: **EU-27** vs **broader Europe** (incl. UK/NO/CH) — document the choice

---

## 2. Data collection — OpenAlex (Week 1 → 2) **(Shifa)**

- [ ] One working OpenAlex API call returns results (polite pool: add `mailto`)
- [ ] Get the **count** for the filter *before* building the pipeline
  - [ ] `from_publication_date` = 2020-01-01 onward
  - [ ] at least one EU-affiliated co-author
  - [ ] AI-in-education keyword / concept filter
- [ ] Draft the keyword query (editable config) **(Shifa + Mabango)**
- [ ] Decide EU country code list (affiliation filter)
- [ ] Paginated pull implemented (cursor paging, rate-limit friendly)
- [ ] Raw pull saved to `data/raw/` with pull date recorded
- [ ] Record: total works, date of pull, exact query string

## 2b. Data collection — external lists (fetch by hand, once)

- [ ] SCImago SJR file downloaded **by hand**, committed to `data/external/`, **date recorded** **(Shifa)**
- [ ] Scopus source list downloaded **by hand**, committed to `data/external/`, **date recorded** **(Shifa)**
- [ ] Note the exact source URL + download date in the data dictionary

---

## 3. Understanding the data

- [ ] Data dictionary written: every field used, in plain words **(Shifa)**
- [ ] Document what OpenAlex gives (works, authorships, institutions, ISSN, concepts/topics)
- [ ] Document ISSN format differences between OpenAlex, SCImago, Scopus (for the join)
- [ ] Note known gaps (incomplete affiliations, missing country)

---

## 4. Data preparation (Week 2) **(Shifa)** — *graded 15%*

- [ ] Cleaning: dedupe works, normalise institution/country names
- [ ] Handle missing country/affiliation data (decide + document rule)
- [ ] Extract per-work: year, authors, institutions, countries, venue, ISSN, concepts
- [ ] Join SCImago SJR on ISSN
- [ ] Join Scopus source list on ISSN
- [ ] Build **ALL layer** (everything from OpenAlex)
- [ ] Build **STRICT layer** (Scopus-listed sources only)
- [ ] Save both to `data/processed/`
- [ ] Pipeline re-runs from scratch end-to-end (verify on a clean checkout)
- [ ] Quantify: how many works lost country? how many matched Scopus?

---

## 5. Exploratory / Descriptive analysis **(Dev)** — *RQ1, RQ2*

- [ ] Top institutions (ALL and STRICT)
- [ ] Top countries
- [ ] Top venues / journals
- [ ] Trend over time 2020 → now (works per year)
- [ ] **ALL vs STRICT comparison** — does the picture change? (RQ2)
- [ ] Descriptive tables + figures saved
- [ ] Start early on what the numbers *mean*, not just the counts

---

## 6. Collaboration networks **(Keerthana)** — *part of RQ3*

- [ ] Co-authorship network built
- [ ] Institution–institution collaboration network built
- [ ] Bibliometric maps / visualisations
- [ ] Community detection (e.g. Louvain / Leiden)
- [ ] Centrality measures (degree, betweenness, eigenvector)
- [ ] Identify: one community or several? (the core question)

---

## 7. Clustering & interpretation **(John)** — *part of RQ3, 30% interpretation*

- [ ] Topic clustering on keywords / concepts
- [ ] Compare clusters against a **"just country" baseline**
- [ ] Argue the choice of clustering method (why this one)
- [ ] Evaluate the clustering (metric vs baseline)
- [ ] Interpret what the clusters *mean*
- [ ] Compare network communities vs topic clusters (with Keerthana)

---

## 8. Search validation & limitations **(Mabango)** — *RQ4, 20%*

- [ ] Design keyword query with Shifa
- [ ] Hand-check a sample of results → measure **over-capture** (false hits)
- [ ] Hand-check for **under-capture** (missed relevant works)
- [ ] Quantify missing affiliations / lost countries
- [ ] Write the limitations section: what's missing, who's excluded, what would overturn the conclusion

---

## 9. Model evaluation

- [ ] Clustering beats / compared against the country baseline
- [ ] Results checked on held-out or alternative view where applicable
- [ ] Robustness: does ALL vs STRICT change the conclusion?

---

## 10. Interpretation **(John, Dev)** — *graded 30%*

- [ ] Answer RQ1: who dominates, and has it shifted since 2020?
- [ ] Answer RQ2: how much does ALL vs STRICT change the picture?
- [ ] Answer RQ3: one collaboration community or several?
- [ ] Answer RQ4: what does the search miss?
- [ ] Each result explained ("what it means", not a restatement of numbers)

---

## 11. Limitations **(Mabango)** — *graded 20%*

- [ ] OpenAlex affiliation incompleteness quantified
- [ ] Keyword over/under-capture quantified
- [ ] External-list coverage caveats (ISSN match rate)
- [ ] "What would change the conclusion" paragraph

---

## 12. Communication — report & slides — *graded 15%*

- [ ] Written report: descriptions, tables, figures, code (notebook or appendix) **(Mabango edits/proofreads)**
- [ ] Presentation slides (10 min + 5 min Q&A) **(Dev)**
  - [ ] Slide 1: who you are + **who did what**
  - [ ] the project · approach · results & conclusions · demo · what next
- [ ] Report intelligible to a non-technical reader
- [ ] Method + Interpretation sections written together **(Keerthana + John)**

---

## 13. Reproducibility & AI-use log **(Shifa)** — *part of 15%*

- [ ] README re-run-from-scratch verified on a clean clone
- [ ] Data dictionary complete
- [ ] External-file download dates recorded
- [ ] **AI-use log**: prompts, model, configuration, cost/effort **(Shifa)**
- [ ] Final reproducibility check **(Shifa)**

---

## 14. Submission (Week 4)

- [ ] Final report done
- [ ] Slides done + rehearsed
- [ ] **Submit at least 2 days before the presentation day**

---

## Watch-outs (from the brief)

- Half the marks (50%) are on **interpretation + limitations** — start thinking about meaning early, not at the end.
- OpenAlex affiliation data is incomplete — some works lose their country entirely.
- Keyword search over- AND under-captures — measure both by hand.
- SCImago & Scopus block automated download — fetch by hand once, commit, record the date.
