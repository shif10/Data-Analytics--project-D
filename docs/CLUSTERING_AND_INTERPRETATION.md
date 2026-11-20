# Clustering and Interpretation

## Research question

Which European institutions and venues drive AI-in-education research
since 2020, and do they form one collaboration community or several?

This report keeps two things apart: text-similarity clusters (what papers
are about) and institutional collaboration communities (who works with
whom). They answer different questions.

**Final analysis:** `src/cluster_analysis_final.py`
(outputs in `data/processed/clustering/final/`). Earlier runs are
summarised in the History section and are superseded by this one.

## Headline result

After removing off-topic records, STRICT AI-in-education research in the EU
falls into **four broad, overlapping themes**. The text separation is weak
(cosine silhouette 0.012), so these are descriptive groupings, not distinct
topics. Theme membership is almost independent of country (NMI 0.016,
Cramer's V 0.11) and of institutional collaboration community
(NMI 0.021 to 0.050, Cramer's V 0.13 to 0.14). The association is
statistically detectable (permutation p about 0.001 to 0.002) but weak.

## Method

1. **Population.** 3,095 STRICT records marked "Likely relevant", rebuilt
   from local files (`openalex_relevance_screened.csv` and
   `strict_scopus_provisional.csv`).
2. **Cleaning** (three steps, in this order; the first decision that applies wins):
   - Manual review: 123 "Out of scope" records removed. The 2 "Relevant"
     records are always kept.
   - Health-domain rule: remove a record if its title and abstract contain
     at least 5 health words and more than twice as many health words as
     education words, unless the title names an education activity and is not
     about patients. Removed 381 records.
   - No-education-context rule: for records with an abstract, remove those
     with no narrow education word, no education signal in the title and at
     most one education word in the abstract. Removed 272 records.
   - Result: **2,319 records** (776 removed).
3. **Features.** TF-IDF on title plus abstract: English stop words,
   unigrams and bigrams, `min_df=3`, `max_df=0.90`, 12,000 features,
   sublinear term frequency.
4. **Clustering.** KMeans (`n_init=10`), k from 4 to 10, 10 random seeds
   per k. Silhouette (cosine) is computed on all records, not a sample.
5. **Choice of k.** Highest mean pairwise ARI between seeds among values of
   k where every cluster holds at least 5% of records. Silhouette is
   reported but not used to choose k, because it differs by less than its
   own noise across k.

## Cleaning validation

| Check | Result |
|---|---|
| Manual "Out of scope" records caught by the health rule (rule applied blind) | 90.2% (111 of 123) |
| Manual "Relevant" records flagged by the health rule | 1 of 2 (kept, manual decision overrides) |
| Records removed by the health rule, not manually reviewed | 381 |
| Records removed by the no-education-context rule | 272 |

The 90.2% figure is optimistic: the manual review covered only the two most
health-heavy clusters.

**First-pass check on 150 sampled records** (`screen_audit_sample.csv`,
50 per group). One AI reader judged titles only, so this is an estimate and
not an independent human validation. "Unsure" cases are shown as a range.

| Group | Finding |
|---|---|
| Removed by the health rule | 49 of 50 correctly removed (precision 98%). The one in-scope record: a paper on medical problem representation in the age of AI |
| Removed by the no-education rule | 46 to 49 of 50 correctly removed (precision 92% to 98%). One clearly in-scope record (generative AI for surgical training video) and three unsure editorials or scales |
| Kept records with 5 or more health words | 10 of 50 off-topic (20%), 3 more unsure (up to 26%). Mostly patient-education papers and clinical ChatGPT studies |

The rules rarely remove in-scope records. They miss some patient-education
papers, because the title rescue keeps any title containing "education".
Among about 150 kept records with 5 or more health words, that leaves
roughly 30 to 40 off-topic records (1.5% of 2,319).

Removed records are listed with their reason in `excluded_records.csv`.

## Choice of k and stability

| k | Silhouette (mean of 10 seeds) | Between-seed ARI | Smallest cluster |
|---:|---:|---:|---:|
| 4 | 0.0125 | **0.800** | 8.4% |
| 5 | 0.0119 | 0.570 | 7.2% |
| 6 | 0.0108 | 0.483 | 7.2% |
| 7 | 0.0111 | 0.424 | 3.9% |
| 8 | 0.0110 | 0.419 | 4.0% |
| 9 | 0.0110 | 0.409 | 5.0% |
| 10 | 0.0117 | 0.419 | 3.2% |

Silhouette is flat (0.011 to 0.0125) for every k. Only k=4 gives
reproducible clusters across seeds (ARI 0.80); at k=7 or higher the
partition depends strongly on the random seed (ARI about 0.4). The earlier
choices of k=8 and k=5 are therefore not supported. Four themes is the
finest division the data supports reliably.

**Effect of cleaning at fixed k=4:** ARI between the fit on 3,095 records
and the fit on 2,319 records (same records compared) is 0.50, against 0.80
between seeds. Cleaning changes cluster membership more than a new seed
does. This is expected: the removed records formed a health-and-clinical
group that no longer exists after cleaning.

## Final clusters (k=4, 2,319 records)

Labels come from the top terms and random titles per cluster
(`cluster_label_sample.csv`, 20 per cluster). They are interpretations
checked only by one AI reader (see below), not validated categories.

| Cluster | Records | Share | Interpretation | Review-like titles | No abstract |
|---:|---:|---:|---|---:|---:|
| 0 | 836 | 36.1% | Generative AI, ChatGPT and higher education: use, attitudes of students and teachers | 5.3% | 10.3% |
| 1 | 606 | 26.1% | Machine learning and learning analytics on student data: performance prediction, dropout, teaching ML. Mixed; contains residual off-topic records | 3.3% | 17.0% |
| 2 | 193 | 8.3% | Intelligent tutoring, adaptive learning, feedback | 12.4% | 13.0% |
| 3 | 684 | 29.5% | General AI-in-education: policy, ethics, reviews, editorials, framing. Partly a document-type cluster | 25.4% | 10.7% |

**First-pass label check** (20 random records per cluster, one AI reader,
titles only, `ai_first_pass_validation.csv`):

| Cluster | Off-topic records | In-scope records that fit the label (yes / partial) |
|---:|---:|---|
| 0 | 0 of 20 (0%) | 19 / 1 |
| 1 | 5 of 20 (25%) | 8 / 7 |
| 2 | 1 of 20 (5%) | 17 / 2 |
| 3 | 3 of 20 (15%) | 12 / 5 |

With 20 records per cluster these rates are rough (the margin is several
percentage points either way). Weighted by cluster size, about 11% of the
2,319 records may still be off-topic, mainly in cluster 1 (general
machine-learning studies in psychiatry, neuroscience and social science
with a weak education link) and cluster 3 (editorials, scholar profiles,
general trustworthy-AI papers).

Cluster 0 is the cleanest and best defined. Cluster 1 is the weakest: only
8 of its 15 in-scope sampled records are about predicting student
outcomes, and the rest are teaching machine learning, learning analytics
or critical commentary. Cluster 3 is part topic and part document type:
a quarter of its titles are reviews or similar. Clusters 0 and 2 are the
most reliable themes.

## Topic clusters versus country and collaboration

Normalised mutual information (NMI) measures shared information, 0 meaning
none. The permutation null is the NMI expected if labels were shuffled.

| Comparison | Records | NMI | NMI under shuffling | Permutation p | ARI | Cramer's V |
|---|---:|---:|---:|---:|---:|---:|
| Topic vs dominant EU country (22 groups) | 2,319 | 0.016 | 0.007 | 0.001 | -0.002 | 0.107 |
| Topic vs Louvain community (all 55) | 943 | 0.050 | 0.038 | 0.002 | 0.005 | 0.130 |
| Topic vs Louvain community (top 10 + rest) | 943 | 0.021 | 0.009 | 0.001 | 0.006 | 0.137 |

The association is real but weak. Countries and collaboration communities
do not map onto themes: each of the ten largest communities has papers in
all four themes, and all but one country group (Denmark, no papers in
cluster 2) does too. This answers research question 3: clusters are not
explained by country, and only barely by collaboration community.

Country groups are countries with at least 30 records (others pooled as
"Other"). Each record uses its most frequent EU country. Chi-square
p-values are in the CSV but are unreliable with sparse cells, so use the
permutation p-values.

## Institutional collaboration and venues

The network uses EU affiliations of the 2,319 cleaned records:

- 1,230 institutions, of which 1,085 have at least one co-authorship link
- 3,777 co-authorship edges
- 55 Louvain communities, modularity 0.728
- 943 papers with at least two EU institutions (used for the community comparison)

Several communities, not one, appear under this graph definition. High
modularity does not alone show that the field is fragmented, because
sparse co-authorship graphs give high modularity easily. Many communities
are small.

Most frequent venues among the cleaned records (`top_venues.csv`):
*Education Sciences* (81), *Frontiers in Education* (72), *Applied
Sciences* (57), *Lecture Notes in Networks and Systems* (56),
*Communications in Computer and Information Science* (51), *Sustainability*
(42), *Computers and Education: Artificial Intelligence* (40). Counts are
descriptive, not a measure of venue quality.

## Records without abstracts

287 records (12.4%) have no abstract and are clustered on the title alone.
They are not spread evenly: cluster 1 has 17.0% against 10.3% to 13.0% in
the others (chi-square p = 0.0006).

Robustness: refitting without them gives an ARI of 0.37 against the main
labels, while two seeds on that reduced data agree at 0.64. The structure
depends partly on these records. Treat cluster 1 in particular with
caution.

## Limitations

- Cleaning uses keyword rules. Their precision (92% to 98%) and the
  per-cluster off-topic rates come from one AI reader judging titles only
  on small samples. Human validation is still to do (see Open items).
- The manual review covered 125 records chosen from two clusters. Its
  proportions must not be quoted as an overall false-positive rate.
- Whether AI-assisted patient education belongs in "AI in education" is a
  scope decision. Under a broader definition, some removed records would
  return.
- Silhouette is about 0.012 for every setting. Text overlap between
  themes is large and individual papers can belong to several.
- Only EU-27 affiliations with usable country data enter the network.
  Venue counts include records with missing venue data as "(unknown)".

## Open items for the team

The AI first pass is recorded in separate `ai_pass_*` columns. The human
columns in the sample files are still blank on purpose.

1. Two humans fill `rater1_*` and `rater2_*` in `cluster_label_sample.csv`
   (in scope yes/no, theme). Compare them with Cohen's kappa and replace the
   AI first-pass table above.
2. One human fills `human_label_in_scope_yes_no` in `screen_audit_sample.csv`
   to confirm the rule precision.
3. Team confirms the scope decision on patient-education papers. **Working
   decision until then: they are out of scope**, which matches the manual
   review (123 out-of-scope decisions). If the team decides otherwise, the
   health rule and the manual exclusions need revisiting.

## History (superseded runs)

| Run | Population | Best k by silhouette | Silhouette | Note |
|---|---:|---:|---:|---|
| Screened, all likely-relevant | 6,442 | 4 | 0.0207 | Not limited to STRICT |
| STRICT, all records | 3,668 | 5 | 0.0106 | No relevance filter |
| STRICT primary | 3,095 | 8 | 0.0124 | k=7 scored 0.0121, within noise |
| Sensitivity (manual review applied) | 2,972 | 5 | 0.0126 | ARI 0.53 mixed k=8 vs k=5 |

These used a sampled silhouette, picked k by the maximum silhouette, and
did not fix k when measuring stability. The final analysis corrects all
three. The scripts remain in `src/` for traceability; superseded backups
are in `archive/` (ignored by Git).

## Reproducibility

Run from the repository root:

```
python src/cluster_analysis_final.py
```

Then `python src/ai_first_pass_validation.py` records the AI first-pass
labels and rates.

Inputs: `project-d/data/processed/openalex_relevance_screened.csv`,
`strict_scopus_provisional.csv`, `eu_paper_institution_affiliations.csv`,
and `docs/health_title_review_decisions.csv`. Runtime is a few minutes.
Seeds are fixed (42 to 51). Python 3.11, scikit-learn 1.5.2, networkx.

Processed CSVs are ignored by Git. Share `data/processed/clustering/final/`
deliberately if the team needs the result tables without rerunning.
