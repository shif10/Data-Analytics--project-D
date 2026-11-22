# Revision of the clustering part of the submitted report

Applies to `Project_D_Final_Report_Team8` (submitted 17 November 2026):
Summary ("Topics"), Table 3, Section 2.2, Section 5, Section 8, Section 10.
The submitted PDF and DOCX were not changed. This file holds the checks and
paste-ready replacement text.

Replacement text uses the corrected analysis in
`src/cluster_analysis_final.py` (outputs in `data/processed/clustering/final/`).

## 1. Fact-check of the submitted clustering claims

Checked against `data/processed/clustering/strict_only_sensitivity/` and a re-run.

| Claim in report | Result of check | Status |
|---|---|---|
| 2,972 papers; cluster sizes 954 / 832 / 657 / 319 / 210 | Match `cluster_assignments.csv` | Correct |
| Silhouette 0.0126 (k=5) | 0.0127 on all papers, 0.0126 on the 2,000-paper sample | Correct |
| Generative-AI theme: 1, 34, 132, 316, 466 papers (2020, 2023 to 2026) | Match | Correct |
| NMI topic vs country 0.03 (shuffled about 0.01) | 0.026 (shuffled 0.009) | Correct |
| ARI 0.53 "structure partly survives the cleaning step" | The 0.53 compares k=8 with k=5, so it mixes a change in k with the removal of papers | **Misleading** |
| "Alzheimer's & Dementia (26) and European Heart Journal (13)" as leading venues of cluster 2 | These are counts for all 2,972 papers. Inside cluster 2 they are **24 and 11** | **Wrong** |
| NMI community vs country 0.47 | 0.40 from `institution_nodes.csv` (1,502 non-isolated institutions). 0.47 may come from another sample, such as the 7,594 candidates | **Not reproduced** |
| "In each of the 8 largest communities all five themes appear; clinical share 10% to 36%" | Needs paper-level community data not stored in the outputs | Not re-checked |
| k "chosen by cosine silhouette" | Scores for k=4 to 10 differ by 0.004 and the first run's k=8 beat k=7 by 0.0003. Re-running with 5 seeds gives seed agreement (ARI) of 0.57 for k=5 and 0.46 for k=8 | **Weak basis for k** |
| "Topics beat country labels, but only just" (0.013 vs -0.012) | Compares 5 topic groups with about 27 country groups, and country is on a 2,000-paper sample. Silhouette depends on the number of groups | **Not a fair comparison** |

## 2. What is weak in the submitted clustering, and the fix

| Weakness | Fix in the revised analysis |
|---|---|
| k picked by silhouette, differences within noise | k picked by reproducibility across 10 seeds. Only k=4 is stable (ARI 0.80) |
| Cluster 2 (319 papers) is clinical and stays in the data | Health-domain rule and no-education rule remove 653 more papers (2,319 remain) |
| ARI mixes k and sample changes | Cleaning effect measured at fixed k (ARI 0.50) against seed noise (0.80) |
| Topic vs country compared with silhouette | NMI, Cramer's V and a 1,000-shuffle permutation test |
| 287 papers without abstract not examined | Checked: 17% of cluster 1, and the result depends on them (ARI 0.37) |
| Cluster labels only from top terms | 20 random papers per cluster read; off-topic share estimated |

## 3. Replacement text

### 3.1 Summary, "Topics" paragraph

> **Topics.** Topic clustering of 2,319 cleaned STRICT papers gives four broad,
> overlapping themes (silhouette 0.012). Four is the only number of groups that
> repeats when the clustering is run with different random seeds. Topics barely
> follow country or collaboration community. Our answer to RQ3 is one connected
> field with several largely national collaboration communities.

### 3.2 Table 3, last row

| Step | Papers | Description |
|---|---:|---|
| Clustering sample | 2,319 | 123 out-of-scope papers removed after manual review, then 381 health-domain papers and 272 papers with no education context removed by two keyword rules |

### 3.3 Section 2.2, "RQ3 (topics)" paragraph

> **RQ3 (topics):** TF-IDF features (1 to 2 word phrases, English stop words, up
> to 12,000 features) and KMeans on titles and abstracts, with k from 4 to 10.
> Each k was run with 10 random seeds. We chose k by how reproducible the groups
> are across seeds (mean pairwise adjusted Rand index), among values of k where
> every group holds at least 5% of papers. Silhouette is reported but not used to
> choose k. Before clustering we removed off-topic papers: the 123 papers
> rejected in the manual review, papers with at least 5 health words and more
> than twice as many health words as education words (unless the title names an
> education activity and is not about patients), and papers with an abstract but
> no education signal. We compare the topic groups with country and with the
> collaboration communities using normalized mutual information (NMI), bias-
> corrected Cramer's V and a permutation test with 1,000 shuffles.

### 3.4 Section 5 (replacement)

> ## 5. Topic clustering (RQ3)
>
> ### 5.1 Method and sample
> We started from the 3,095 STRICT papers rated likely relevant. A first run
> (k = 8) produced two clusters that read as clinical. A targeted review of 125
> papers from them found 123 out of scope (53 in cluster 5, 70 in cluster 7).
> This review was targeted, so 123 of 125 is not a false-positive rate for the
> whole dataset. Removing 123 papers still left clinical papers, so we added two
> keyword rules (Section 2.2). Together the manual review and the rules removed
> 776 papers (123 manual, 381 health rule, 272 no-education rule), leaving 2,319.
> Applied blind, the health rule caught 111 of the 123 manually rejected papers.
> In a first-pass check of 100 removed papers by one AI-assisted reader (titles
> only), 98% of papers removed by the health rule and 92% to 98% of papers
> removed by the no-education rule were off-topic. This is an estimate. A human
> check is still pending.
>
> ### 5.2 Choosing the number of groups
> Silhouette is almost flat across k (0.011 to 0.0125), so it cannot choose k.
> Reproducibility differs clearly:
>
> | k | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
> |---|---:|---:|---:|---:|---:|---:|---:|
> | Agreement between 10 seeds (ARI) | **0.80** | 0.57 | 0.48 | 0.42 | 0.42 | 0.41 | 0.42 |
>
> Only k = 4 gives groups that repeat across seeds. Our first-run choices of
> k = 8 and k = 5 are not supported: with 5 seeds, their agreement was 0.46 and
> 0.57 on the earlier sample. Four is the finest division the data supports.
> Removing the off-topic papers changes group membership more than a new random
> seed does (ARI 0.50 against 0.80 at k = 4), as expected because the clinical
> group disappears.
>
> ### 5.3 Four broad themes
> **Table 7. Topic clusters (k = 4, 2,319 papers)**
>
> | Theme (our reading) | Papers | Share | Review-like titles | No abstract |
> |---|---:|---:|---:|---:|
> | Generative AI and higher education | 836 | 36.1% | 5.3% | 10.3% |
> | General AI in education: policy, ethics, reviews | 684 | 29.5% | 25.4% | 10.7% |
> | Machine learning and learning analytics on student data | 606 | 26.1% | 3.3% | 17.0% |
> | Intelligent tutoring and adaptive learning | 193 | 8.3% | 12.4% | 13.0% |
>
> Labels are our reading of top terms and 20 randomly drawn titles per cluster,
> not validated categories. In a first-pass check by one AI-assisted reader (titles
> only), off-topic papers were 0 of 20 in the generative-AI theme, 5 of 20 in the
> machine-learning theme, 1 of 20 in tutoring and 3 of 20 in the general theme.
> With 20 papers per cluster these rates are rough. They suggest that about 11%
> of the 2,319 papers may still be off-topic, mainly in the machine-learning
> and general themes. The general theme is partly a document-type cluster (a
> quarter of its titles are reviews or similar). The generative-AI theme is the
> cleanest.
>
> ### 5.4 How well do topics separate, and how do they relate to country and communities?
> **Table 8. Cluster quality and comparison**
>
> | Measure | Value | Reading |
> |---|---|---|
> | Silhouette, 4 topic groups (all papers, mean of 10 seeds) | 0.012 | Barely above zero: themes overlap strongly |
> | Agreement between random seeds (ARI) | 0.80 | Groups are reproducible |
> | Topic vs dominant country, NMI (22 groups) | 0.016 | Shuffled labels give 0.007. Cramer's V 0.11 |
> | Topic vs collaboration community, NMI (55 communities) | 0.050 | Shuffled labels give 0.038. Cramer's V 0.13 |
> | Topic vs top-10 communities, NMI | 0.021 | Shuffled labels give 0.009. Cramer's V 0.14 |
>
> The links are detectable (permutation p about 0.001 to 0.002) but weak.
> Countries and communities do not map onto themes: each of the ten largest
> communities has papers in all four themes. The community comparison uses the
> 943 cleaned papers with at least two EU institutions. The network for this
> comparison (1,230 institutions, 3,777 links, 55 Louvain communities,
> modularity 0.73) is rebuilt on the cleaned papers, so its counts differ from
> Table 6, which uses the 2,972-paper reviewed set. Countries with fewer than 30
> papers are pooled as "Other".
>
> The 287 papers without abstract (12.4%) are clustered on title only. They
> concentrate in the machine-learning theme (17.0% against 10.3% to 13.0% in the
> others, chi-square p = 0.0006). Refitting without them agrees with the main
> labels at ARI 0.37, while two seeds on the reduced data agree at 0.64, so the
> structure partly depends on these papers.
>
> **Answer to RQ3:** AI-in-education research in the EU is one connected field
> with several largely national collaboration communities. Topics are broad and
> overlapping, and they cut across those communities and across countries.

### 3.5 Section 8, clustering bullet

> - The off-topic filter for topic clustering uses keyword rules. Its precision
>   and the share of off-topic papers left in each cluster come from a
>   first-pass check by one AI-assisted reader on small samples (100 removed and
>   80 kept papers, titles only). Human validation is pending. Residual
>   off-topic papers (about 11% in our estimate) remain, mostly in two themes.

### 3.6 Section 10, scripts line

Replace `src/cluster_analysis_screened.py and src/cluster_analysis_strict_sensitivity.py (clustering)` with:

> `src/cluster_analysis_final.py` (clustering, cleaning rules, seed stability, comparison with country and communities), `src/ai_first_pass_validation.py` (validation samples). The earlier runs `src/cluster_analysis_screened.py` and `src/cluster_analysis_strict_sensitivity.py` are kept for traceability and are superseded.

## 4. Decisions for the team

1. **Report version.** The submitted report shows five themes on 2,972 papers.
   The revised text shows four themes on 2,319 papers. The RQ3 answer does not
   change. Whether to submit the revised section needs lecturer approval.
2. **Slides.** `project-d/ProjectD_clustering_slides.pptx` follows the submitted
   report (five themes). If the revised section is used, the slides must be
   rebuilt with the four-theme numbers.
3. **NMI 0.47.** Check which sample produced the 0.47 for community vs country.
   The reviewed-network file gives 0.40.
4. **Human validation.** Two people should fill the blank rater columns in
   `data/processed/clustering/final/cluster_label_sample.csv` and one person the
   `human_label_in_scope_yes_no` column in `screen_audit_sample.csv`.

