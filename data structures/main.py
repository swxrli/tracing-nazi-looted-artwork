"""Main program for the Nazi-looted art provenance project."""

import argparse
import json
from pathlib import Path

import pandas as pd

from data_index import DataIndex
from graph import ProvenanceGraph

from algorithms import (
    bfs,
    dfs,
    location_frequency,
    find_provenance_gaps,
    artwork_provenance_summary,
    date_status_distribution
)


# Project folder paths
def get_project_folder():

    return Path(__file__).resolve().parent.parent


def get_data_folder():

    return (
        get_project_folder()
        / "shared data"
        / "data"
        / "processed"
    )


def get_output_folder():

    return get_project_folder() / "outputs"


# Load CSV datasets
def load_datasets(artworks_path=None, statements_path=None):

    data_folder = get_data_folder()

    artworks_path = (
        Path(artworks_path)
        if artworks_path
        else data_folder / "artworks.csv"
    )

    statements_path = (
        Path(statements_path)
        if statements_path
        else data_folder / "provenance_statements.csv"
    )

    if not artworks_path.exists():
        raise FileNotFoundError(
            f"Artworks file not found: {artworks_path}"
        )

    if not statements_path.exists():
        raise FileNotFoundError(
            f"Provenance file not found: {statements_path}"
        )

    print("\nLoading datasets...")

    artworks = pd.read_csv(
        artworks_path,
        low_memory=False
    )

    statements = pd.read_csv(
        statements_path,
        low_memory=False
    )

    return artworks, statements


# Main analysis
def run_analysis(
    artworks_path=None,
    statements_path=None,
    output_dir=None,
    sample_artwork=None
):

    artworks, statements = load_datasets(
        artworks_path,
        statements_path
    )

    out = (
        Path(output_dir)
        if output_dir
        else get_output_folder()
    )

    out.mkdir(parents=True, exist_ok=True)

    print("\n==========================================")
    print(" NAZI-LOOTED ART PROVENANCE PROJECT")
    print("==========================================")

    print(f"Total artworks: {len(artworks):,}")
    print(f"Total statements: {len(statements):,}")

    # Build hash and date indexes
    print("\nBuilding data indexes...")

    index = DataIndex(
        artworks,
        statements
    )

    index.display_statistics()

    if not index.validate_indexes():
        raise RuntimeError("Index validation failed")

    # Build provenance graph
    print("\nBuilding provenance graph...")

    graph = ProvenanceGraph().build(
        artworks,
        statements
    )

    graph.display_statistics()

    # Provenance completeness analysis
    print("\nAnalyzing provenance date completeness...")

    gaps = pd.DataFrame(
        find_provenance_gaps(index)
    )

    gaps.to_csv(
        out / "provenance_date_completeness.csv",
        index=False
    )

    # Location frequency analysis
    print("Analyzing locations...")

    locations = pd.DataFrame(
        location_frequency(index),
        columns=[
            "location",
            "distinct_artworks"
        ]
    )

    locations.to_csv(
        out / "location_frequency.csv",
        index=False
    )

    # Date status distribution
    distribution = date_status_distribution(
        statements.to_dict("records")
    )

    pd.DataFrame(
        distribution.items(),
        columns=[
            "date_status",
            "statement_count"
        ]
    ).to_csv(
        out / "date_status_distribution.csv",
        index=False
    )

    # Individual artwork provenance
    if sample_artwork:
        aid = str(sample_artwork)
    elif len(artworks):
        aid = str(artworks.iloc[0]["artwork_id"])
    else:
        aid = None

    summary = (
        artwork_provenance_summary(index, aid)
        if aid
        else None
    )

    if summary:

        with open(
            out / "sample_artwork_provenance.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                summary,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        print("\n===== SAMPLE ARTWORK =====")

        print("Artwork ID:", aid)
        print("Title:", summary.get("title"))
        print("Artist:", summary.get("artist"))
        print(
            "Total statements:",
            summary["total_statements"]
        )

        print(
            "Recorded locations:",
            graph.get_artwork_locations(aid)
        )

        print(
            "Recorded sources:",
            graph.get_artwork_sources(aid)
        )

        # BFS and DFS
        start_node = f"ART:{aid}"

        bfs_result = bfs(graph, start_node)
        dfs_result = dfs(graph, start_node)

        print(
            "\nBFS traversal nodes:",
            len(bfs_result)
        )

        print(
            "DFS traversal nodes:",
            len(dfs_result)
        )

        print(
            "Other artworks sharing locations:",
            len(graph.get_related_artworks(aid))
        )

    # Project summary
    artwork_ids_with_statements = set(
        statements["artwork_id"]
        .dropna()
        .astype(str)
    )

    artwork_ids = (
        artworks["artwork_id"]
        .dropna()
        .astype(str)
    )

    summary_stats = {

        "artworks_rows": len(artworks),

        "statements_rows": len(statements),

        "artwork_ids_without_statements": int(
            (~artwork_ids.isin(artwork_ids_with_statements)).sum()
        ),

        "index_statistics": index.statistics(),

        "graph_nodes": graph.number_of_nodes(),

        "graph_edges": graph.number_of_edges(),

        "graph_node_types": graph.count_node_types(),

        "graph_edge_types": graph.count_edge_types(),

        "date_completeness_categories":
            gaps["date_completeness"].value_counts().to_dict(),

        "top_15_locations":
            location_frequency(index)[:15],

        "interpretation_note":
            "Recorded associations are not proof of ownership, "
            "transfer, or physical presence."
    }

    with open(
        out / "project_summary.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary_stats,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    # Display top locations
    print("\n===== TOP 10 RECORDED LOCATIONS =====")

    for location, count in location_frequency(index)[:10]:

        print(f"{location}: {count:,}")

    print("\n==========================================")
    print(" ANALYSIS COMPLETED SUCCESSFULLY")
    print("==========================================")

    print("Output folder:", out.resolve())

    return index, graph, summary_stats


# Command-line execution
def main():

    parser = argparse.ArgumentParser(
        description="Nazi-looted art provenance analysis"
    )

    parser.add_argument(
        "--artworks",
        help="Optional path to artworks.csv"
    )

    parser.add_argument(
        "--statements",
        help="Optional path to provenance_statements.csv"
    )

    parser.add_argument(
        "--output",
        help="Optional output directory"
    )

    parser.add_argument(
        "--artwork-id",
        help="Artwork ID for an individual provenance report"
    )

    args = parser.parse_args()

    run_analysis(
        args.artworks,
        args.statements,
        args.output,
        args.artwork_id
    )


if __name__ == "__main__":
    main()