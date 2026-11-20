from pathlib import Path

import pandas as pd


def main() -> None:
    project_root = Path(__file__).resolve().parent
    processed_dir = project_root / "data" / "processed"
    deliverables_dir = processed_dir / "deliverables"
    deliverables_dir.mkdir(parents=True, exist_ok=True)

    all_df = pd.read_csv(processed_dir / "openalex_eu_candidates.csv")
    strict_df = pd.read_csv(processed_dir / "strict_scopus_provisional.csv")
    yearly = pd.read_csv(processed_dir / "all_vs_strict_by_year.csv")
    country_df = pd.read_csv(processed_dir / "publication_counts_by_country.csv")
    institution_df = pd.read_csv(processed_dir / "eu_institution_paper_counts.csv")

    total_all = len(all_df)
    total_strict = len(strict_df)
    strict_share = total_strict / total_all if total_all else 0.0

    top_countries = country_df.head(10).copy()
    top_institutions = institution_df.head(10).copy()
    top_venues = strict_df["venue"].value_counts().head(10).reset_index()
    top_venues.columns = ["venue", "count"]

    summary = {
        "metric": [
            "all_candidates_total",
            "strict_provisional_total",
            "strict_retention_rate",
            "yearly_total_records",
            "top_country_1",
            "top_country_1_count",
            "top_institution_1",
            "top_institution_1_count",
            "top_venue_1",
            "top_venue_1_count",
        ],
        "value": [
            total_all,
            total_strict,
            f"{strict_share:.1%}",
            int(yearly["ALL_candidates"].sum()),
            top_countries.iloc[0]["country"],
            int(top_countries.iloc[0]["paper_count"]),
            top_institutions.iloc[0]["institution"],
            int(top_institutions.iloc[0]["paper_count"]),
            top_venues.iloc[0]["venue"],
            int(top_venues.iloc[0]["count"]),
        ],
    }

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(deliverables_dir / "final_project_summary.csv", index=False)

    print("Project D final summary")
    print("=" * 40)
    print(f"ALL candidates: {total_all:,}")
    print(f"STRICT provisional: {total_strict:,}")
    print(f"Retention: {strict_share:.1%}")
    print()
    print("Top countries:")
    print(top_countries.to_string(index=False))
    print()
    print("Top institutions:")
    print(top_institutions.to_string(index=False))
    print()
    print("Top venues:")
    print(top_venues.to_string(index=False))
    print()
    print(f"Saved: {deliverables_dir / 'final_project_summary.csv'}")


if __name__ == "__main__":
    main()
