"""Graph representation of artwork provenance records."""

from collections import defaultdict, Counter
from bisect import bisect_left, bisect_right
from datetime import date
import pandas as pd


class ProvenanceGraph:

    def __init__(self):

        self.adjacency = defaultdict(set)
        self.node_data = {}
        self.edge_data = {}

        self.edge_type_index = defaultdict(set)
        self.node_type_counts = Counter()
        self.edge_type_counts = Counter()

        self.location_artworks = defaultdict(set)
        self.source_artworks = defaultdict(set)
        self.source_statements = defaultdict(set)

        self.artwork_statements = defaultdict(list)
        self.artwork_locations = defaultdict(set)
        self.artwork_sources = defaultdict(set)
        self.artwork_owners = defaultdict(set)

        self.date_index = []
        self.sorted_dates = []

    @staticmethod
    def clean(value):

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        value = str(value).strip()

        if value.casefold() in {"", "nan", "none", "null"}:
            return None

        return value

    def add_node(self, node_id, node_type, **attributes):

        if node_id in self.node_data:
            return False

        self.adjacency[node_id]

        self.node_data[node_id] = {
            "node_type": node_type,
            **attributes
        }

        self.node_type_counts[node_type] += 1

        return True

    def add_edge(self, source, target, relationship, **attributes):

        if source not in self.node_data or target not in self.node_data:
            raise ValueError("Both edge endpoints must exist")

        edge = tuple(sorted((source, target))) + (relationship,)

        if edge in self.edge_data:
            return False

        self.adjacency[source].add(target)
        self.adjacency[target].add(source)

        self.edge_data[edge] = {
            "relationship": relationship,
            **attributes
        }

        self.edge_type_index[relationship].add(edge)
        self.edge_type_counts[relationship] += 1

        return True

    def build(self, artworks, statements):

        # Create artwork and owner nodes
        for row in artworks.to_dict("records"):

            aid = self.clean(row.get("artwork_id"))

            if not aid:
                continue

            artwork_node = f"ART:{aid}"

            self.add_node(
                artwork_node,
                "artwork",
                **{
                    key: self.clean(row.get(key))
                    for key in (
                        "artwork_id",
                        "title",
                        "artist",
                        "owner",
                        "collection",
                        "medium",
                        "inventory_no",
                        "source_name",
                        "source_url"
                    )
                }
            )

            owner = self.clean(row.get("owner"))

            if owner:

                owner_node = f"OWN:{owner.casefold()}"

                self.add_node(
                    owner_node,
                    "recorded_owner",
                    name=owner
                )

                self.add_edge(
                    artwork_node,
                    owner_node,
                    "owner_recorded_on_artwork"
                )

                self.artwork_owners[aid].add(owner)

        # Create provenance statement nodes
        for row in statements.to_dict("records"):

            aid = self.clean(row.get("artwork_id"))
            sid = self.clean(row.get("statement_id"))

            if not aid or not sid:
                continue

            artwork_node = f"ART:{aid}"

            if artwork_node not in self.node_data:
                continue

            statement_node = f"STMT:{sid}"

            if statement_node in self.node_data:
                raise ValueError(f"Duplicate statement ID: {sid}")

            statement_type = self.clean(row.get("statement_type"))
            value = self.clean(row.get("statement_value_raw"))
            source = self.clean(row.get("source_name"))
            normalized_date = self.clean(row.get("normalized_date"))
            date_status = self.clean(row.get("date_status"))

            self.add_node(
                statement_node,
                "statement",
                statement_id=sid,
                artwork_id=aid,
                statement_type=statement_type,
                value=value,
                normalized_date=normalized_date,
                date_status=date_status,
                date_association_status=self.clean(
                    row.get("date_association_status")
                ),
                source_name=source,
                source_url=self.clean(row.get("source_url")),
                source_sequence_number=self.clean(
                    row.get("source_sequence_number")
                )
            )

            self.add_edge(
                artwork_node,
                statement_node,
                "has_statement"
            )

            self.artwork_statements[aid].append(sid)

            # Location nodes
            if statement_type in {"Intake place", "Transfer place"} and value:

                key = value.casefold()
                location_node = f"LOC:{key}"

                self.add_node(
                    location_node,
                    "location",
                    name=value
                )

                self.add_edge(
                    statement_node,
                    location_node,
                    "records_location"
                )

                self.location_artworks[key].add(aid)
                self.artwork_locations[aid].add(value)

            # Documentary source nodes
            if source:

                key = source.casefold()
                source_node = f"SRC:{key}"

                self.add_node(
                    source_node,
                    "documentary_source",
                    name=source
                )

                self.add_edge(
                    statement_node,
                    source_node,
                    "documented_by"
                )

                self.source_artworks[key].add(aid)
                self.source_statements[key].add(sid)
                self.artwork_sources[aid].add(source)

            # Complete dates only
            if normalized_date and date_status == "documented_dated":

                try:
                    parsed = date.fromisoformat(normalized_date)

                    self.date_index.append(
                        (parsed, sid, aid)
                    )

                except ValueError:
                    pass

        self.date_index.sort()

        self.sorted_dates = [
            item[0] for item in self.date_index
        ]

        return self

    # Basic graph methods

    def get_neighbours(self, node):
        return self.adjacency.get(node, set())

    def number_of_nodes(self):
        return len(self.node_data)

    def number_of_edges(self):
        return len(self.edge_data)

    def count_node_types(self):
        return dict(self.node_type_counts)

    def count_edge_types(self):
        return dict(self.edge_type_counts)

    def get_node(self, node_id):
        return self.node_data.get(node_id)

    # Artwork searches

    def get_artwork_locations(self, artwork_id):
        return sorted(
            self.artwork_locations.get(artwork_id, set())
        )

    def get_artwork_sources(self, artwork_id):
        return sorted(
            self.artwork_sources.get(artwork_id, set())
        )

    def get_artwork_statements(self, artwork_id):

        return [
            self.node_data[f"STMT:{sid}"]
            for sid in self.artwork_statements.get(artwork_id, [])
            if f"STMT:{sid}" in self.node_data
        ]

    def get_location_artworks(self, location):

        value = self.clean(location)

        if not value:
            return []

        return sorted(
            self.location_artworks.get(value.casefold(), set())
        )

    def get_source_artworks(self, source):

        value = self.clean(source)

        if not value:
            return []

        return sorted(
            self.source_artworks.get(value.casefold(), set())
        )

    def get_source_statements(self, source):

        value = self.clean(source)

        if not value:
            return []

        return sorted(
            self.source_statements.get(value.casefold(), set())
        )

    # Chronological provenance

    def get_chronological_provenance(self, artwork_id):

        rows = self.get_artwork_statements(artwork_id)

        rows = [
            row for row in rows
            if row.get("normalized_date")
            and row.get("date_status") == "documented_dated"
        ]

        return sorted(
            rows,
            key=lambda row: (
                row["normalized_date"],
                str(row.get("source_sequence_number") or ""),
                row["statement_id"]
            )
        )

    # Binary date search

    def search_date_range(self, start_date, end_date):

        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))

        if start > end:
            raise ValueError("Start date cannot exceed end date")

        left = bisect_left(self.sorted_dates, start)
        right = bisect_right(self.sorted_dates, end)

        return self.date_index[left:right]

    # Related artworks by shared recorded location

    def get_related_artworks(self, artwork_id):

        related = set()

        for location in self.artwork_locations.get(artwork_id, set()):

            related.update(
                self.location_artworks.get(
                    location.casefold(), set()
                )
            )

        related.discard(artwork_id)

        return sorted(related)

    def display_statistics(self):

        print("\n===== PROVENANCE GRAPH STATISTICS =====")

        print(f"Nodes: {self.number_of_nodes():,}")
        print(f"Edges: {self.number_of_edges():,}")

        print("Node types:", self.count_node_types())
        print("Edge types:", self.count_edge_types())