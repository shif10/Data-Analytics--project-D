"""Sensitivity analysis for STRICT AI-in-education records.

Uses the official screened and STRICT CSVs from origin/main.
Excludes manually reviewed Out of scope records, retains Relevant
records, and writes results to a separate output directory.
"""

import csv
import io
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, silhouette_score


STRICT_PATH = "project-d/data/processed/strict_scopus_provisional.csv"
SCREENED_PATH = "project-d/data/processed/openalex_relevance_screened.csv"

REVIEW_PATH = Path("docs/health_title_review_decisions.csv")
ORIGINAL_DIR = Path("data/processed/clustering/strict_only")
OUTPUT = Path("data/processed/clustering/strict_only_sensitivity")

EXPECTED_STRICT_PRIMARY = 3095
EXPECTED_OUT_OF_SCOPE = 123
EXPECTED_RELEVANT = 2
EXPECTED_RETAINED = 2972

EU27 = {
  "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
  "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
  "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def read_origin_csv(repo_path):
  """Read a versioned project CSV from origin/main."""
  raw = subprocess.check_output(
      ["git", "show", f"origin/main:{repo_path}"],
      text=True,
      encoding="utf-8",
  )
  return list(csv.DictReader(io.StringIO(raw)))


def normalize_id(value):
  """Normalize OpenAlex URLs and bare work IDs to the same ID."""
  value = str(value or "").strip().rstrip("/")
  return value.rsplit("/", 1)[-1] if value else ""


def dominant_country(value):
  countries = [
      country.strip().upper()
      for country in (value or "").split(";")
      if country.strip().upper() in EU27
  ]
  if not countries:
      return None
  return max(sorted(set(countries)), key=countries.count)


def main():
  if not REVIEW_PATH.exists():
      raise FileNotFoundError(
          f"Manual-review file not found: {REVIEW_PATH}"
      )

  screened = read_origin_csv(SCREENED_PATH)
  strict = read_origin_csv(STRICT_PATH)
  review = pd.read_csv(
      REVIEW_PATH, dtype=str, keep_default_na=False
  )

  required_review_columns = {
      "openalex_id", "title", "final_relevance", "decision_reason"
  }
  if not required_review_columns.issubset(review.columns):
      raise ValueError(
          "Missing review columns: "
          f"{required_review_columns - set(review.columns)}"
      )

  review["id_key"] = review["openalex_id"].map(normalize_id)
  if review["id_key"].eq("").any():
      raise ValueError("Review file contains an empty OpenAlex ID.")
  if review["id_key"].duplicated().any():
      raise ValueError("Review file contains duplicate OpenAlex IDs.")

  decisions = (
      review["final_relevance"].str.strip().value_counts().to_dict()
  )
  expected_decisions = {"Out of scope": 123, "Relevant": 2}
  if len(review) != 125 or decisions != expected_decisions:
      raise ValueError(
          f"Unexpected review results: {len(review)} records, {decisions}"
      )

  strict_ids = {
      normalize_id(row.get("openalex_id", ""))
      for row in strict
  }
  strict_ids.discard("")

  # Reconstruct the STRICT subset of the original primary population.
  primary = []
  for row in screened:
      if (
          row.get("automated_relevance_flag", "").strip()
          != "Likely relevant"
      ):
          continue

      work_id = normalize_id(row.get("openalex_id", ""))
      if not work_id or work_id not in strict_ids:
          continue

      title = (row.get("title") or "").strip()
      abstract = (row.get("abstract") or "").strip()
      text = " ".join(part for part in (title, abstract) if part)

      if not text:
          continue

      item = dict(row)
      item["text"] = text
      item["dominant_eu_country"] = dominant_country(
          row.get("eu_countries", "")
      )
      item["id_key"] = work_id
      primary.append(item)

  primary_ids = [row["id_key"] for row in primary]

  if len(set(primary_ids)) != len(primary_ids):
      raise ValueError("Duplicate IDs found in the reconstructed population.")

  if len(primary) != EXPECTED_STRICT_PRIMARY:
      raise ValueError(
          "STOP: The original STRICT primary population did not match "
          f"the expected {EXPECTED_STRICT_PRIMARY}. Found {len(primary)}. "
          "No analysis outputs have been written."
      )

  primary_id_set = set(primary_ids)
  review_id_set = set(review["id_key"])

  unmatched_review_ids = review_id_set - primary_id_set
  if unmatched_review_ids:
      raise ValueError(
          f"STOP: {len(unmatched_review_ids)} reviewed IDs are absent "
          "from the reconstructed STRICT primary population."
      )

  out_of_scope_ids = set(
      review.loc[
          review["final_relevance"].str.strip().eq("Out of scope"),
          "id_key",
      ]
  )

  retained = [
      row for row in primary
      if row["id_key"] not in out_of_scope_ids
  ]

  if len(retained) != EXPECTED_RETAINED:
      raise ValueError(
          f"Expected {EXPECTED_RETAINED} retained records; "
          f"found {len(retained)}."
      )

  retained_ids = {row["id_key"] for row in retained}
  reviewed_relevant_ids = set(
      review.loc[
          review["final_relevance"].str.strip().eq("Relevant"),
          "id_key",
      ]
  )

  if not reviewed_relevant_ids.issubset(retained_ids):
      raise ValueError("A Relevant reviewed record was inadvertently removed.")

  review_lookup = dict(zip(review["id_key"], review["final_relevance"]))

  print(f"Official screened records: {len(screened):,}")
  print(f"Official STRICT IDs: {len(strict_ids):,}")
  print(f"STRICT primary population before review: {len(primary):,}")
  print(f"Reviewed Out of scope records excluded: {len(out_of_scope_ids):,}")
  print(f"Reviewed Relevant records retained: {len(reviewed_relevant_ids):,}")
  print(f"Records for sensitivity analysis: {len(retained):,}")

  texts = [row["text"] for row in retained]

  print("\nBuilding TF-IDF features...")
  vectorizer = TfidfVectorizer(
      lowercase=True,
      stop_words="english",
      ngram_range=(1, 2),
      min_df=3,
      max_df=0.90,
      max_features=12000,
      sublinear_tf=True,
  )
  X = vectorizer.fit_transform(texts)
  terms = vectorizer.get_feature_names_out()

  print(f"Feature matrix: {X.shape[0]:,} x {X.shape[1]:,}")
  print("Testing k=4 through k=10...")

  evaluations = []
  fitted_models = {}

  for k in range(4, 11):
      model = KMeans(
          n_clusters=k,
          random_state=42,
          n_init=10,
      )
      labels = model.fit_predict(X)

      score = silhouette_score(
          X,
          labels,
          metric="cosine",
          sample_size=min(2000, X.shape[0]),
          random_state=42,
      )

      evaluations.append({
          "k": k,
          "silhouette_cosine": score,
          "smallest_cluster": int(np.bincount(labels).min()),
          "largest_cluster": int(np.bincount(labels).max()),
      })
      fitted_models[k] = (model, labels)
      print(f"k={k}: silhouette={score:.4f}")

  evaluation_df = pd.DataFrame(evaluations)
  best_k = int(
      evaluation_df.loc[
          evaluation_df["silhouette_cosine"].idxmax(), "k"
      ]
  )
  model, labels = fitted_models[best_k]

  print(f"\nBest tested k by silhouette: {best_k}")

  assignments = pd.DataFrame({
      "openalex_id": [row["openalex_id"] for row in retained],
      "title": [row.get("title", "") for row in retained],
      "year": [row.get("year", "") for row in retained],
      "relevance": [
          row.get("automated_relevance_flag", "") for row in retained
      ],
      "has_abstract": [
          bool(row.get("abstract", "").strip()) for row in retained
      ],
      "is_strict": [True] * len(retained),
      "manual_review_decision": [
          review_lookup.get(row["id_key"], "")
          for row in retained
      ],
      "dominant_eu_country": [
          row["dominant_eu_country"] for row in retained
      ],
      "topic_cluster": labels,
  })

  # Everything below is saved in a NEW directory.
  OUTPUT.mkdir(parents=True, exist_ok=True)
  evaluation_df.to_csv(OUTPUT / "k_evaluation.csv", index=False)
  assignments.to_csv(
      OUTPUT / "cluster_assignments.csv", index=False
  )

  summaries = []
  for cluster_id in range(best_k):
      members = np.where(labels == cluster_id)[0]
      top_indices = np.argsort(
          model.cluster_centers_[cluster_id]
      )[-12:][::-1]

      summaries.append({
          "cluster": cluster_id,
          "size": int(len(members)),
          "share_pct": round(100 * len(members) / len(retained), 2),
          "top_terms": "; ".join(terms[top_indices]),
          "example_titles": " | ".join(
              str(retained[i].get("title", ""))
              for i in members[:5]
          ),
          "reviewed_relevant_count": sum(
              retained[i]["id_key"] in reviewed_relevant_ids
              for i in members
          ),
      })

  pd.DataFrame(summaries).to_csv(
      OUTPUT / "cluster_summary.csv", index=False
  )

  # Compare topic and country labels on the same records.
  eligible = [
      i for i, row in enumerate(retained)
      if row["dominant_eu_country"] is not None
  ]
  rng = np.random.RandomState(42)
  if len(eligible) > 2000:
      eligible = sorted(
          rng.choice(eligible, size=2000, replace=False)
      )

  comparison = {
      "population": "STRICT likely-relevant records excluding reviewed out-of-scope",
      "records_clustered": len(retained),
      "records_with_country": len(eligible),
      "best_k": best_k,
  }

  if len(eligible) >= 3:
      sample_X = X[eligible]
      topic_labels = labels[eligible]
      country_labels = [
          retained[i]["dominant_eu_country"] for i in eligible
      ]

      if 1 < len(set(topic_labels)) < len(topic_labels):
          comparison["topic_cluster_silhouette"] = silhouette_score(
              sample_X, topic_labels, metric="cosine"
          )

      if 1 < len(set(country_labels)) < len(country_labels):
          comparison["country_baseline_silhouette"] = silhouette_score(
              sample_X, country_labels, metric="cosine"
          )

  pd.DataFrame([comparison]).to_csv(
      OUTPUT / "baseline_comparison.csv", index=False
  )

  # Compare silhouette and cluster-size metrics across k.
  original_eval_path = ORIGINAL_DIR / "k_evaluation.csv"
  if original_eval_path.exists():
      original_eval = pd.read_csv(original_eval_path)
      original_eval = original_eval.rename(columns={
          column: f"{column}_original"
          for column in original_eval.columns
          if column != "k"
      })

      sensitivity_eval = evaluation_df.rename(columns={
          column: f"{column}_sensitivity"
          for column in evaluation_df.columns
          if column != "k"
      })

      original_eval.merge(
          sensitivity_eval, on="k", how="outer"
      ).sort_values("k").to_csv(
          OUTPUT / "k_evaluation_comparison.csv", index=False
      )

  # Measure assignment stability on the same retained IDs.
  original_assignment_path = ORIGINAL_DIR / "cluster_assignments.csv"
  original_assignments = pd.read_csv(
      original_assignment_path, dtype=str, keep_default_na=False
  )

  if not {"openalex_id", "topic_cluster"}.issubset(
      original_assignments.columns
  ):
      raise ValueError(
          "Original assignments must contain openalex_id and topic_cluster."
      )

  original_merge = pd.DataFrame({
      "id_key": original_assignments["openalex_id"].map(normalize_id),
      "original_cluster": original_assignments["topic_cluster"],
  })
  new_merge = pd.DataFrame({
      "id_key": assignments["openalex_id"].map(normalize_id),
      "sensitivity_cluster": assignments["topic_cluster"].astype(str),
  })

  if (
      original_merge["id_key"].duplicated().any()
      or new_merge["id_key"].duplicated().any()
  ):
      raise ValueError("Duplicate IDs prevent a reliable stability comparison.")

  common = original_merge.merge(
      new_merge, on="id_key", how="inner", validate="one_to_one"
  )

  if len(common) != len(retained):
      raise ValueError(
          f"Expected {len(retained)} shared IDs for stability comparison; "
          f"matched {len(common)}."
      )

  ari = adjusted_rand_score(
      common["original_cluster"].astype(str),
      common["sensitivity_cluster"].astype(str),
  )

  pd.DataFrame([{
      "original_records": len(original_assignments),
      "retained_records_compared": len(common),
      "original_cluster_count": common["original_cluster"].nunique(),
      "sensitivity_best_k": best_k,
      "adjusted_rand_index": ari,
      "note": (
          "ARI compares memberships on the same retained records; "
          "cluster numbers are arbitrary and need not match."
      ),
  }]).to_csv(OUTPUT / "stability_comparison.csv", index=False)

  crosswalk = (
      common.groupby(
          ["original_cluster", "sensitivity_cluster"]
      )
      .size()
      .reset_index(name="shared_records")
  )
  crosswalk.to_csv(
      OUTPUT / "cluster_membership_crosswalk.csv", index=False
  )

  pd.DataFrame([{
      "screened_records_total": len(screened),
      "strict_ids_total": len(strict_ids),
      "strict_primary_before_review": len(primary),
      "reviewed_records_total": len(review),
      "reviewed_out_of_scope_excluded": len(out_of_scope_ids),
      "reviewed_relevant_retained": len(reviewed_relevant_ids),
      "reviewed_ids_unmatched": len(unmatched_review_ids),
      "sensitivity_records": len(retained),
      "sensitivity_best_k": best_k,
  }]).to_csv(OUTPUT / "coverage.csv", index=False)

  print("\nSensitivity results saved to:", OUTPUT)
  print(" - k_evaluation.csv")
  print(" - k_evaluation_comparison.csv (if original evaluation exists)")
  print(" - cluster_assignments.csv")
  print(" - cluster_summary.csv")
  print(" - baseline_comparison.csv")
  print(" - stability_comparison.csv")
  print(" - cluster_membership_crosswalk.csv")
  print(" - coverage.csv")
  print(f"\nAdjusted Rand Index against original assignments: {ari:.4f}")
  print("Original clustering outputs were not overwritten.")


if __name__ == "__main__":
  main()
