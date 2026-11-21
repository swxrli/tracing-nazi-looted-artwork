import csv
import json
import os
import re
from datetime import datetime


# ============================================================
# PROJECT PATHS
# ============================================================

# prepare_data.py is inside:
#
# College mini project/
# └── shared data/
#     └── python/
#         └── prepare_data.py
#
# Therefore BASE_DIR points to:
# College mini project/shared data/

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RAW_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "err_records_raw.json"
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

ARTWORKS_PATH = os.path.join(
    PROCESSED_DIR,
    "artworks.csv"
)

STATEMENTS_PATH = os.path.join(
    PROCESSED_DIR,
    "provenance_statements.csv"
)


# ============================================================
# ERR RECORD-LEVEL FIELDS
# ============================================================

SINGLE_FIELDS = [
    "Owner",
    "Collection",
    "Inventory No.",
    "Artist",
    "Medium",
    "Title",
    "Description",
    "Literature",
    "Provenance and Comments",
    "Archival Sources",
    "Measurements",
    "Images",
    "Framed?",
    "Signed?",
    "Repatriated to France?",
    "Repatriated to Belgium?",
    "Repatriation date",
    "Restituted?",
    "Restitution date",
    "Munich No.",
    "Shipment No.",
    "Slated for destruction?"
]


# ============================================================
# PROVENANCE FIELDS
# ============================================================

STATEMENT_FIELDS = [
    "Intake place",
    "Intake date",
    "Transfer place",
    "Transfer date"
]


# ============================================================
# DATE CLASSIFICATION
# ============================================================

def classify_date(value):
    """
    Classify an ERR date without changing the original
    source value.

    Examples:

        1942-11-05
        -> documented_dated

        1940-07-00
        -> documented_partial_date

        1941-00-00
        -> documented_partial_date

        1940-15-10
        -> invalid_source_date
    """

    if not value:
        return "not_applicable"

    value = value.strip()

    # Standard ERR format:
    # YYYY-MM-DD

    match = re.fullmatch(
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        value
    )

    if not match:
        return "unclassified_source_date"

    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))

    # ERR uses 00 when a month or day is unknown.
    if month == 0 or day == 0:
        return "documented_partial_date"

    # Check whether it is a valid calendar date.
    try:

        datetime(
            year,
            month,
            day
        )

        return "documented_dated"

    except ValueError:

        return "invalid_source_date"


# ============================================================
# NORMALIZE DUPLICATED DATE TEXT
# ============================================================

def normalize_date_value(value):
    """
    Normalize obvious duplicated date extraction while
    preserving the original source value separately.

    Example:

        1943-11-26943-11-26
        -> 1943-11-26

    A value is only changed when it is exactly the same
    valid YYYY-MM-DD string repeated twice.
    """

    if not value:
        return ""

    value = value.strip()

    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2})\1",
        value
    )

    if match:
        return match.group(1)

    return value


# ============================================================
# LOAD RAW JSON
# ============================================================

def load_raw_data():

    print("=" * 80)
    print("LOADING ERR RAW DATA")
    print("=" * 80)
    print()

    if not os.path.exists(RAW_PATH):

        raise FileNotFoundError(
            "Could not find the raw ERR dataset:\n"
            f"{RAW_PATH}"
        )

    with open(
        RAW_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    records = data.get(
        "records",
        []
    )

    print(
        f"Records found: {len(records):,}"
    )

    return data, records


# ============================================================
# CONVERT ORDERED FIELD LIST TO DICTIONARY
# ============================================================

def fields_to_dict(fields):
    """
    Convert:

        [
            {"field": "Owner", "value": "..."},
            {"field": "Transfer place", "value": "..."},
            {"field": "Transfer place", "value": "..."}
        ]

    into:

        {
            "Owner": ["..."],
            "Transfer place": ["...", "..."]
        }

    Repeated fields are preserved.
    """

    result = {}

    for item in fields:

        field = item.get(
            "field",
            ""
        ).strip()

        value = item.get(
            "value",
            ""
        )

        if field not in result:
            result[field] = []

        result[field].append(
            value
        )

    return result


# ============================================================
# MAKE CSV COLUMN NAME
# ============================================================

def make_column_name(field):

    return (
        field.lower()
        .replace(" ", "_")
        .replace("?", "")
        .replace(".", "")
        .replace("/", "_")
    )


# ============================================================
# JOIN REPEATED VALUES
# ============================================================

def joined_values(
    field_dict,
    field_name
):

    values = field_dict.get(
        field_name,
        []
    )

    cleaned = [
        value.strip()
        for value in values
        if value.strip()
    ]

    return " | ".join(
        cleaned
    )


# ============================================================
# CREATE ARTWORKS CSV
# ============================================================

def create_artworks_table(records):

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    columns = [
        "artwork_id",
        "record_number",
        "card_id",
        "source_name",
        "source_url"
    ]

    columns.extend([
        make_column_name(field)
        for field in SINGLE_FIELDS
    ])

    with open(
        ARTWORKS_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()

        for record in records:

            fields = fields_to_dict(
                record.get(
                    "fields",
                    []
                )
            )

            record_number = record.get(
                "record_number"
            )

            card_id = record.get(
                "card_id",
                ""
            )

            artwork_id = (
                f"ERR-{int(record_number):05d}"
            )

            row = {
                "artwork_id": artwork_id,
                "record_number": record_number,
                "card_id": card_id,
                "source_name": (
                    "ERR Jeu de Paume"
                ),
                "source_url": record.get(
                    "source_url",
                    ""
                )
            }

            for field in SINGLE_FIELDS:

                column = make_column_name(
                    field
                )

                row[column] = joined_values(
                    fields,
                    field
                )

            writer.writerow(
                row
            )

    print(
        f"Created: {ARTWORKS_PATH}"
    )


# ============================================================
# CREATE PROVENANCE STATEMENTS CSV
# ============================================================

def create_statement_table(records):

    statement_rows = []

    statement_counter = 1

    for record in records:

        record_number = record.get(
            "record_number"
        )

        artwork_id = (
            f"ERR-{int(record_number):05d}"
        )

        card_id = record.get(
            "card_id",
            ""
        )

        source_url = record.get(
            "source_url",
            ""
        )

        fields = record.get(
            "fields",
            []
        )

        # Preserve the ORIGINAL field order from ERR.
        for source_sequence_number, item in enumerate(
            fields,
            start=1
        ):

            field = item.get(
                "field",
                ""
            ).strip()

            raw_value = item.get(
                "value",
                ""
            ).strip()

            # We only create provenance statements for
            # explicit intake/transfer fields.
            if field not in STATEMENT_FIELDS:
                continue

            if not raw_value:
                continue

            # ------------------------------------------------
            # DATE STATEMENTS
            # ------------------------------------------------

            if field in [
                "Intake date",
                "Transfer date"
            ]:

                date_status = classify_date(
                    raw_value
                )

                normalized_value = (
                    normalize_date_value(
                        raw_value
                    )
                )

                date_association_status = (
                    "standalone_source_date"
                )

            # ------------------------------------------------
            # PLACE STATEMENTS
            # ------------------------------------------------

            else:

                date_status = (
                    "not_applicable"
                )

                normalized_value = ""

                date_association_status = (
                    "not_explicitly_associated"
                )

            statement_rows.append({

                "statement_id": (
                    f"PS-{statement_counter:06d}"
                ),

                "artwork_id": artwork_id,

                "record_number": record_number,

                "card_id": card_id,

                "source_name": (
                    "ERR Jeu de Paume"
                ),

                "source_url": source_url,

                "statement_type": field,

                "statement_value_raw": raw_value,

                "normalized_date": (
                    normalized_value
                    if field in [
                        "Intake date",
                        "Transfer date"
                    ]
                    else ""
                ),

                "source_sequence_number": (
                    source_sequence_number
                ),

                "date_status": date_status,

                "date_association_status": (
                    date_association_status
                )
            })

            statement_counter += 1

    columns = [
        "statement_id",
        "artwork_id",
        "record_number",
        "card_id",
        "source_name",
        "source_url",
        "statement_type",
        "statement_value_raw",
        "normalized_date",
        "source_sequence_number",
        "date_status",
        "date_association_status"
    ]

    with open(
        STATEMENTS_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()

        writer.writerows(
            statement_rows
        )

    print(
        f"Created: {STATEMENTS_PATH}"
    )

    return statement_rows


# ============================================================
# FIND UNUSUAL DATE VALUES
# ============================================================

def find_problem_dates(records):

    print()
    print("=" * 80)
    print("UNUSUAL DATE VALUES")
    print("=" * 80)
    print()

    found = []

    for record in records:

        for item in record.get(
            "fields",
            []
        ):

            field = item.get(
                "field",
                ""
            ).strip()

            value = item.get(
                "value",
                ""
            ).strip()

            if field not in [
                "Intake date",
                "Transfer date"
            ]:
                continue

            if not value:
                continue

            status = classify_date(
                value
            )

            if status in [
                "invalid_source_date",
                "unclassified_source_date"
            ]:

                normalized = normalize_date_value(
                    value
                )

                found.append({

                    "record_number": record.get(
                        "record_number"
                    ),

                    "card_id": record.get(
                        "card_id"
                    ),

                    "field": field,

                    "value": value,

                    "normalized": normalized,

                    "status": status
                })

    if not found:

        print(
            "No unusual date values found."
        )

    else:

        for item in found:

            print(
                f"Record {item['record_number']} | "
                f"CardId {item['card_id']} | "
                f"{item['field']} | "
                f"{item['value']} | "
                f"{item['status']}"
            )

            if (
                item["normalized"]
                != item["value"]
            ):

                print(
                    f"    Normalized: "
                    f"{item['normalized']}"
                )

    print()

    print(
        f"Problematic date values found: "
        f"{len(found)}"
    )


# ============================================================
# VALIDATE OUTPUT
# ============================================================

def validate_output(
    records,
    statements
):

    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    # Expected artwork rows
    expected_artworks = len(
        records
    )

    # Check artwork CSV count
    actual_artworks = 0

    with open(
        ARTWORKS_PATH,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        for _ in reader:
            actual_artworks += 1

    print(
        f"Artwork rows expected: "
        f"{expected_artworks:,}"
    )

    print(
        f"Artwork rows created:  "
        f"{actual_artworks:,}"
    )

    if actual_artworks != expected_artworks:

        raise RuntimeError(
            "Artwork row count does not match "
            "the raw ERR record count."
        )

    # Check statement IDs
    statement_ids = [
        row["statement_id"]
        for row in statements
    ]

    unique_statement_ids = set(
        statement_ids
    )

    print(
        f"Statement rows created: "
        f"{len(statement_ids):,}"
    )

    print(
        f"Unique statement IDs:    "
        f"{len(unique_statement_ids):,}"
    )

    if len(statement_ids) != len(
        unique_statement_ids
    ):

        raise RuntimeError(
            "Duplicate statement IDs detected."
        )

    # Check output files
    if not os.path.exists(
        ARTWORKS_PATH
    ):

        raise RuntimeError(
            "artworks.csv was not created."
        )

    if not os.path.exists(
        STATEMENTS_PATH
    ):

        raise RuntimeError(
            "provenance_statements.csv was not created."
        )

    print()
    print(
        "Validation passed."
    )


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(
    records,
    statements
):

    print()
    print("=" * 80)
    print("PREPARATION COMPLETE")
    print("=" * 80)
    print()

    print(
        f"ERR records: "
        f"{len(records):,}"
    )

    print(
        f"Provenance statements: "
        f"{len(statements):,}"
    )

    print()

    complete_dates = sum(
        1
        for row in statements
        if row["date_status"]
        == "documented_dated"
    )

    partial_dates = sum(
        1
        for row in statements
        if row["date_status"]
        == "documented_partial_date"
    )

    invalid_dates = sum(
        1
        for row in statements
        if row["date_status"]
        == "invalid_source_date"
    )

    unclassified_dates = sum(
        1
        for row in statements
        if row["date_status"]
        == "unclassified_source_date"
    )

    print(
        f"Complete dates: "
        f"{complete_dates:,}"
    )

    print(
        f"Partial dates: "
        f"{partial_dates:,}"
    )

    print(
        f"Invalid source dates: "
        f"{invalid_dates:,}"
    )

    print(
        f"Unclassified source dates: "
        f"{unclassified_dates:,}"
    )

    print()

    print(
        f"Artworks CSV:"
    )

    print(
        ARTWORKS_PATH
    )

    print()

    print(
        f"Statements CSV:"
    )

    print(
        STATEMENTS_PATH
    )


# ============================================================
# MAIN
# ============================================================

def main():

    data, records = load_raw_data()

    if not records:

        raise RuntimeError(
            "No ERR records were found."
        )

    # --------------------------------------------------------
    # Create canonical artwork table
    # --------------------------------------------------------

    create_artworks_table(
        records
    )

    # --------------------------------------------------------
    # Create provenance statement table
    # --------------------------------------------------------

    statements = create_statement_table(
        records
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_output(
        records,
        statements
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print_summary(
        records,
        statements
    )

    # --------------------------------------------------------
    # Inspect unusual dates
    # --------------------------------------------------------

    find_problem_dates(
        records
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()