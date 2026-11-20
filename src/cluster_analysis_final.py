"""Final text-clustering analysis for STRICT AI-in-education records.

Replaces the scattered cluster_analysis_*.py runs. Reads only local files
(no git/origin dependency) and writes to data/processed/clustering/final/.

What this script does (see docs/CLUSTERING_FIXES.md):
  1. Rebuild the STRICT likely-relevant population (expected 3,095).
  2. Remove off-topic health/clinical records: manual review decisions
     plus a transparent, validated keyword rule.
  3. Choose k from seed stability and cluster size, not from silhouette.
  4. Measure stability at FIXED k (seed-to-seed ARI; before/after cleaning).
  5. Compare topic clusters with country and with Louvain collaboration
     communities (NMI, ARI, Cramer's V, permutation test).
  6. Check records without abstracts (cluster distribution + robustness).
  7. Export per-cluster samples for label validation by two raters.

Run from the repository root:  python src/cluster_analysis_final.py
"""

import re
import sys
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
    silhouette_score,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCREENED = Path("project-d/data/processed/openalex_relevance_screened.csv")
STRICT = Path("project-d/data/processed/strict_scopus_provisional.csv")
AFFILIATIONS = Path(
    "project-d/data/processed/eu_paper_institution_affiliations.csv"
)
REVIEW = Path("docs/health_title_review_decisions.csv")
OUT = Path("data/processed/clustering/final")

EXPECTED_PRIMARY = 3095
K_RANGE = range(4, 11)
N_SEEDS = 10
MIN_CLUSTER_SHARE = 0.05
SEED = 42

EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}

# Health-domain rule. Counts of health words vs education-context words in
# title + abstract. "education" alone is deliberately not an education word
# because health papers use it ("patient education", "education groups").
HEALTH_RE = re.compile(
    r"\b(patients?|clinical|clinic|diseases?|cancer|tumou?rs?|surgery|"
    r"surgical|diagnos\w*|therap\w*|mortality|hospital\w*|medical|medicine|"
    r"health\w*|nursing|dental|cardio\w*|diabet\w*|depress\w*|disorders?|"
    r"symptoms?|pregnan\w*|covid\S*|biomarkers?|radiolog\w*|imaging|"
    r"genom\w*|pathology|physician\w*|prognos\w*|treatment|illness|"
    r"psychiatr\w*|mental)\b",
    re.I,
)
EDU_RE = re.compile(
    r"\b(students?|teachers?|teaching|learners?|pedagog\w*|classrooms?|"
    r"curricul\w*|schools?|universit\w*|higher education|e-learning|"
    r"tutor\w*|instructors?|lecturers?|educators?|undergraduates?|"
    r"pupils?|courses?|academic|educational|learning outcomes?|moocs?|"
    r"chatgpt)\b",
    re.I,
)
# A title that names an education activity keeps a record in scope
# unless it is about educating patients.
TITLE_EDU_RE = re.compile(
    r"\b(educat\w*|teach\w*|student\w*|curricul\w*|pedagog\w*|school\w*|"
    r"course\w*|tutor\w*|training|workshop\w*|universit\w*)\b",
    re.I,
)
PATIENT_RE = re.compile(r"\bpatients?\b|\bpatient-", re.I)
# Rule 2 (no education context): a record with an abstract that has no
# narrow education word, no education word in the title, and at most one
# education word in the abstract is treated as off-topic general ML/AI.
TITLE_SIGNAL_RE = re.compile(
    r"knowledge tracing|learning analytics|\bAIED\b|literacy|\bMOOC|"
    r"intelligent tutoring|textbooks?|question generation|educat\w*|"
    r"teach\w*|student\w*|school\w*|curricul\w*|pedagog\w*|learner\w*",
    re.I,
)
ABSTRACT_SIGNAL_RE = re.compile(
    r"educat\w*|teach\w*|student\w*|school\w*|pedagog\w*|learner\w*", re.I
)


def normalize_id(value):
    value = str(value or "").strip().rstrip("/")
    return value.rsplit("/", 1)[-1] if value else ""


def dominant_country(value):
    countries = [
        c.strip().upper()
        for c in (value or "").split(";")
        if c.strip().upper() in EU27
    ]
    if not countries:
        return None
    return max(sorted(set(countries)), key=countries.count)


def load_population():
    screened = pd.read_csv(SCREENED, dtype=str, keep_default_na=False)
    strict = pd.read_csv(STRICT, dtype=str, keep_default_na=False)
    strict_ids = set(strict["openalex_id"].map(normalize_id)) - {""}

    screened["id_key"] = screened["openalex_id"].map(normalize_id)
    pop = screened[
        screened["automated_relevance_flag"].str.strip().eq("Likely relevant")
        & screened["id_key"].isin(strict_ids)
    ].copy()
    pop["text"] = (pop["title"].str.strip() + " " + pop["abstract"].str.strip()).str.strip()
    pop = pop[pop["text"] != ""].reset_index(drop=True)

    if pop["id_key"].duplicated().any():
        raise ValueError("Duplicate IDs in the reconstructed population.")
    if len(pop) != EXPECTED_PRIMARY:
        raise ValueError(
            f"Expected {EXPECTED_PRIMARY} records, found {len(pop)}."
        )
    pop["has_abstract"] = pop["abstract"].str.strip().ne("")
    pop["dominant_country"] = pop["eu_countries"].map(dominant_country)
    return pop


def health_rule(pop):
    """Return boolean Series: True where the keyword rule flags a record."""
    h = pop["text"].map(lambda t: len(HEALTH_RE.findall(t)))
    e = pop["text"].map(lambda t: len(EDU_RE.findall(t)))
    rescued = pop["title"].map(
        lambda t: bool(TITLE_EDU_RE.search(t)) and not PATIENT_RE.search(t)
    )
    flagged = (h >= 5) & (h > 2 * e) & ~rescued
    return flagged, h, e


def no_education_rule(pop, e):
    """Rule 2: abstract present but essentially no education signal."""
    title_signal = pop["title"].map(lambda t: bool(TITLE_SIGNAL_RE.search(t)))
    abs_signal = pop["abstract"].map(lambda t: len(ABSTRACT_SIGNAL_RE.findall(t)))
    return pop["has_abstract"] & (e == 0) & ~title_signal & (abs_signal <= 1)


def clean_population(pop):
    review = pd.read_csv(REVIEW, dtype=str, keep_default_na=False)
    review["id_key"] = review["openalex_id"].map(normalize_id)
    oos = set(review.loc[review["final_relevance"].str.strip().eq("Out of scope"), "id_key"])
    rel = set(review.loc[review["final_relevance"].str.strip().eq("Relevant"), "id_key"])

    flagged, h, e = health_rule(pop)
    pop["health_terms"] = h
    pop["edu_terms"] = e
    pop["rule_flag"] = flagged
    pop["rule2_flag"] = no_education_rule(pop, e) & ~flagged
    pop["manual_oos"] = pop["id_key"].isin(oos)
    pop["manual_relevant"] = pop["id_key"].isin(rel)

    # Manual decisions override the rule in both directions.
    auto = (pop["rule_flag"] | pop["rule2_flag"]) & ~pop["manual_relevant"]
    pop["excluded"] = pop["manual_oos"] | auto
    pop["exclusion_reason"] = np.select(
        [
            pop["manual_oos"],
            auto & pop["rule_flag"],
            auto & pop["rule2_flag"],
        ],
        ["manual_review_out_of_scope", "health_domain_rule", "no_education_context_rule"],
        default="",
    )

    # Validate the rule against the manual decisions (rule applied blind).
    rows = [{
        "metric": "manual_out_of_scope_records", "value": len(oos),
    }, {
        "metric": "rule_recall_on_manual_out_of_scope",
        "value": round(pop.loc[pop["manual_oos"], "rule_flag"].mean(), 4),
    }, {
        "metric": "manual_relevant_flagged_by_rule",
        "value": int(pop.loc[pop["manual_relevant"], "rule_flag"].sum()),
    }, {
        "metric": "health_rule_exclusions_unreviewed",
        "value": int(((pop["exclusion_reason"] == "health_domain_rule") & ~pop["manual_oos"]).sum()),
    }, {
        "metric": "no_education_context_exclusions",
        "value": int((pop["exclusion_reason"] == "no_education_context_rule").sum()),
    }, {
        "metric": "population_before_cleaning", "value": len(pop),
    }, {
        "metric": "population_after_cleaning", "value": int((~pop["excluded"]).sum()),
    }, {
        "metric": "note",
        "value": "The manual review sampled only the two most health-heavy "
                 "clusters, so rule recall on it is optimistic. Rule "
                 "precision on unreviewed records is checked with "
                 "screen_audit_sample.csv.",
    }]
    pd.DataFrame(rows).to_csv(OUT / "cleaning_validation.csv", index=False)

    # Audit sample for human verification.
    rng = np.random.RandomState(SEED)
    health_only = pop[pop["exclusion_reason"] == "health_domain_rule"]
    edu_only = pop[pop["exclusion_reason"] == "no_education_context_rule"]
    kept_health = pop[(~pop["excluded"]) & (pop["health_terms"] >= 5)]
    parts = []
    for name, frame in (
        ("excluded_by_health_rule", health_only),
        ("excluded_by_no_education_rule", edu_only),
        ("kept_with_health_terms", kept_health),
    ):
        n = min(50, len(frame))
        sample = frame.iloc[rng.choice(len(frame), n, replace=False)]
        parts.append(sample.assign(audit_group=name))
    audit = pd.concat(parts)[[
        "audit_group", "openalex_id", "title", "health_terms", "edu_terms",
    ]]
    audit["human_label_in_scope_yes_no"] = ""
    audit.to_csv(OUT / "screen_audit_sample.csv", index=False)

    pop[pop["excluded"]][[
        "openalex_id", "title", "health_terms", "edu_terms", "exclusion_reason",
    ]].to_csv(OUT / "excluded_records.csv", index=False)
    return pop


def vectorize(texts):
    vec = TfidfVectorizer(
        lowercase=True, stop_words="english", ngram_range=(1, 2),
        min_df=3, max_df=0.90, max_features=12000, sublinear_tf=True,
    )
    X = vec.fit_transform(texts)
    return X, vec.get_feature_names_out()


def fit(X, k, seed):
    model = KMeans(n_clusters=k, random_state=seed, n_init=10)
    return model, model.fit_predict(X)


def mean_pairwise_ari(label_sets):
    scores = [adjusted_rand_score(a, b) for a, b in combinations(label_sets, 2)]
    return float(np.mean(scores)), float(np.std(scores))


def evaluate_k(X):
    rows, runs = [], {}
    for k in K_RANGE:
        fits = [fit(X, k, SEED + s) for s in range(N_SEEDS)]
        label_sets = [lab for _, lab in fits]
        sils = [silhouette_score(X, lab, metric="cosine") for lab in label_sets]
        ari_mean, ari_sd = mean_pairwise_ari(label_sets)
        sizes = np.bincount(label_sets[0], minlength=k)
        rows.append({
            "k": k,
            "silhouette_full_mean": np.mean(sils),
            "silhouette_full_sd": np.std(sils),
            "seed_ari_mean": ari_mean,
            "seed_ari_sd": ari_sd,
            "smallest_cluster_share": sizes.min() / len(label_sets[0]),
            "largest_cluster_share": sizes.max() / len(label_sets[0]),
        })
        runs[k] = fits
        print(f"k={k}: sil={np.mean(sils):.4f}+-{np.std(sils):.4f} "
              f"seedARI={ari_mean:.3f}")
    table = pd.DataFrame(rows)
    ok = table[table["smallest_cluster_share"] >= MIN_CLUSTER_SHARE]
    if ok.empty:
        ok = table
    chosen = int(ok.loc[ok["seed_ari_mean"].idxmax(), "k"])
    return table, chosen, runs


def cramers_v(table):
    chi2 = chi2_contingency(table, correction=False)[0]
    n = table.values.sum()
    r, c = table.shape
    phi2 = chi2 / n
    # Bergsma bias correction
    phi2c = max(0, phi2 - (c - 1) * (r - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    cc = c - (c - 1) ** 2 / (n - 1)
    return float(np.sqrt(phi2c / max(min(rc - 1, cc - 1), 1e-12)))


def association(topic, other, label, rng, n_perm=1000):
    """NMI/ARI/Cramer's V between topic clusters and another labelling."""
    topic = np.asarray(topic)
    other = np.asarray(other)
    nmi = normalized_mutual_info_score(topic, other)
    ari = adjusted_rand_score(topic, other)
    table = pd.crosstab(topic, other)
    chi2, p, dof, _ = chi2_contingency(table, correction=False)
    v = cramers_v(table)
    null = np.array([
        normalized_mutual_info_score(topic, rng.permutation(other))
        for _ in range(n_perm)
    ])
    p_perm = float((np.sum(null >= nmi) + 1) / (n_perm + 1))
    return {
        "comparison": label, "records": len(topic),
        "n_groups_other": len(set(other)),
        "nmi": nmi, "nmi_permutation_mean": float(null.mean()),
        "nmi_permutation_p": p_perm, "ari": ari,
        "cramers_v_bias_corrected": v,
        "chi2_p_value": float(p),
        "note": "chi-square p-value is unreliable with sparse cells; "
                "prefer the permutation p-value.",
    }


def collaboration_communities(ids):
    """Louvain communities of EU institutions on the given papers."""
    aff = pd.read_csv(AFFILIATIONS, dtype=str, keep_default_na=False)
    aff["id_key"] = aff["openalex_id"].map(normalize_id)
    aff = aff[aff["id_key"].isin(ids) & aff["institution_id"].ne("")]
    per_paper = aff.groupby("id_key")["institution_id"].apply(lambda s: sorted(set(s)))
    graph = nx.Graph()
    for insts in per_paper:
        graph.add_nodes_from(insts)
        for a, b in combinations(insts, 2):
            w = graph[a][b]["weight"] + 1 if graph.has_edge(a, b) else 1
            graph.add_edge(a, b, weight=w)
    core = graph.subgraph([n for n in graph if graph.degree(n) > 0]).copy()
    comms = nx.community.louvain_communities(core, weight="weight", seed=SEED)
    modularity = nx.community.modularity(core, comms, weight="weight")
    comm_of = {n: i for i, c in enumerate(comms) for n in c}
    paper_comm = {}
    for pid, insts in per_paper.items():
        votes = [comm_of[i] for i in insts if i in comm_of]
        if len(insts) >= 2 and votes:
            counts = pd.Series(votes).value_counts()
            paper_comm[pid] = int(counts.index[0])
    stats = {
        "institution_nodes": graph.number_of_nodes(),
        "nodes_with_collaboration": core.number_of_nodes(),
        "edges": core.number_of_edges(),
        "louvain_communities": len(comms),
        "modularity": modularity,
        "papers_with_2plus_eu_institutions": len(paper_comm),
    }
    return paper_comm, stats


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(SEED)

    pop = load_population()
    print(f"Population before cleaning: {len(pop):,}")
    pop = clean_population(pop)
    clean = pop[~pop["excluded"]].reset_index(drop=True)
    print(f"Excluded: {int(pop['excluded'].sum()):,}")
    print(pop["exclusion_reason"].replace("", "kept").value_counts().to_string())
    print(f"Cleaned population: {len(clean):,}")

    X, terms = vectorize(clean["text"].tolist())
    print(f"Feature matrix: {X.shape}")

    # --- k selection and seed stability -------------------------------
    k_table, k, runs = evaluate_k(X)
    k_table.to_csv(OUT / "k_evaluation.csv", index=False)
    print(f"\nSelected k={k} (highest seed stability with every cluster "
          f">= {MIN_CLUSTER_SHARE:.0%} of records)")

    # Reference fit: the seed-run closest to the others (medoid by ARI).
    fits = runs[k]
    labs = [lab for _, lab in fits]
    scores = [np.mean([adjusted_rand_score(a, b) for b in labs if b is not a]) for a in labs]
    best_idx = int(np.argmax(scores))
    model, labels = fits[best_idx]
    clean["topic_cluster"] = labels

    # --- cleaning effect at fixed k -----------------------------------
    Xall, _ = vectorize(pop["text"].tolist())
    _, labels_all = fit(Xall, k, SEED)
    pop["cluster_before_cleaning"] = labels_all
    common = pop[~pop["excluded"]].reset_index(drop=True)
    ari_clean = adjusted_rand_score(common["cluster_before_cleaning"], clean["topic_cluster"])
    ari_seed_mean, ari_seed_sd = mean_pairwise_ari(labs)
    stability = pd.DataFrame([{
        "k": k,
        "records_before": len(pop), "records_after": len(clean),
        "ari_before_vs_after_cleaning_same_k": ari_clean,
        "ari_between_seeds_mean_after_cleaning": ari_seed_mean,
        "ari_between_seeds_sd": ari_seed_sd,
        "interpretation": "If the before/after ARI is close to the "
                          "between-seed ARI, cleaning changes assignments "
                          "no more than a different random seed does.",
    }])
    stability.to_csv(OUT / "stability.csv", index=False)
    print(f"ARI before/after cleaning (k={k}): {ari_clean:.3f}; "
          f"between seeds: {ari_seed_mean:.3f}+-{ari_seed_sd:.3f}")

    # --- assignments and summaries ------------------------------------
    clean[[
        "openalex_id", "title", "year", "type", "has_abstract",
        "dominant_country", "topic_cluster",
    ]].to_csv(OUT / "cluster_assignments.csv", index=False)

    review_flag = clean["title"].str.contains(
        r"\breview\b|systematic|meta-analysis|scoping|literature|bibliometric|overview",
        case=False, regex=True,
    )
    summaries = []
    for c in range(k):
        idx = np.where(labels == c)[0]
        top = np.argsort(model.cluster_centers_[c])[-12:][::-1]
        sub = clean.iloc[idx]
        summaries.append({
            "cluster": c, "size": len(idx),
            "share_pct": round(100 * len(idx) / len(clean), 2),
            "top_terms": "; ".join(terms[top]),
            "share_review_like_titles_pct": round(100 * review_flag.iloc[idx].mean(), 1),
            "share_no_abstract_pct": round(100 * (~sub["has_abstract"]).mean(), 1),
            "share_health_terms_ge5_pct": round(100 * (sub["health_terms"] >= 5).mean(), 1),
        })
    pd.DataFrame(summaries).to_csv(OUT / "cluster_summary.csv", index=False)

    # Samples for label validation (two raters fill the blank columns).
    sample_rows = []
    for c in range(k):
        sub = clean[clean["topic_cluster"] == c]
        pick = sub.iloc[rng.choice(len(sub), min(20, len(sub)), replace=False)]
        for _, r in pick.iterrows():
            sample_rows.append({
                "cluster": c, "openalex_id": r["openalex_id"],
                "title": r["title"], "type": r["type"],
                "rater1_in_scope_yes_no": "", "rater2_in_scope_yes_no": "",
                "rater1_theme": "", "rater2_theme": "",
            })
    pd.DataFrame(sample_rows).to_csv(OUT / "cluster_label_sample.csv", index=False)

    # --- venues of the cleaned population -------------------------------
    strict = pd.read_csv(STRICT, dtype=str, keep_default_na=False)
    strict["id_key"] = strict["openalex_id"].map(normalize_id)
    venues = clean[["id_key", "topic_cluster"]].merge(
        strict[["id_key", "venue"]].drop_duplicates("id_key"), on="id_key", how="left"
    )
    venues["venue"] = venues["venue"].replace("", "(unknown)")
    top_venues = venues["venue"].value_counts().head(15).rename_axis("venue").reset_index(name="records")
    top_venues.to_csv(OUT / "top_venues.csv", index=False)
    pd.crosstab(venues["venue"], venues["topic_cluster"]).loc[top_venues["venue"]].to_csv(
        OUT / "top_venues_by_cluster.csv"
    )

    # --- topic vs country / collaboration ------------------------------
    results = []
    with_country = clean[clean["dominant_country"].notna()]
    counts = with_country["dominant_country"].value_counts()
    big = set(counts[counts >= 30].index)
    country = with_country["dominant_country"].where(
        with_country["dominant_country"].isin(big), "Other"
    )
    results.append(association(
        with_country["topic_cluster"], country,
        f"topic vs dominant EU country (countries >=30 records, else Other)", rng,
    ))
    pd.crosstab(with_country["topic_cluster"], country).to_csv(OUT / "topic_by_country.csv")

    paper_comm, net = collaboration_communities(set(clean["id_key"]))
    pd.DataFrame([net]).to_csv(OUT / "collaboration_network_summary.csv", index=False)
    cc = clean[clean["id_key"].isin(paper_comm)].copy()
    cc["community"] = cc["id_key"].map(paper_comm)
    big_c = set(cc["community"].value_counts().head(10).index)
    cc["community_top10"] = cc["community"].where(cc["community"].isin(big_c), -1)
    results.append(association(
        cc["topic_cluster"], cc["community"],
        "topic vs Louvain institution community (all communities)", rng,
    ))
    results.append(association(
        cc["topic_cluster"], cc["community_top10"],
        "topic vs Louvain institution community (top 10, rest pooled)", rng,
    ))
    pd.crosstab(cc["topic_cluster"], cc["community_top10"]).to_csv(
        OUT / "topic_by_community_top10.csv"
    )
    pd.DataFrame(results).to_csv(OUT / "topic_vs_country_and_community.csv", index=False)

    # --- abstract robustness ------------------------------------------
    table = pd.crosstab(clean["topic_cluster"], clean["has_abstract"])
    _, p_abs, _, _ = chi2_contingency(table)
    with_abs = clean[clean["has_abstract"]].reset_index(drop=True)
    Xa, _ = vectorize(with_abs["text"].tolist())
    _, lab_a = fit(Xa, k, SEED)
    ari_abs = adjusted_rand_score(with_abs["topic_cluster"], lab_a)
    _, lab_b = fit(Xa, k, SEED + 1)
    ari_abs_seed = adjusted_rand_score(lab_a, lab_b)
    pd.DataFrame([{
        "records_without_abstract": int((~clean["has_abstract"]).sum()),
        "share_without_abstract_pct": round(100 * (~clean["has_abstract"]).mean(), 1),
        "chi2_p_cluster_vs_has_abstract": float(p_abs),
        "ari_main_vs_abstract_only_refit": ari_abs,
        "ari_abstract_only_refit_between_two_seeds": ari_abs_seed,
        "records_abstract_only": len(with_abs),
    }]).to_csv(OUT / "abstract_robustness.csv", index=False)
    print(f"No-abstract: {(~clean['has_abstract']).sum()} records; "
          f"chi2 p={p_abs:.3g}; ARI abstract-only refit={ari_abs:.3f}")

    # --- headline ------------------------------------------------------
    sil = float(k_table.loc[k_table["k"] == k, "silhouette_full_mean"].iloc[0])
    pd.DataFrame([{
        "population": "STRICT likely-relevant, cleaned of health-domain and off-topic records",
        "records_clustered": len(clean), "selected_k": k,
        "silhouette_cosine_full_mean": sil,
        "seed_ari_mean": ari_seed_mean,
        "n_seeds": N_SEEDS,
    }]).to_csv(OUT / "final_summary.csv", index=False)

    print("\nTopic vs country / community:")
    print(pd.DataFrame(results)[[
        "comparison", "records", "nmi", "nmi_permutation_mean",
        "nmi_permutation_p", "ari", "cramers_v_bias_corrected",
    ]].to_string(index=False))
    print("\nCollaboration network:", net)
    print(f"\nOutputs written to {OUT}")


if __name__ == "__main__":
    main()
