
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score


INPUT = Path("data/processed/openalex_works_deduplicated.jsonl")
OUTPUT = Path("data/processed/clustering")

EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
    "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
    "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def load_works():
    with INPUT.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]




def get_text(work):
    topics = [
        str(topic)
        for topic in (work.get("topics") or [])
        if topic
    ]

    concepts = [
        item["name"]
        for item in (work.get("concepts") or [])
        if isinstance(item, dict) and item.get("name")
    ]

    return " ".join(topics + concepts)


def get_eu_country(work):
    countries = []

    for authorship in work.get("authorships") or []:
        for country in authorship.get("countries") or []:
            if country in EU27:
                countries.append(country)

    if not countries:
        return None

    # Dominant affiliation country for the country-only baseline.
    return Counter(countries).most_common(1)[0][0]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    works = load_works()

    texts = [get_text(work) for work in works]
    valid_indices = [i for i, text in enumerate(texts) if text.strip()]

    if len(valid_indices) < 10:
        raise ValueError("Too few works have topics or concepts to cluster.")

    works = [works[i] for i in valid_indices]
    texts = [texts[i] for i in valid_indices]
    countries = [get_eu_country(work) for work in works]

    print(f"Works loaded: {len(works):,}")
    print("Building TF-IDF features...")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.90,
        max_features=8000,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(texts)
    terms = vectorizer.get_feature_names_out()

    print(f"Feature matrix: {X.shape[0]:,} works x {X.shape[1]:,} features")
    print("Testing cluster counts from 4 to 10...")

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
            sample_size=min(2500, X.shape[0]),
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
    evaluation_df.to_csv(OUTPUT / "k_evaluation.csv", index=False)

    # Choose the tested k with the highest silhouette score.
    best_k = int(
        evaluation_df.loc[
            evaluation_df["silhouette_cosine"].idxmax(), "k"
        ]
    )
    model, labels = fitted_models[best_k]
    print(f"\nBest tested k by silhouette: {best_k}")

    # Compare topic clusters with country groups on the SAME works.
    country_indices = [
        i for i, country in enumerate(countries)
        if country is not None
    ]

    rng = np.random.RandomState(42)
    if len(country_indices) > 2500:
        country_indices = sorted(
            rng.choice(country_indices, size=2500, replace=False)
        )

    comparison = {}
    if len(country_indices) >= 3:
        sample_X = X[country_indices]
        topic_labels = labels[country_indices]
        country_labels = [countries[i] for i in country_indices]

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

    # Save a label for every work used in clustering.
    assignments = pd.DataFrame({
        "id": [work.get("id") for work in works],
        "title": [work.get("title") for work in works],
        "year": [work.get("year") for work in works],
        "topic_cluster": labels,
        "dominant_eu_country": countries,
    })
    assignments.to_csv(OUTPUT / "cluster_assignments.csv", index=False)

    # Summarise the leading terms and example titles per cluster.
    summaries = []
    for cluster_id in range(best_k):
        members = np.where(labels == cluster_id)[0]
        top_term_indices = np.argsort(model.cluster_centers_[cluster_id])[-10:][::-1]
        top_terms = [terms[i] for i in top_term_indices]

        example_titles = [
            str(works[i].get("title") or "")
            for i in members[:5]
            if works[i].get("title")
        ]

        summaries.append({
            "cluster": cluster_id,
            "size": len(members),
            "top_terms": "; ".join(top_terms),
            "example_titles": " | ".join(example_titles),
        })

    pd.DataFrame(summaries).to_csv(
        OUTPUT / "cluster_summary.csv", index=False
    )

    print("\nSaved results in:", OUTPUT)
    print(" - k_evaluation.csv")
    print(" - baseline_comparison.csv")
    print(" - cluster_assignments.csv")
    print(" - cluster_summary.csv")


if __name__ == "__main__":
    main()
