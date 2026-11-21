
"""Unit tests for the provenance project."""

import unittest
import pandas as pd

from data_index import DataIndex
from graph import ProvenanceGraph

from algorithms import (
    bfs,
    dfs,
    connected_artworks,
    find_provenance_gaps
)


class ProjectTests(unittest.TestCase):

    def setUp(self):

        # Sample artwork dataset
        self.artworks = pd.DataFrame([
            {
                "artwork_id": "A1",
                "title": "Work 1",
                "artist": "Artist",
                "owner": "Owner X"
            },
            {
                "artwork_id": "A2",
                "title": "Work 2",
                "artist": "Artist",
                "owner": "Owner Y"
            },
            {
                "artwork_id": "A3",
                "title": "Work 3",
                "artist": "Other",
                "owner": None
            }
        ])

        # Sample provenance statements
        self.statements = pd.DataFrame([
            {
                "statement_id": "S1",
                "artwork_id": "A1",
                "statement_type": "Intake place",
                "statement_value_raw": "Paris",
                "source_name": "Archive",
                "normalized_date": "1941-01-01",
                "date_status": "documented_dated"
            },
            {
                "statement_id": "S2",
                "artwork_id": "A1",
                "statement_type": "Transfer date",
                "statement_value_raw": None,
                "source_name": "Archive",
                "normalized_date": "1942-00-00",
                "date_status": "documented_partial_date"
            },
            {
                "statement_id": "S3",
                "artwork_id": "A2",
                "statement_type": "Transfer place",
                "statement_value_raw": "Paris",
                "source_name": "Archive",
                "normalized_date": None,
                "date_status": "not_applicable"
            }
        ])

        # Build data index
        self.index = DataIndex(
            self.artworks,
            self.statements
        )

        # Build provenance graph
        self.graph = ProvenanceGraph().build(
            self.artworks,
            self.statements
        )

    # TEST 1: Artwork hash index
    def test_hash_and_inverted_indexes(self):

        self.assertEqual(
            self.index.get_artwork("A1")["title"],
            "Work 1"
        )

        self.assertEqual(
            len(self.index.get_statements("A1")),
            2
        )

        self.assertEqual(
            self.index.get_artist_artworks("artist"),
            ["A1", "A2"]
        )

        self.assertEqual(
            self.index.get_location_artworks("PARIS"),
            ["A1", "A2"]
        )

    # TEST 2: Date range search
    def test_date_search(self):

        result = self.index.search_date_range(
            "1941-01-01",
            "1941-12-31"
        )

        self.assertEqual(len(result), 1)

        self.assertEqual(
            len(self.index.partial_date_index),
            1
        )

        with self.assertRaises(ValueError):

            self.index.search_date_range(
                "1942-01-01",
                "1941-01-01"
            )

    # TEST 3: Graph and traversal
    def test_graph_and_traversals(self):

        self.assertEqual(
            self.graph.get_related_artworks("A1"),
            ["A2"]
        )

        self.assertEqual(
            set(bfs(self.graph, "ART:A1")),
            set(dfs(self.graph, "ART:A1"))
        )

        self.assertEqual(
            connected_artworks(self.graph, "A1"),
            ["A2"]
        )

    # TEST 4: Provenance gaps
    def test_provenance_gaps(self):

        gaps = {
            row["artwork_id"]: row
            for row in find_provenance_gaps(self.index)
        }

        self.assertEqual(len(gaps), 3)

        self.assertEqual(
            gaps["A3"]["date_completeness"],
            "No provenance statements"
        )

    # TEST 5: Index validation
    def test_index_validation(self):

        self.assertTrue(
            self.index.validate_indexes()
        )

    # TEST 6: BFS should not expand shared locations
    def test_bfs_does_not_expand_shared_locations(self):

        result = bfs(
            self.graph,
            "ART:A1"
        )

        # Artwork A1 should be included
        self.assertIn("ART:A1", result)

        # Its provenance statements should be included
        self.assertIn("STMT:S1", result)
        self.assertIn("STMT:S2", result)

        # Artwork A2 must not be reached through shared Paris location
        self.assertNotIn("ART:A2", result)

        # Paris should be included as a terminal node
        self.assertIn("LOC:paris", result)

    # TEST 7: DFS should not expand shared locations
    def test_dfs_does_not_expand_shared_locations(self):

        result = dfs(
            self.graph,
            "ART:A1"
        )

        self.assertIn("ART:A1", result)

        self.assertIn("STMT:S1", result)
        self.assertIn("STMT:S2", result)

        self.assertNotIn("ART:A2", result)

        self.assertIn("LOC:paris", result)


if __name__ == "__main__":

    unittest.main(verbosity=2)
