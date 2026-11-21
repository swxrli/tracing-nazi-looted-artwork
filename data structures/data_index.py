"""Hash-table and sorted-list indexes for provenance records."""

from collections import defaultdict
from bisect import bisect_left, bisect_right
from datetime import date
import pandas as pd


class DataIndex:

    def __init__(self, artworks, statements):
        self.artwork_index = {}
        self.statement_index = {}

        self.artwork_statements = defaultdict(list)

        self.location_index = defaultdict(set)
        self.artist_index = defaultdict(set)
        self.owner_index = defaultdict(set)
        self.statement_type_index = defaultdict(set)
        self.source_index = defaultdict(set)
        self.date_status_index = defaultdict(set)

        self.date_index = []
        self.partial_date_index = []

        self.sorted_dates = []
        self.sorted_partial_dates = []

        self.orphan_statements = set()
        self.invalid_date_statements = set()
        self.unclassified_date_statements = set()
        self.missing_date_statements = set()

        self.build_indexes(artworks, statements)

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

    @staticmethod
    def classify_date(value, status):

        if not value:
            return "missing"

        if status == "documented_dated":
            try:
                date.fromisoformat(value)
                return "complete"
            except ValueError:
                return "invalid"

        if status == "documented_partial_date":
            parts = value.split("-")

            if len(parts) != 3:
                return "invalid"

            try:
                year, month, day = map(int, parts)

                if year < 1 or not 0 <= month <= 12 or not 0 <= day <= 31:
                    return "invalid"

                if month == 0 and day != 0:
                    return "invalid"

                if month != 0 and day == 0:
                    return "partial"

                if month == 0 and day == 0:
                    return "partial"

                date(year, month, day)
                return "complete"

            except ValueError:
                return "invalid"

        if status == "invalid_source_date":
            return "invalid"

        if status == "unclassified_source_date":
            return "unclassified"

        if status == "not_applicable":
            return "not_applicable"

        return "unclassified"

    def build_indexes(self, artworks, statements):

        # Artwork hash index
        for row in artworks.to_dict("records"):

            aid = self.clean(row.get("artwork_id"))

            if not aid:
                continue

            if aid in self.artwork_index:
                raise ValueError(f"Duplicate artwork ID: {aid}")

            self.artwork_index[aid] = row

            artist = self.clean(row.get("artist"))
            owner = self.clean(row.get("owner"))

            if artist:
                self.artist_index[artist.casefold()].add(aid)

            if owner:
                self.owner_index[owner.casefold()].add(aid)

        # Provenance statement indexes
        for row in statements.to_dict("records"):

            sid = self.clean(row.get("statement_id"))
            aid = self.clean(row.get("artwork_id"))

            if not sid:
                continue

            if sid in self.statement_index:
                raise ValueError(f"Duplicate statement ID: {sid}")

            self.statement_index[sid] = row

            if aid not in self.artwork_index:
                self.orphan_statements.add(sid)
                continue

            self.artwork_statements[aid].append(sid)

            stype = self.clean(row.get("statement_type"))

            if stype:
                self.statement_type_index[stype.casefold()].add(aid)

            if stype in {"Intake place", "Transfer place"}:

                location = self.clean(row.get("statement_value_raw"))

                if location:
                    self.location_index[location.casefold()].add(aid)

            source = self.clean(row.get("source_name"))

            if source:
                self.source_index[source.casefold()].add(aid)

            status = self.clean(row.get("date_status"))
            value = self.clean(row.get("normalized_date"))

            if status:
                self.date_status_index[status].add(sid)

            classification = self.classify_date(value, status)

            if classification == "complete":
                try:
                    parsed = date.fromisoformat(value)
                    self.date_index.append((parsed, sid))
                except ValueError:
                    self.invalid_date_statements.add(sid)

            elif classification == "partial":
                self.partial_date_index.append((value, sid))

            elif classification == "invalid":
                self.invalid_date_statements.add(sid)

            elif classification == "unclassified":
                self.unclassified_date_statements.add(sid)

            elif classification == "missing":
                self.missing_date_statements.add(sid)

        self.date_index.sort()
        self.sorted_dates = [item[0] for item in self.date_index]

        self.partial_date_index.sort()
        self.sorted_partial_dates = [
            item[0] for item in self.partial_date_index
        ]

    # Artwork and statement searches

    def get_artwork(self, artwork_id):
        return self.artwork_index.get(self.clean(artwork_id))

    def get_statement(self, statement_id):
        return self.statement_index.get(self.clean(statement_id))

    def get_statements(self, artwork_id):

        aid = self.clean(artwork_id)

        return [
            self.statement_index[sid]
            for sid in self.artwork_statements.get(aid, [])
        ]

    def _lookup(self, index, value):

        value = self.clean(value)

        if not value:
            return []

        return sorted(index.get(value.casefold(), set()))

    def get_location_artworks(self, location):
        return self._lookup(self.location_index, location)

    def get_artist_artworks(self, artist):
        return self._lookup(self.artist_index, artist)

    def get_owner_artworks(self, owner):
        return self._lookup(self.owner_index, owner)

    def get_source_artworks(self, source):
        return self._lookup(self.source_index, source)

    def get_statement_type_artworks(self, statement_type):
        return self._lookup(self.statement_type_index, statement_type)

    # Binary search for date ranges

    def search_date_range(self, start_date, end_date):

        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))

        if start > end:
            raise ValueError("Start date cannot exceed end date")

        left = bisect_left(self.sorted_dates, start)
        right = bisect_right(self.sorted_dates, end)

        return self.date_index[left:right]

    def get_statements_by_date_status(self, status):
        return sorted(self.date_status_index.get(status, set()))

    # Statistics

    def statistics(self):

        return {
            "artwork_hash_entries": len(self.artwork_index),
            "statement_hash_entries": len(self.statement_index),
            "artwork_statement_links": sum(
                map(len, self.artwork_statements.values())
            ),
            "unique_locations": len(self.location_index),
            "unique_artists": len(self.artist_index),
            "unique_owners": len(self.owner_index),
            "unique_statement_types": len(self.statement_type_index),
            "unique_sources": len(self.source_index),
            "complete_dates": len(self.date_index),
            "partial_dates": len(self.partial_date_index),
            "invalid_dates": len(self.invalid_date_statements),
            "unclassified_dates": len(self.unclassified_date_statements),
            "missing_dates": len(self.missing_date_statements),
            "orphan_statements": len(self.orphan_statements)
        }

    def display_statistics(self):

        print("\n===== DATA INDEX STATISTICS =====")

        for key, value in self.statistics().items():
            print(f"{key.replace('_', ' ').title()}: {value:,}")

    def validate_indexes(self):

        linked = sum(
            map(len, self.artwork_statements.values())
        )

        checks = {
            "all statements linked or classified as orphan":
                linked + len(self.orphan_statements) == len(self.statement_index),

            "complete date index sorted":
                self.sorted_dates == sorted(self.sorted_dates),

            "unique artwork IDs":
                len(self.artwork_index) == len(set(self.artwork_index)),

            "unique statement IDs":
                len(self.statement_index) == len(set(self.statement_index))
        }

        for label, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'}: {label}")

        return all(checks.values())


# Compatibility alias
ProvenanceIndex = DataIndex