# Clustering: What Was Fixed

Status of each item from the clustering review. Final code:
`src/cluster_analysis_final.py`. Final report:
`docs/CLUSTERING_AND_INTERPRETATION.md`. Outputs:
`data/processed/clustering/final/`.

**Done by code:** items 1 to 6 and 8. **Needs teammates:** human confirmation of the AI first-pass
checks in items 1 and 7, and the scope decision (listed at the bottom).

## High priority

### 1. Health papers contaminate the corpus: DONE (rule precision still to confirm)
- Health-domain rule removed 381 records, the manual review removed 123,
  and a second rule removed 272 records with no education context
  (general ML papers on climate, tourism, energy and similar). 2,319 remain.
- The rule caught 111 of the 123 manually reviewed out-of-scope records.
- Residual off-topic records remain, mainly in cluster 1. This is stated in the report.
- Rule precision measured on 100 removed records by one AI reader (titles only): 98% (health rule) and 92% to 98% (no-education rule). About 20% to 26% of kept records with many health words are off-topic (about 1.5% of the corpus).
- Still to do: a human confirms the precision figures in `screen_audit_sample.csv`.

### 2. Silhouette too low to support named topics: DONE
- Report now says "four broad, overlapping themes" (silhouette 0.012).
- No claim of distinct topics remains.

### 3. Choice of k not reliable: DONE
- Silhouette is computed on all records, averaged over 10 seeds, and no longer picks k.
- k=4 is chosen for seed stability (ARI 0.80). k of 5 or more gives ARI 0.57 or lower.
- The earlier k=8 and k=5 results are marked superseded.

### 4. Stability metric mixed several changes: DONE
- Seed-to-seed ARI at every k (`k_evaluation.csv`).
- Before/after cleaning at the same k=4: ARI 0.50, against 0.80 between seeds (`stability.csv`).

## Medium priority

### 5. Topic vs country comparison not like for like: DONE
- NMI, ARI, bias-corrected Cramer's V and a 1,000-shuffle permutation test.
- Added topic vs Louvain collaboration community, which research question 3 needs.
- Result: weak but non-zero association (NMI 0.016 with country, 0.021 to 0.050 with community).

### 6. Records without abstracts: DONE
- 12.4% of records. They concentrate in cluster 1 (17.0%, p = 0.0006).
- Refit without them agrees with the main labels at ARI 0.37, against 0.64
  between two seeds. Reported as a limitation (`abstract_robustness.csv`).

### 7. Cluster labels are subjective: DONE as AI first pass, human check pending
- Labels re-derived from top terms plus random titles per cluster. Per-cluster review-like and no-abstract shares added.
- One AI reader labelled 20 records per cluster: off-topic share is 0%, 25%, 5% and 15% for clusters 0 to 3. The cluster 1 label was widened to include learning analytics and teaching ML, because only 8 of 15 in-scope records were about prediction.
- Not possible for me: independent human raters. Their columns in `cluster_label_sample.csv` are blank.

## Housekeeping

### 8. Repository clean-up: DONE
- [x] Backup and "broken backup" scripts moved from `src/` to `archive/`.
- [x] Stale experiment folders and review-decision backups moved to `data/processed/clustering/archive/`.
- [x] `.env` is listed in `.gitignore` and is not tracked by Git.
  Check it holds no secret you would share. It contains an OpenAlex key.
- [x] Report updated to match the final results.
- [x] Final run stated: `src/cluster_analysis_final.py`.
- `archive/` is added to `.gitignore`. Nothing was deleted.

## Remaining human tasks

1. Two raters fill the `rater1_*` and `rater2_*` columns of `cluster_label_sample.csv`; compare with Cohen's kappa.
2. One person fills `human_label_in_scope_yes_no` in `screen_audit_sample.csv`.
3. Team confirms the scope decision on patient-education papers. Working decision: out of scope.
