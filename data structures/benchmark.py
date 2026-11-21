"""Performance comparison of data structures and graph algorithms."""

import argparse
import gc
import statistics
import time
import tracemalloc

from pathlib import Path

import pandas as pd

from main import load_datasets, get_output_folder
from data_index import DataIndex
from graph import ProvenanceGraph
from algorithms import bfs, dfs


# Measure execution time
def measure_time(function, repetitions=5):

    samples = []

    for _ in range(repetitions):

        start = time.perf_counter()

        function()

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        samples.append(elapsed)

    return statistics.median(samples)


# Measure peak memory usage
def measure_peak_mb(function):

    gc.collect()

    tracemalloc.start()

    try:

        function()

        current, peak = tracemalloc.get_traced_memory()

    finally:

        tracemalloc.stop()

    return peak / (1024 * 1024)


# Run benchmark experiments
def run_benchmarks(
    artworks_path=None,
    statements_path=None,
    output_dir=None,
    repetitions=5
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

    print("\n======================================")
    print(" PERFORMANCE BENCHMARK")
    print("======================================")

    print(f"Artworks: {len(artworks):,}")
    print(f"Statements: {len(statements):,}")

    results = []

    # 1. Index construction
    print("\n1. Measuring index construction...")

    start = time.perf_counter()

    index = DataIndex(
        artworks,
        statements
    )

    index_build_time = (
        time.perf_counter() - start
    ) * 1000

    index_memory = measure_peak_mb(
        lambda: DataIndex(artworks, statements)
    )

    results.append({
        "experiment": "Index construction",
        "median_time_ms": index_build_time,
        "peak_memory_mb": index_memory,
        "repetitions": 1
    })

    # 2. Linear search vs hash search
    print("2. Comparing linear and hash lookup...")

    target = str(
        artworks.iloc[-1]["artwork_id"]
    )

    records = artworks.to_dict("records")

    def linear_lookup():

        return next(
            (
                row for row in records
                if str(row.get("artwork_id")) == target
            ),
            None
        )

    def hash_lookup():

        return index.get_artwork(target)

    assert linear_lookup() == hash_lookup()

    linear_time = measure_time(
        linear_lookup,
        repetitions
    )

    hash_time = measure_time(
        hash_lookup,
        repetitions
    )

    results.append({
        "experiment": "Linear artwork lookup",
        "median_time_ms": linear_time,
        "peak_memory_mb": None,
        "repetitions": repetitions
    })

    results.append({
        "experiment": "Hash artwork lookup",
        "median_time_ms": hash_time,
        "peak_memory_mb": None,
        "repetitions": repetitions
    })

    # 3. Linear date search vs binary date search
    print("3. Comparing linear and binary date search...")

    start_date = "1940-01-01"
    end_date = "1945-12-31"

    start_d = pd.Timestamp(start_date).date()
    end_d = pd.Timestamp(end_date).date()

    def linear_date_search():

        return [
            item for item in index.date_index
            if start_d <= item[0] <= end_d
        ]

    def binary_date_search():

        return index.search_date_range(
            start_date,
            end_date
        )

    assert linear_date_search() == binary_date_search()

    linear_date_time = measure_time(
        linear_date_search,
        repetitions
    )

    binary_date_time = measure_time(
        binary_date_search,
        repetitions
    )

    results.append({
        "experiment": "Linear date range search",
        "median_time_ms": linear_date_time,
        "peak_memory_mb": None,
        "repetitions": repetitions
    })

    results.append({
        "experiment": "Binary date range search",
        "median_time_ms": binary_date_time,
        "peak_memory_mb": None,
        "repetitions": repetitions
    })

    # 4. Graph construction
    print("4. Measuring graph construction...")

    start = time.perf_counter()

    graph = ProvenanceGraph().build(
        artworks,
        statements
    )

    graph_time = (
        time.perf_counter() - start
    ) * 1000

    results.append({
        "experiment": "Graph construction",
        "median_time_ms": graph_time,
        "peak_memory_mb": None,
        "repetitions": 1
    })

    # 5. BFS vs DFS
    print("5. Comparing BFS and DFS...")

    start_artwork = target

    start_node = f"ART:{start_artwork}"

    if start_node not in graph.node_data:

        start_artwork = str(
            artworks.iloc[0]["artwork_id"]
        )

        start_node = f"ART:{start_artwork}"

    bfs_result = bfs(graph, start_node)
    dfs_result = dfs(graph, start_node)

    assert set(bfs_result) == set(dfs_result)

    bfs_time = measure_time(
        lambda: bfs(graph, start_node),
        repetitions
    )

    dfs_time = measure_time(
        lambda: dfs(graph, start_node),
        repetitions
    )

    results.append({
        "experiment": "BFS traversal",
        "median_time_ms": bfs_time,
        "peak_memory_mb": None,
        "repetitions": repetitions
    })

    results.append({
        "experiment": "DFS traversal",
        "median_time_ms": dfs_time,
        "peak_memory_mb": None,
        "repetitions": repetitions
    })

    # Save results
    dataframe = pd.DataFrame(results)

    dataframe.to_csv(
        out / "performance_results.csv",
        index=False
    )

    print("\n===== BENCHMARK RESULTS =====")

    print(
        dataframe.to_string(index=False)
    )

    print("\nBenchmark completed!")

    print(
        "Results saved to:",
        (out / "performance_results.csv").resolve()
    )

    return dataframe


# Command-line execution
def main():

    parser = argparse.ArgumentParser(
        description="Benchmark provenance data structures"
    )

    parser.add_argument("--artworks")
    parser.add_argument("--statements")
    parser.add_argument("--output")

    parser.add_argument(
        "--repetitions",
        type=int,
        default=5
    )

    args = parser.parse_args()

    if args.repetitions < 1:
        parser.error("Repetitions must be at least 1")

    run_benchmarks(
        args.artworks,
        args.statements,
        args.output,
        args.repetitions
    )


if __name__ == "__main__":
    main()