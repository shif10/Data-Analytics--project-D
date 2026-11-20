"""Text clustering for all 3,668 official STRICT AI-in-education records.

This analysis intentionally does not apply the automated Likely relevant
filter or exclude manually reviewed records.
"""

import csv
import io
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score


STRICT_PATH = "project-d/data/processed/strict_scopus_provisional.csv"
SCREENED_PATH = "project-d/data/processed/openalex_relevance_screened.csv"
REVIEW_PATH = Path("docs/health_title_review_decisions.csv")
OUTPUT = Path("data/processed/clustering/strict_all")

EXPECTED_STRICT = 3668

EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
    "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
    "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def read_origin_csv(repo_path):
    raw = subprocess.check_output(
        ["git", "show", f"origin/main:{repo_path}"],
        text=True,
        encoding="utf-8",
    )
    return list(csv.DictReader(io.StringIO(raw)))


def normalize_id(value):
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
    strict = read_origin_csv(STRICT_PATH)
    screened = read_origin_csv(SCREENED_PATH)

    strict_ids = [normalize_id(row.get("openalex_id", "")) for row in strict]
    if len(strict_ids) != len(set(strict_ids)):
        raise ValueError("STRICT CSV contains duplicate OpenAlex IDs.")
    if len(strict_ids) != EXPECTED_STRICT:
        raise ValueError(
            f"Expected {EXPECTED_STRICT} STRICT records; found {len(strict_ids)}."
        )

    screened_by_id = {}
    for row in screened:
        work_id = normalize_id(row.get("openalex_id", ""))
        if work_id:
            if work_id in screened_by_id:
                raise ValueError(f"Duplicate screened ID: {work_id}")
            screened_by_id[work_id] = row

    review_lookup = {}
    if REVIEW_PATH.exists():
        review = pd.read_csv(REVIEW_PATH, dtype=str, keep_default_na=False)
        if {"openalex_id", "final_relevance"}.issubset(review.columns):
            review_lookup = {
                normalize_id(openalex_id): decision
                for openalex_id, decision in zip(
                    review["openalex_id"],
                    review["final_relevance"],
                )
            }

    rows = []
    for work_id in strict_ids:
        row = screened_by_id.get(work_id)
        if row is None:
            raise ValueError(f"STRICT ID missing from screened CSV: {work_id}")

        title = (row.get("title") or "").strip()
        abstract = (row.get("abstract") or "").strip()
        text = " ".join(part for part in (title, abstract) if part)
        if not text:
            raise ValueError(f"STRICT record has no title or abstract: {work_id}")

        item = dict(row)
        item["text"] = text
        item["id_key"] = work_id
        item["dominant_eu_country"] = dominant_country(
            row.get("eu_countries", "")
        )
        item["manual_review_decision"] = review_lookup.get(work_id, "")
        rows.append(item)

    texts = [row["text"] for row in rows]
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

    print(f"Official STRICT records clustered: {len(rows):,}")
    print(f"Feature matrix: {X.shape[0]:,} x {X.shape[1]:,}")

    evaluations = []
    fitted_models = {}
    for k in range(4, 11):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
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

    assignments = pd.DataFrame({
        "openalex_id": [row["openalex_id"] for row in rows],
        "title": [row.get("title", "") for row in rows],
        "year": [row.get("year", "") for row in rows],
        "relevance": [
            row.get("automated_relevance_flag", "") for row in rows
        ],
        "has_abstract": [
            bool(row.get("abstract", "").strip()) for row in rows
        ],
        "manual_review_decision": [
            row["manual_review_decision"] for row in rows
        ],
        "dominant_eu_country": [
            row["dominant_eu_country"] for row in rows
        ],
        "topic_cluster": labels,
    })

    summaries = []
    for cluster_id in range(best_k):
        members = np.where(labels == cluster_id)[0]
        top_indices = np.argsort(
            model.cluster_centers_[cluster_id]
        )[-12:][::-1]
        summaries.append({
            "cluster": cluster_id,
            "size": len(members),
            "share_pct": round(100 * len(members) / len(rows), 2),
            "top_terms": "; ".join(terms[top_indices]),
            "example_titles": " | ".join(
                str(rows[i].get("title", "")) for i in members[:5]
            ),
            "reviewed_relevant_count": sum(
                rows[i]["manual_review_decision"] == "Relevant"
                for i in members
            ),
            "reviewed_out_of_scope_count": sum(
                rows[i]["manual_review_decision"] == "Out of scope"
                for i in members
            ),
        })

    eligible = [
        i for i, row in enumerate(rows)
        if row["dominant_eu_country"] is not None
    ]
    rng = np.random.RandomState(42)
    if len(eligible) > 2000:
        eligible = sorted(
            rng.choice(eligible, size=2000, replace=False)
        )

    comparison = {
        "population": "All official STRICT records",
        "records_clustered": len(rows),
        "records_with_country": len(eligible),
        "best_k": best_k,
    }
    if len(eligible) >= 3:
        sample_X = X[eligible]
        topic_labels = labels[eligible]
        country_labels = [
            rows[i]["dominant_eu_country"] for i in eligible
        ]
        if 1 < len(set(topic_labels)) < len(topic_labels):
            comparison["topic_cluster_silhouette"] = silhouette_score(
                sample_X, topic_labels, metric="cosine"
            )
        if 1 < len(set(country_labels)) < len(country_labels):
            comparison["country_baseline_silhouette"] = silhouette_score(
                sample_X, country_labels, metric="cosine"
            )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    evaluation_df.to_csv(OUTPUT / "k_evaluation.csv", index=False)
    assignments.to_csv(OUTPUT / "cluster_assignments.csv", index=False)
    pd.DataFrame(summaries).to_csv(
        OUTPUT / "cluster_summary.csv", index=False
    )
    pd.DataFrame([comparison]).to_csv(
        OUTPUT / "baseline_comparison.csv", index=False
    )
    pd.DataFrame([{
        "strict_records": len(rows),
        "likely_relevant_records": sum(
            row.get("automated_relevance_flag", "").strip()
            == "Likely relevant"
            for row in rows
        ),
        "needs_checking_records": sum(
            row.get("automated_relevance_flag", "").strip()
            == "Needs checking"
            for row in rows
        ),
        "best_k": best_k,
    }]).to_csv(OUTPUT / "coverage.csv", index=False)

    print(f"Best tested k by silhouette: {best_k}")
    print(f"All-STRICT results saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
