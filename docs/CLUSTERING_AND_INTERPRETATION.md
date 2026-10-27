# Clustering and Interpretation

## Research question

Which European institutions and venues drive AI-in-education research
since 2020, and do they form one collaboration community or several?

This report distinguishes textual similarity clusters from institutional
collaboration communities. They answer different analytical questions.

## Method

The primary STRICT likely-relevant population contained 3,095 records.
Titles and abstracts were represented using TF-IDF with English stop-word
removal, unigrams and bigrams, `min_df=3`, `max_df=0.90`, up to 12,000
features and sublinear term frequency. KMeans used `random_state=42` and
`n_init=10`. Values of k from 4 to 10 were tested. Cosine silhouette
scores were estimated on a sample of up to 2,000 records.

The highest-scoring tested k is a model-selection aid, not proof that the
corpus contains a naturally fixed number of topics.

## Original STRICT-only text clustering

The best tested solution was k=8, with cosine silhouette 0.012372.

| Cluster | Records | Share | Preliminary interpretation |
|---:|---:|---:|---|
| 0 | 169 | 5.46% | AI-in-education foundations, ethics and policy |
| 1 | 278 | 8.98% | Reviews and literature syntheses |
| 2 | 189 | 6.11% | Intelligent tutoring and adaptive learning |
| 3 | 570 | 18.42% | Generative AI and higher education |
| 4 | 593 | 19.16% | Machine learning and student performance |
| 5 | 548 | 17.71% | Mixed AI applications, including clinical papers |
| 6 | 434 | 14.02% | Teacher and student attitudes and experiences |
| 7 | 314 | 10.15% | Predominantly clinical and health machine learning |

These labels are qualitative interpretations of top terms and example
titles, not independently validated topic categories.

## Targeted manual review

A targeted review examined 125 records from original clusters 5 and 7.
The final decisions were 123 Out of scope and 2 Relevant: cluster 5 had
53 Out of scope and 1 Relevant; cluster 7 had 70 Out of scope and
1 Relevant.

This review targeted likely false positives in two clusters. It was not
a random sample of the entire research population, so its exclusion
proportion must not be presented as the false-positive rate for all records.

## Sensitivity analysis

After excluding the 123 reviewed Out of scope records and retaining the
2 Relevant records, the sensitivity population contained 2,972 records.

The best tested solution changed to k=5, with cosine silhouette 0.012563.
The Adjusted Rand Index comparing original and sensitivity assignments
on the same retained records was 0.526192.

| Cluster | Records | Share | Preliminary interpretation |
|---:|---:|---:|---|
| 0 | 832 | 27.99% | Broad foundations, reviews and policy |
| 1 | 210 | 7.07% | Intelligent tutoring and adaptive learning |
| 2 | 319 | 10.73% | Health and clinical machine-learning crossover |
| 3 | 657 | 22.11% | Machine learning and student performance |
| 4 | 954 | 32.10% | Generative AI, higher education, teachers and students |

Both silhouette scores are very low, indicating substantial overlap
between clusters. The change in preferred k and ARI indicate that removing
the reviewed records affects membership structure. Report these as broad,
overlapping thematic groupings rather than sharply separated topics.

## Institutional collaboration and venues

The separate institutional network analysis retained 2,972 records and
matched 2,908 to local OpenAlex records; 64 were unavailable locally.
It identified 1,641 institution nodes, 7,557 co-authorship edges,
139 isolated institutions, 168 connected components including isolates,
and 46 Louvain communities among non-isolated institutions. Modularity
was 0.6392 under this graph definition.

Leading venues by retained-record count were *Education Sciences* (81),
*Frontiers in Education* (73), *Applied Sciences* (66), *Lecture Notes
in Networks and Systems* (56), and *Communications in Computer and
Information Science* (53).

Text clusters and network communities must not be conflated. Low silhouette
scores indicate weak text-cluster separation. Modularity suggests
community structure within the constructed network but does not, alone,
prove that the research field is fragmented.

## Limitations

The manual review was targeted at clusters 5 and 7 only; residual false
positives may remain elsewhere. The inclusion decisions depend on scope:
if AI-assisted patient education is explicitly included in the team's
definition of AI in education, some excluded clinical-information papers
may warrant reconsideration.

The institutional analysis uses only eligible EU27 affiliations with
explicit or uniquely inferred country metadata. Missing records and
ambiguous affiliation-country data are coverage limitations. Venue counts
are descriptive publication counts, not measures of venue quality.

## Reproducibility

- `src/cluster_analysis_screened.py`: broader likely-relevant population.
- `src/cluster_analysis_strict_sensitivity.py`: STRICT sensitivity analysis.
- `src/collaboration_analysis.py`: institutional network and venue analysis.
- `docs/health_title_review_decisions.csv`: compact manual-review decisions.

Processed CSVs are ignored by the current Git rules. Share them deliberately
if the team needs the generated result tables without rerunning the scripts.
