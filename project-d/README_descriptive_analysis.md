# Project D — Descriptive Analysis README

This file summarizes the descriptive analysis for the first two research questions.

## Scope
The project examines which European institutions and venues drive AI-in-education research from 2020 onward, with a comparison between an ALL-layer candidate set and a provisional STRICT-layer set restricted to Scopus-listed venues.

## Relevant files
- `project-d/RQ1RQ2.py` — main analysis script for RQ1 and RQ2
- `project-d/data/processed/` — output tables and figures for counts and comparisons
- `project-d/Project D RQ1 and RQ2 Descriptive Analysis.pdf` — presentation-quality summary
- `project-d/Project D RQ1 and RQ2 Descriptive Analysis.docx` — editable manuscript version

## What the analysis covers
1. Top institutions by publication counts
2. Top countries by candidate-paper counts
3. Top venues by publication counts
4. Trends over time from 2020 to the latest available year
5. Comparison between ALL and STRICT definitions

## Important limitations
- The ALL layer is based on OpenAlex search results and EU-affiliated candidate papers, not manually confirmed relevance.
- The STRICT layer is provisional and depends on venue matching against the Scopus source list.
- The 2026 data point is partial and should be interpreted cautiously.
- Country counts can overlap because a paper may have authors from multiple countries.

## Recommended interpretation
Use the descriptive results as a structured summary of the candidate dataset rather than as a final validated relevance judgment. The analyses should be read alongside the main preparation notes in `project-d/README_data_preparation.md` and the project limitations documented there.
