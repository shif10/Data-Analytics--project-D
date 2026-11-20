# Project D Final Report

## Who Drives AI-in-Education Research in Europe?

### Executive Summary
This project investigates which institutions and venues are leading AI-in-education research across Europe since 2020 and how the analytical picture changes when moving from a broad ALL-candidate pool to a more restrictive Scopus-based STRICT layer. The analysis is built on OpenAlex bibliographic metadata for publications with at least one EU-affiliated author and a provisional venue match against the Scopus source list.

The results indicate rapid growth in the field over time, with Germany, Spain, and Italy among the leading country contributors and a small set of universities and research centres repeatedly appearing at the top of the institutional rankings. The provisional STRICT layer retains approximately half of the candidate records, suggesting that the underlying geographic and institutional pattern remains broadly stable even under a stricter venue screen.

This report should be interpreted as an exploratory, candidate-level analysis rather than a final, fully validated relevance dataset. The evidence is based on search and affiliation filtering, not on manual adjudication of every paper’s substantive relevance.

---

## 1. Research Question and Scope
The project addresses the following question:

Which European institutions and venues drive research on AI in education since 2020, and how does the picture change between a broad ALL-candidate dataset and a stricter Scopus-only STRICT subset?

The study focuses on publications with at least one EU-affiliated author from 2020 onward. The ALL layer captures the broader candidate corpus assembled from OpenAlex. The STRICT layer is narrower and restricted to venues matched to the Scopus source list and covered for the relevant publication year. This approach allows the project to compare a wider search-based field with a more standardised quality-filtered subset.

---

## 2. Data Sources and Methodology
The project draws on three main sources of evidence:

- OpenAlex API for candidate publication records and metadata
- EU affiliation data for filtering publications associated with European institutions
- Scopus source list and year-coverage logic to create a provisional STRICT layer

### Workflow
1. Search OpenAlex using multiple AI-in-education keywords.
2. Deduplicate records by OpenAlex paper ID.
3. Filter to publications with at least one EU-affiliated author.
4. Create the broader ALL candidate dataset.
5. Match publication venues to Scopus by ISSN/eISSN and publication-year coverage.
6. Build the provisional STRICT dataset.
7. Derive country and institution tables for descriptive analysis.

### Dataset Totals
- ALL candidate papers: 7,594
- Provisional STRICT papers: 3,668
- STRICT retention rate: 48.3%

---

## 3. Descriptive Results

### 3.1 Temporal Trend
The yearly count of publications rises steadily over the period 2020–2026.

| Year | ALL Candidates | STRICT Provisional |
|---|---:|---:|
| 2020 | 329 | 139 |
| 2021 | 369 | 207 |
| 2022 | 420 | 236 |
| 2023 | 725 | 365 |
| 2024 | 1308 | 633 |
| 2025 | 2062 | 992 |
| 2026 | 2381 | 1096 |

The trend is consistent in both layers, with a sharp expansion after 2022. It is important to note that 2026 remains incomplete and should be treated with caution when making direct comparisons with full years.

### 3.2 Leading Countries
The strongest country contributions in the ALL candidate layer are shown below. These counts use full counting, meaning that one paper can contribute to multiple countries if multiple EU-affiliated authors are involved.

| Country | Paper Count |
|---|---:|
| Germany | 1382 |
| Spain | 1137 |
| Italy | 908 |
| France | 560 |
| Greece | 481 |
| Netherlands | 473 |
| Finland | 418 |
| Sweden | 405 |
| Portugal | 365 |
| Romania | 342 |

Germany and Spain dominate the candidate dataset, with Italy and France also showing sustained activity. This pattern suggests an important centre of gravity in central and southern Europe, with strong participation also from the Nordics and the Netherlands.

### 3.3 Leading Institutions
The institution-level ranking reflects the concentration of output in a small number of research-intensive universities and research centres.

| Institution | Country | Paper Count |
|---|---|---:|
| University of Eastern Finland | Finland | 96 |
| Centre National de la Recherche Scientifique | France | 93 |
| University of Bonn | Germany | 86 |
| Leibniz University Hannover | Germany | 80 |
| Technical University of Munich | Germany | 78 |
| University of Oulu | Finland | 74 |
| Ludwig-Maximilians-Universität München | Germany | 71 |
| University College Dublin | Ireland | 67 |
| Universidad de Salamanca | Spain | 66 |
| Bucharest University of Economic Studies | Romania | 64 |

This ranking indicates that output is highly concentrated among a relatively small set of high-capacity institutions, many of which are located in Germany, Finland, France, and Spain.

### 3.4 Leading Venues in the STRICT Layer
The STRICT layer is not dominated by a single education journal. Instead, it includes a mix of education-focused venues, conference proceedings, and broader technical outlets.

| Venue | Count |
|---|---:|
| Communications in Computer and Information Science | 155 |
| Lecture Notes in Networks and Systems | 136 |
| Education Sciences | 84 |
| Frontiers in Education | 75 |
| Applied Sciences | 68 |
| IEEE Access | 48 |
| Sustainability | 47 |
| Computers and Education: Artificial Intelligence | 45 |
| Alzheimer’s & Dementia | 43 |
| Scientific Reports | 40 |

This distribution shows that AI-in-education research is not confined to one narrow venue ecosystem. It spans education, computer science, applied technology, and interdisciplinary publication venues.

---

## 4. Interpretation of Findings
The results show a clear pattern of increasing research output in AI in education across Europe since 2020. The strongest country- and institution-level concentrations point to Germany, Spain, Italy, France, and Finland as prominent contributors to the field. The rise in publication counts is visible in both the ALL and STRICT layers, suggesting that the growth trend is not an artefact of one particular venue set.

The provisional STRICT layer removes around half of the candidate records, which indicates that stricter venue filtering materially changes the size and composition of the visible dataset. However, it does not erase the broader geographic and institutional pattern: the general concentration of activity remains evident even after filtering to Scopus-matched venues. This suggests that the field has a core set of highly visible European institutions and venues, even though the full candidate pool is wider and more heterogeneous.

The project therefore provides a strong descriptive window into the field’s structure, but it should be understood as a candidate-level and provisional analysis rather than a definitive statement about final research relevance.

---

## 5. Limitations and Caveats
Several limitations are important for interpreting the results responsibly:

- Candidate papers are not manually validated as relevant to AI in education.
- The keyword screen is preliminary and may produce both false positives and false negatives.
- The STRICT layer is provisional and depends on the current Scopus match and publication-year coverage logic.
- 2026 is incomplete, so it should not be treated as a full-year comparison.
- Country counts overlap because papers with multiple EU-affiliated authors can contribute to more than one country.
- One STRICT record has no title, which is documented and should not be fabricated or silently removed without a project-wide rule.

These limitations are central to the interpretation and should be clearly stated in any final presentation or report.

---

## 6. Conclusion
This project provides a credible preliminary map of AI-in-education research in Europe. It demonstrates substantial growth in output from 2020 onward, a concentrated pattern of institutional activity around a relatively small number of European universities and research centres, and a substantive but incomplete overlap between the broad candidate pool and the stricter Scopus-based subset.

Overall, the findings support the conclusion that AI-in-education research is increasingly important in Europe, with a clear core of high-output countries and institutions. At the same time, the dataset remains candidate-level and provisional, so the results should be interpreted as exploratory and descriptive rather than as a final validated research assessment.

---

## 7. Appendix: Headline Numbers
- Total ALL candidate papers: 7,594
- Total provisional STRICT papers: 3,668
- STRICT retention rate: 48.3%
- Top country: Germany (1,382)
- Top institution: University of Eastern Finland (96)
- Most frequent STRICT venue: Communications in Computer and Information Science (155)
