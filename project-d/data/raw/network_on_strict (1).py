"""
Rerun Keerthana's collaboration-network pipeline on the STRICT paper set,
so her numbers are directly comparable with John's.

Usage (from the repo root, where project-d/ lives):
    python network_on_strict.py --strict path/to/strict_papers.csv --id-col openalex_id
Optional:
    --resolution 1.0     Louvain resolution (match John's setting; Keerthana used 1.0)
    --all-components     run Louvain on the whole graph instead of the largest component
    --big 30             size threshold for a "large" community (Keerthana used 30)
"""
import argparse, itertools
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd
from networkx.algorithms.community import louvain_communities, modularity
from sklearn.metrics import normalized_mutual_info_score as nmi

ap = argparse.ArgumentParser()
ap.add_argument("--project", default="project-d")
ap.add_argument("--strict", required=True, help="CSV listing the STRICT papers")
ap.add_argument("--id-col", default="openalex_id")
ap.add_argument("--resolution", type=float, default=1.0)
ap.add_argument("--all-components", action="store_true")
ap.add_argument("--big", type=int, default=30)
ap.add_argument("--seed", type=int, default=42)
a = ap.parse_args()

P = Path(a.project) / "data" / "processed"
aff = pd.read_csv(P / "eu_paper_institution_affiliations.csv").drop_duplicates(
    ["openalex_id", "institution_id"])
strict_ids = set(pd.read_csv(a.strict)[a.id_col].astype(str))
country = aff.drop_duplicates("institution_id").set_index("institution_id")["country_code"].to_dict()


def build_graph(links):
    w = Counter()
    for _, g in links.groupby("openalex_id"):
        ids = sorted(set(g.institution_id))
        for u, v in itertools.combinations(ids, 2):
            w[(u, v)] += 1
    G = nx.Graph()
    G.add_nodes_from(links.institution_id.unique())
    G.add_weighted_edges_from([(u, v, c) for (u, v), c in w.items()])
    return G


def summarize(G):
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    H = G.subgraph([n for n in G if G.degree(n) > 0]).copy() if a.all_components else G.subgraph(comps[0]).copy()
    com = louvain_communities(H, weight="weight", seed=a.seed, resolution=a.resolution)
    lab = {n: i for i, c in enumerate(com) for n in c}
    by_country = {}
    for n in H:
        by_country.setdefault(country[n], set()).add(n)
    tw = sum(d["weight"] for *_, d in H.edges(data=True))
    te = H.number_of_edges()
    cross_w = sum(d["weight"] for u, v, d in H.edges(data=True) if country[u] != country[v]) / tw
    in_com_w = sum(d["weight"] for u, v, d in H.edges(data=True) if lab[u] == lab[v]) / tw
    in_com_e = sum(1 for u, v in H.edges() if lab[u] == lab[v]) / te
    return {
        "papers": links_papers(G),
        "institutions": G.number_of_nodes(),
        "links": G.number_of_edges(),
        "largest_component": len(H),
        "communities": len(com),
        f"large_communities (>={a.big})": sum(len(c) >= a.big for c in com),
        "modularity": round(modularity(H, com, weight="weight"), 3),
        "modularity_country_baseline": round(modularity(H, list(by_country.values()), weight="weight"), 3),
        "nmi_vs_country": round(nmi([lab[n] for n in H], [country[n] for n in H]), 3),
        "cross_border_share_of_weight": round(cross_w, 3),
        "within_community_share_of_weight": round(in_com_w, 3),
        "within_community_share_of_ties": round(in_com_e, 3),
    }


_paper_counts = {}
def links_papers(G):
    return _paper_counts.get(id(G), "")


rows = {}
for name, links in {"all candidates (Keerthana)": aff,
                    "STRICT only (John)": aff[aff.openalex_id.astype(str).isin(strict_ids)]}.items():
    G = build_graph(links)
    _paper_counts[id(G)] = links.openalex_id.nunique()
    rows[name] = summarize(G)

out = pd.DataFrame(rows)
print(out.to_string())
out.to_csv("network_comparison_like_for_like.csv")
print("\nSTRICT ids found in affiliations:",
      len(strict_ids & set(aff.openalex_id.astype(str))), "of", len(strict_ids))
