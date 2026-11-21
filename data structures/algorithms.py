
"""Searching, graph traversal and provenance analysis algorithms."""

from collections import deque, Counter


# Only artwork and statement nodes can expand the traversal.
# Locations, sources and owners are included as terminal nodes.
EXPANDABLE_NODE_TYPES = {"artwork", "statement"}


def bfs(graph, start, expand_node_types=None):
    """Breadth First Search with controlled graph expansion."""

    if start not in graph.node_data:
        return []

    allowed = (
        EXPANDABLE_NODE_TYPES
        if expand_node_types is None
        else set(expand_node_types)
    )

    visited = {start}
    queue = deque([start])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        node_type = graph.node_data[node].get("node_type")

        # Do not expand shared location/source/owner nodes.
        if node_type not in allowed:
            continue

        for neighbour in sorted(graph.get_neighbours(node)):

            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)

    return order


def dfs(graph, start, expand_node_types=None):
    """Depth First Search with controlled graph expansion."""

    if start not in graph.node_data:
        return []

    allowed = (
        EXPANDABLE_NODE_TYPES
        if expand_node_types is None
        else set(expand_node_types)
    )

    visited = set()
    stack = [start]
    order = []

    while stack:

        node = stack.pop()

        if node in visited:
            continue

        visited.add(node)
        order.append(node)

        node_type = graph.node_data[node].get("node_type")

        if node_type not in allowed:
            continue

        for neighbour in sorted(
            graph.get_neighbours(node),
            reverse=True
        ):

            if neighbour not in visited:
                stack.append(neighbour)

    return order


def connected_artworks(graph, artwork_id):
    """Find other artworks sharing recorded locations."""

    if f"ART:{artwork_id}" not in graph.node_data:
        return []

    return graph.get_related_artworks(artwork_id)


def location_frequency(index):
    """Count distinct artworks associated with each location."""

    display_names = {}

    for row in index.statement_index.values():

        if row.get("statement_type") in {
            "Intake place",
            "Transfer place"
        }:

            value = index.clean(
                row.get("statement_value_raw")
            )

            if value:
                display_names.setdefault(
                    value.casefold(),
                    value
                )

    results = []

    for key, artwork_ids in index.location_index.items():

        results.append((
            display_names.get(key, key),
            len(artwork_ids)
        ))

    return sorted(
        results,
        key=lambda item: (-item[1], item[0].casefold())
    )


def find_provenance_gaps(index):
    """Classify artwork-level provenance date completeness."""

    result = []

    for aid in index.artwork_index:

        statement_ids = index.artwork_statements.get(aid, [])

        records = [
            index.statement_index[sid]
            for sid in statement_ids
        ]

        date_rows = [
            row for row in records
            if row.get("statement_type") in {
                "Intake date",
                "Transfer date"
            }
        ]

        statuses = [
            str(row.get("date_status") or "missing")
            for row in date_rows
        ]

        complete = statuses.count("documented_dated")
        partial = statuses.count("documented_partial_date")
        invalid = statuses.count("invalid_source_date")
        unclassified = statuses.count("unclassified_source_date")

        if not records:
            category = "No provenance statements"

        elif not date_rows:
            category = "No date statements"

        elif complete and (
            partial or invalid or unclassified
        ):
            category = "Complete dates with other date issues"

        elif complete:
            category = "Complete dates only"

        elif partial and not invalid and not unclassified:
            category = "Partial dates only"

        elif invalid or unclassified:
            category = "Invalid or unclassified dates"

        else:
            category = "Other date status"

        result.append({
            "artwork_id": aid,
            "total_statements": len(records),
            "date_statements": len(date_rows),
            "complete_dates": complete,
            "partial_dates": partial,
            "invalid_dates": invalid,
            "unclassified_dates": unclassified,
            "date_completeness": category
        })

    return result


def artwork_provenance_summary(index, artwork_id):
    """Generate a provenance summary for one artwork."""

    artwork = index.get_artwork(artwork_id)

    if artwork is None:
        return None

    rows = index.get_statements(artwork_id)

    return {
        "artwork_id": artwork_id,
        "title": artwork.get("title"),
        "artist": artwork.get("artist"),
        "recorded_owner": artwork.get("owner"),
        "total_statements": len(rows),

        "intake_places": [
            row.get("statement_value_raw")
            for row in rows
            if row.get("statement_type") == "Intake place"
        ],

        "transfer_places": [
            row.get("statement_value_raw")
            for row in rows
            if row.get("statement_type") == "Transfer place"
        ],

        "intake_dates": [
            row.get("normalized_date")
            for row in rows
            if row.get("statement_type") == "Intake date"
        ],

        "transfer_dates": [
            row.get("normalized_date")
            for row in rows
            if row.get("statement_type") == "Transfer date"
        ]
    }


def get_location_statistics(index, location):
    """Return artwork statistics for a recorded location."""

    artwork_ids = index.get_location_artworks(location)

    return {
        "location": location,
        "total_artworks": len(artwork_ids),
        "artwork_ids": artwork_ids
    }


def date_status_distribution(statements):
    """Count statements by date status."""

    counts = Counter(
        str(row.get("date_status") or "missing")
        for row in statements
    )

    return dict(sorted(counts.items()))
