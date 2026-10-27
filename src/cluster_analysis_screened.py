
import csv
import io
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score


OUTPUT = Path("data/processed/clustering/screened")
STRICT_PATH = (
    "project-d/data/processed/strict_scopus_provisional.csv"
)
SCREENED_PATH = (
    "project-d/data/processed/openalex_relevance_screened.csv"
)

EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
    "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
    "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def read_origin_csv(path):
    raw = subprocess.check_output(
        ["git", "show", f"origin/main:{path}"],
        text=True,
        encoding="utf-8",
    )
    return list(csv.DictReader(io.StringIO(raw)))


def dominant_country(value):
    countries = [
        country.strip()
        for country in (value or "").split(";")
        if country.strip() in EU27
    ]
    if not countries:
        return None
    return max(sorted(set(countries)), key=countries.count)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    screened = read_origin_csv(SCREENED_PATH)
    strict = read_origin_csv(STRICT_PATH)

    strict_ids = {row["openalex_id"] for row in strict}

    # Primary population: records marked likely relevant.
    # Use title when abstract is missing.
    rows = [
        row for row in screened
        if row.get("automated_relevance_flag", "").strip()
        == "Likely relevant"
    ]

    for row in rows:
        row["text"] = " ".join(
            part.strip()
            for part in (
                row.get("title", ""),
                row.get("abstract", ""),
            )
            if part and part.strip()
        )
        row["dominant_eu_country"] = dominant_country(
            row.get("eu_countries", "")
        )
        row["is_strict"] = row["openalex_id"] in strict_ids

    rows = [row for row in rows if row["text"].strip()]

    if len(rows) < 10:
        raise ValueError("Too few records to cluster.")

    texts = [row["text"] for row in rows]

    print(f"Likely relevant records with text: {len(rows):,}")
    print(f"STRICT records in primary population: "
          f"{sum(row['is_strict'] for row in rows):,}")
    print("Building TF-IDF features...")

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

    # Keep the initial search modest to make it practical to run.
    evaluations = []
    models = {}

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
        models[k] = (model, labels)
        print(f"k={k}: silhouette={score:.4f}")

    evaluation_df = pd.DataFrame(evaluations)
    evaluation_df.to_csv(OUTPUT / "k_evaluation.csv", index=False)

    best_k = int(
        evaluation_df.loc[
            evaluation_df["silhouette_cosine"].idxmax(), "k"
        ]
    )
    model, labels = models[best_k]
    print(f"Best tested k by silhouette: {best_k}")

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
        "is_strict": [row["is_strict"] for row in rows],
        "dominant_eu_country": [
            row["dominant_eu_country"] for row in rows
        ],
        "topic_cluster": labels,
    })
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
            "size": len(members),
            "share_pct": round(100 * len(members) / len(rows), 2),
            "top_terms": "; ".join(terms[top_indices]),
            "example_titles": " | ".join(
                rows[i].get("title", "") for i in members[:5]
            ),
            "strict_count": sum(
                rows[i]["is_strict"] for i in members
            ),
        })

    pd.DataFrame(summaries).to_csv(
        OUTPUT / "cluster_summary.csv", index=False
    )

    # Compare topic clusters and country labels on the same records
    # that have a known dominant EU country.
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
        "population": "Likely relevant screened records",
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

    pd.DataFrame([comparison]).to_csv(
        OUTPUT / "baseline_comparison.csv", index=False
    )

    # Sensitivity: compare the primary analysis with all screened
    # records, including those marked "Needs checking".
    pd.DataFrame([{
        "screened_records": len(screened),
        "likely_relevant_records": sum(
            row.get("automated_relevance_flag", "").strip()
            == "Likely relevant" for row in screened
        ),
        "needs_checking_records": sum(
            row.get("automated_relevance_flag", "").strip()
            == "Needs checking" for row in screened
        ),
        "strict_records_total": len(strict_ids),
        "strict_records_in_primary_population": sum(
            row["is_strict"] for row in rows
        ),
    }]).to_csv(OUTPUT / "coverage.csv", index=False)

    print(f"\nSaved results to {OUTPUT}")


if __name__ == "__main__":
    main()
