"""Institutional collaboration and venue analysis for Project D."""

import csv
import io
import json
import subprocess
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd


STRICT_PATH = "project-d/data/processed/strict_scopus_provisional.csv"
SCREENED_PATH = "project-d/data/processed/openalex_relevance_screened.csv"

JSONL_PATH = Path("data/processed/openalex_works_deduplicated.jsonl")
REVIEW_PATH = Path(
    "data/processed/clustering/strict_only/"
    "health_title_review_decisions.csv"
)
OUTPUT = Path(
    "data/processed/clustering/strict_only_sensitivity/collaboration"
)

EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
    "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
    "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def normalize_id(value):
    value = str(value or "").strip().rstrip("/")
    return value.rsplit("/", 1)[-1] if value else ""


def clean_country(value):
    value = str(value or "").strip().upper()
    return "" if value in {"", "NONE", "NULL", "NAN"} else value


def read_origin_csv(path):
    raw = subprocess.check_output(
        ["git", "show", f"origin/main:{path}"],
        text=True,
        encoding="utf-8",
    )
    return list(csv.DictReader(io.StringIO(raw)))


def main():
    for path in (JSONL_PATH, REVIEW_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    strict_rows = read_origin_csv(STRICT_PATH)
    screened_rows = read_origin_csv(SCREENED_PATH)
    review = pd.read_csv(REVIEW_PATH, dtype=str, keep_default_na=False)

    strict_by_id = {}
    for row in strict_rows:
        work_id = normalize_id(row.get("openalex_id"))
        if work_id:
            strict_by_id[work_id] = row

    strict_ids = set(strict_by_id)
    likely_ids = {
        normalize_id(row.get("openalex_id"))
        for row in screened_rows
        if row.get("automated_relevance_flag", "").strip()
        == "Likely relevant"
    }
    primary_ids = strict_ids & likely_ids

    if len(primary_ids) != 3095:
        raise ValueError(
            f"Expected 3,095 STRICT likely-relevant records; "
            f"found {len(primary_ids)}."
        )

    review["id_key"] = review["openalex_id"].map(normalize_id)
    decisions = review["final_relevance"].str.strip().value_counts().to_dict()

    if len(review) != 125 or decisions != {
        "Out of scope": 123,
        "Relevant": 2,
    }:
        raise ValueError(
            f"Unexpected manual-review results: {len(review)} rows, {decisions}"
        )

    if review["id_key"].duplicated().any():
        raise ValueError("Duplicate IDs in manual-review file.")

    review_ids = set(review["id_key"])
    if not review_ids.issubset(primary_ids):
        raise ValueError(
            f"{len(review_ids - primary_ids)} reviewed IDs are outside "
            "the STRICT likely-relevant population."
        )

    exclude_ids = set(
        review.loc[
            review["final_relevance"].str.strip().eq("Out of scope"),
            "id_key",
        ]
    )
    retained_ids = primary_ids - exclude_ids

    if len(retained_ids) != 2972:
        raise ValueError(
            f"Expected 2,972 retained records; found {len(retained_ids)}."
        )

    retained_rows = [
        strict_by_id[work_id] for work_id in retained_ids
    ]

    # Build institution metadata lookup from the available OpenAlex corpus.
    # Some affiliation country fields are null. A country is inferred only
    # when the institution has exactly one observed country in this corpus.
    country_counts = defaultdict(Counter)
    name_counts = defaultdict(Counter)
    local_works = {}

    with JSONL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue

            work = json.loads(line)
            work_id = normalize_id(work.get("id"))

            if work_id in retained_ids:
                if work_id in local_works:
                    raise ValueError(
                        f"Duplicate local OpenAlex record: {work_id}"
                    )
                local_works[work_id] = work

            for authorship in work.get("authorships") or []:
                for inst in authorship.get("institutions") or []:
                    inst_id = normalize_id(inst.get("id"))
                    if not inst_id:
                        continue

                    country = clean_country(inst.get("country"))
                    name = str(inst.get("name") or "").strip()

                    if country:
                        country_counts[inst_id][country] += 1
                    if name:
                        name_counts[inst_id][name] += 1

    matched_ids = set(local_works)
    missing_ids = retained_ids - matched_ids

    papers_by_institution = defaultdict(set)
    authors_by_institution = defaultdict(set)
    names_by_institution = defaultdict(Counter)
    countries_by_institution = defaultdict(Counter)
    institution_sets_by_paper = {}

    affiliation_country_explicit = 0
    affiliation_country_inferred = 0
    affiliation_unknown_or_ambiguous = 0
    affiliation_non_eu = 0
    records_with_authorships = 0
    records_with_any_institution = 0

    affiliation_country_unknown_or_ambiguous = 0

    for work_id, work in local_works.items():
        authorships = work.get("authorships") or []

        if authorships:
            records_with_authorships += 1

        if any(
            authorship.get("institutions")
            for authorship in authorships
        ):
            records_with_any_institution += 1

        work_institutions = set()

        for authorship in authorships:
            institutions = authorship.get("institutions") or []
            author_id = normalize_id(authorship.get("author_id"))

            for inst in institutions:
                inst_id = normalize_id(inst.get("id"))
                if not inst_id:
                    continue

                explicit_country = clean_country(inst.get("country"))

                if explicit_country:
                    if explicit_country not in EU27:
                        affiliation_non_eu += 1
                        continue

                    country = explicit_country
                    affiliation_country_explicit += 1
                else:
                    observed = set(country_counts.get(inst_id, {}))

                    if len(observed) != 1:
                        affiliation_country_unknown_or_ambiguous += 1
                        continue

                    country = next(iter(observed))

                    if country not in EU27:
                        affiliation_non_eu += 1
                        continue

                    affiliation_country_inferred += 1

                inst_name = str(inst.get("name") or "").strip()

                if not inst_name and name_counts.get(inst_id):
                    inst_name = sorted(
                        name_counts[inst_id].items(),
                        key=lambda item: (-item[1], item[0]),
                    )[0][0]

                names_by_institution[inst_id][inst_name or inst_id] += 1
                countries_by_institution[inst_id][country] += 1
                papers_by_institution[inst_id].add(work_id)
                work_institutions.add(inst_id)

                if author_id:
                    authors_by_institution[inst_id].add(author_id)

        institution_sets_by_paper[work_id] = work_institutions

    graph = nx.Graph()
    edge_counts = Counter()

    for inst_id, paper_ids in papers_by_institution.items():
        name_counts_local = names_by_institution[inst_id]
        country_counts_local = countries_by_institution[inst_id]

        name = sorted(
            name_counts_local.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]

        country = sorted(
            country_counts_local.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]

        graph.add_node(
            inst_id,
            name=name,
            country=country,
            paper_count=len(paper_ids),
            author_count=len(authors_by_institution[inst_id]),
        )

    # Each edge represents a paper co-authored by two distinct EU27
    # institutions. Weight is the number of shared papers.
    papers_with_eu_institution = 0
    papers_with_two_or_more_eu_institutions = 0

    for work_id, institutions in institution_sets_by_paper.items():
        if institutions:
            papers_with_eu_institution += 1
        if len(institutions) >= 2:
            papers_with_two_or_more_eu_institutions += 1

        for first, second in combinations(sorted(institutions), 2):
            edge_counts[(first, second)] += 1

    for (first, second), weight in edge_counts.items():
        graph.add_edge(first, second, weight=weight)

    isolates = list(nx.isolates(graph))
    active_nodes = [node for node, degree in graph.degree() if degree > 0]
    active_graph = graph.subgraph(active_nodes).copy()

    if active_graph.number_of_nodes() and active_graph.number_of_edges():
        communities = nx.community.louvain_communities(
            active_graph, weight="weight", seed=42
        )
        communities = sorted(
            communities,
            key=lambda group: (-len(group), min(group)),
        )
        modularity = nx.community.modularity(
            active_graph, communities, weight="weight"
        )
    else:
        communities = []
        modularity = None

    community_by_node = {
        node: community_id
        for community_id, members in enumerate(communities)
        for node in members
    }

    # Betweenness is approximated with a fixed sample for reproducibility.
    if active_graph.number_of_nodes() > 1:
        betweenness = nx.betweenness_centrality(
            active_graph,
            k=min(250, active_graph.number_of_nodes()),
            normalized=True,
            seed=42,
        )
    else:
        betweenness = {}

    node_rows = []
    for node, attrs in graph.nodes(data=True):
        degree = graph.degree(node)
        strength = sum(
            edge_data["weight"]
            for _, _, edge_data in graph.edges(node, data=True)
        )

        node_rows.append({
            "institution_id": node,
            "institution_name": attrs["name"],
            "country": attrs["country"],
            "papers": attrs["paper_count"],
            "unique_author_ids": attrs["author_count"],
            "degree": degree,
            "weighted_degree": strength,
            "betweenness_approx": betweenness.get(node, 0.0),
            "community_id": community_by_node.get(node, ""),
            "is_isolate": degree == 0,
        })

    node_df = pd.DataFrame(node_rows)
    if not node_df.empty:
        node_df = node_df.sort_values(
            ["papers", "weighted_degree", "institution_name"],
            ascending=[False, False, True],
        )

    edge_rows = []
    for first, second, attrs in graph.edges(data=True):
        edge_rows.append({
            "institution_1_id": first,
            "institution_1": graph.nodes[first]["name"],
            "country_1": graph.nodes[first]["country"],
            "institution_2_id": second,
            "institution_2": graph.nodes[second]["name"],
            "country_2": graph.nodes[second]["country"],
            "coauthored_papers": attrs["weight"],
            "community_1": community_by_node.get(first, ""),
            "community_2": community_by_node.get(second, ""),
            "same_community": (
                community_by_node.get(first)
                == community_by_node.get(second)
            ),
        })

    edge_df = pd.DataFrame(edge_rows)
    if not edge_df.empty:
        edge_df = edge_df.sort_values(
            ["coauthored_papers", "institution_1", "institution_2"],
            ascending=[False, True, True],
        )

    community_rows = []
    for community_id, members in enumerate(communities):
        ordered_members = sorted(
            members,
            key=lambda node: (
                -graph.nodes[node]["paper_count"],
                graph.nodes[node]["name"],
            ),
        )

        internal_edges = sum(
            1 for u, v in active_graph.subgraph(members).edges()
        )

        country_totals = Counter(
            graph.nodes[node]["country"] for node in members
        )

        community_rows.append({
            "community_id": community_id,
            "institution_count": len(members),
            "internal_edge_count": internal_edges,
            "institution_paper_incidences": sum(
                graph.nodes[node]["paper_count"] for node in members
            ),
            "countries": "; ".join(
                f"{country}:{count}"
                for country, count in country_totals.most_common()
            ),
            "leading_institutions": " | ".join(
                f"{graph.nodes[node]['name']} "
                f"({graph.nodes[node]['paper_count']} papers)"
                for node in ordered_members[:10]
            ),
        })

    # Venue statistics use the official STRICT CSV, so they can cover
    # the full retained population even if local affiliation data are missing.
    venue_counts = Counter()
    venue_year_counts = Counter()
    venue_years = defaultdict(set)
    venue_countries = defaultdict(set)

    for row in retained_rows:
        venue = str(row.get("venue") or "").strip() or "Unknown / missing"
        year = str(row.get("year") or "").strip()
        work_id = normalize_id(row.get("openalex_id"))

        venue_counts[venue] += 1

        if year:
            venue_year_counts[(venue, year)] += 1
            venue_years[venue].add(year)

        countries = str(row.get("eu_countries") or "").split(";")
        venue_countries[venue].update(
            country.strip()
            for country in countries
            if country.strip() in EU27
        )

    venue_rows = []
    for venue, count in venue_counts.items():
        years = sorted(venue_years[venue])
        venue_rows.append({
            "venue": venue,
            "publications": count,
            "share_pct_of_retained_records": round(
                100 * count / len(retained_rows), 2
            ),
            "first_year": years[0] if years else "",
            "last_year": years[-1] if years else "",
            "distinct_eu_countries": len(venue_countries[venue]),
            "eu_countries": "; ".join(sorted(venue_countries[venue])),
        })

    venue_df = pd.DataFrame(venue_rows).sort_values(
        ["publications", "venue"], ascending=[False, True]
    )

    venue_year_df = pd.DataFrame([
        {
            "venue": venue,
            "year": year,
            "publications": count,
        }
        for (venue, year), count in venue_year_counts.items()
    ])
    if not venue_year_df.empty:
        venue_year_df = venue_year_df.sort_values(
            ["venue", "year"]
        )

    years = [
        int(str(row.get("year")).strip())
        for row in retained_rows
        if str(row.get("year") or "").strip().isdigit()
    ]

    summary = {
        "strict_likely_relevant_before_review": len(primary_ids),
        "reviewed_out_of_scope_excluded": len(exclude_ids),
        "reviewed_relevant_retained": int(
            review["final_relevance"].str.strip().eq("Relevant").sum()
        ),
        "retained_records": len(retained_rows),
        "local_jsonl_records_matched": len(local_works),
        "retained_records_missing_local_jsonl": len(missing_ids),
        "matched_records_with_authorships": records_with_authorships,
        "matched_records_with_any_institution": records_with_any_institution,
        "records_with_eu27_institution": papers_with_eu_institution,
        "records_with_two_or_more_eu27_institutions":
            papers_with_two_or_more_eu_institutions,
        "explicit_eu_affiliation_occurrences": affiliation_country_explicit,
        "inferred_eu_affiliation_occurrences": affiliation_country_inferred,
        "unknown_or_ambiguous_affiliation_occurrences":
            affiliation_country_unknown_or_ambiguous,
        "non_eu_affiliation_occurrences": affiliation_non_eu,
        "institution_nodes": graph.number_of_nodes(),
        "institution_edges": graph.number_of_edges(),
        "isolated_institutions": len(isolates),
        "connected_components_including_isolates":
            nx.number_connected_components(graph) if graph.number_of_nodes() else 0,
        "institutions_in_nonisolated_network": active_graph.number_of_nodes(),
        "louvain_communities_nonisolated": len(communities),
        "louvain_modularity_nonisolated": modularity,
        "records_with_known_venue": sum(
            venue != "Unknown / missing"
            for venue in [
                str(row.get("venue") or "").strip() or "Unknown / missing"
                for row in retained_rows
            ]
        ),
        "records_with_missing_venue": venue_counts.get("Unknown / missing", 0),
        "minimum_year": min(years) if years else "",
        "maximum_year": max(years) if years else "",
        "note": (
            "Institution network includes only EU27 affiliations with "
            "explicit or uniquely inferred country metadata. Isolates are "
            "reported separately; communities are detected on the "
            "non-isolated weighted network."
        ),
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([summary]).to_csv(
        OUTPUT / "network_summary.csv", index=False
    )
    node_df.to_csv(OUTPUT / "institution_nodes.csv", index=False)
    edge_df.to_csv(OUTPUT / "institution_edges.csv", index=False)
    pd.DataFrame(community_rows).to_csv(
        OUTPUT / "institution_communities.csv", index=False
    )
    venue_df.to_csv(OUTPUT / "venue_summary.csv", index=False)
    venue_df.head(30).to_csv(OUTPUT / "top_venues.csv", index=False)
    venue_year_df.to_csv(OUTPUT / "venue_year_counts.csv", index=False)

    print("===== POPULATION =====")
    print("STRICT likely-relevant records:", len(primary_ids))
    print("Reviewed out of scope excluded:", len(exclude_ids))
    print("Records retained:", len(retained_rows))
    print("Matched in local OpenAlex JSONL:", len(local_works))
    print("Records missing from local JSONL:", len(missing_ids))

    print("\n===== INSTITUTION NETWORK =====")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n===== TOP INSTITUTIONS BY PUBLICATION COUNT =====")
    if not node_df.empty:
        print(node_df.head(15).to_string(index=False))
    else:
        print("No eligible EU27 institution nodes were found.")

    print("\n===== TOP VENUES =====")
    print(venue_df.head(20).to_string(index=False))

    print("\n===== COMMUNITY SUMMARY =====")
    if community_rows:
        print(pd.DataFrame(community_rows).to_string(index=False))
    else:
        print("No non-isolated institution communities detected.")

    print("\nSaved outputs to:", OUTPUT)
    print("Original clustering results were not modified.")


if __name__ == "__main__":
    main()
