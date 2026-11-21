import truststore
truststore.inject_into_ssl()

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import local
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURATION
# ============================================================

SEARCH_URL = "https://www.errproject.org/jeudepaume/card_search.php"
SHOW_URL = "https://www.errproject.org/jeudepaume/card_show.php"
CARD_URL = "https://www.errproject.org/jeudepaume/card_view.php"

QUERY = "*"

# Records processed together
BATCH_SIZE = 50

# Number of simultaneous requests
WORKERS = 8

# Small delay inside each worker
REQUEST_DELAY = 0.10

RAW_JSON_PATH = "../data/raw/err_records_raw.json"
CHECKPOINT_PATH = "../data/raw/err_records_checkpoint.jsonl"


# ============================================================
# THREAD-LOCAL SESSIONS
# ============================================================

thread_data = local()


def get_session():
    """
    Give each worker its own requests.Session.
    """
    if not hasattr(thread_data, "session"):

        session = requests.Session()

        retry_strategy = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=1.0,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504
            ],
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy
        )

        session.mount(
            "https://",
            adapter
        )

        session.mount(
            "http://",
            adapter
        )

        session.headers.update({
            "User-Agent": (
                "Art-History-Data/1.0 "
                "(academic provenance research)"
            )
        })

        thread_data.session = session

    return thread_data.session


# ============================================================
# FIND TOTAL NUMBER OF RECORDS
# ============================================================

def get_total_records():

    session = get_session()

    response = session.get(
        SEARCH_URL,
        params={
            "Query": QUERY,
            "StartDoc": 1,
            "MaxPageDocs": 50
        },
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    page_text = soup.get_text(
        " ",
        strip=True
    )

    patterns = [
        r"of\s+([\d,]+)\s+matches",
        r"Total matches:\s*([\d,]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            page_text,
            re.IGNORECASE
        )

        if match:
            return int(
                match.group(1).replace(",", "")
            )

    raise RuntimeError(
        "Could not determine the total ERR record count."
    )


# ============================================================
# GET CARD ID
# ============================================================

def get_card_id(position):

    session = get_session()

    response = session.get(
        SHOW_URL,
        params={
            "Query": QUERY,
            "StartDoc": position,
            "MaxPageDocs": 50
        },
        timeout=30,
        allow_redirects=False
    )

    response.raise_for_status()

    location = response.headers.get(
        "Location"
    )

    if not location:

        raise RuntimeError(
            f"No redirect found at position {position}."
        )

    parsed = urlparse(
        location
    )

    query_data = parse_qs(
        parsed.query
    )

    card_ids = query_data.get(
        "CardId"
    )

    if not card_ids:

        raise RuntimeError(
            f"No CardId found at position {position}."
        )

    time.sleep(
        REQUEST_DELAY
    )

    return card_ids[0]


# ============================================================
# GET ONE CARD
# ============================================================

def get_card_record(
    position,
    card_id
):

    session = get_session()

    response = session.get(
        CARD_URL,
        params={
            "CardId": card_id
        },
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    tables = soup.find_all(
        "table"
    )

    if len(tables) < 2:

        raise RuntimeError(
            f"Unexpected page structure "
            f"for CardId {card_id}."
        )

    table = tables[1]

    fields = []

    for sequence_number, row in enumerate(
        table.find_all("tr"),
        start=1
    ):

        header = row.find("th")
        value = row.find("td")

        if not header:
            continue

        field = header.get_text(
            " ",
            strip=True
        )

        field = field.rstrip(":")

        value_text = ""

        if value:

            value_text = value.get_text(
                " ",
                strip=True
            )

        fields.append({
            "field": field,
            "value": value_text,
            "source_sequence_number": sequence_number
        })

    time.sleep(
        REQUEST_DELAY
    )

    return {
        "record_number": position,
        "card_id": card_id,
        "source_url": (
            f"{CARD_URL}?CardId={card_id}"
        ),
        "fields": fields
    }


# ============================================================
# COUNT CHECKPOINT
# ============================================================

def count_checkpoint_records():

    if not os.path.exists(
        CHECKPOINT_PATH
    ):
        return 0

    count = 0

    with open(
        CHECKPOINT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            if line.strip():
                count += 1

    return count


# ============================================================
# SAVE A BATCH
# ============================================================

def save_batch(records):

    for attempt in range(5):

        try:

            with open(
                CHECKPOINT_PATH,
                "a",
                encoding="utf-8"
            ) as file:

                for record in records:

                    file.write(
                        json.dumps(
                            record,
                            ensure_ascii=False
                        )
                    )

                    file.write(
                        "\n"
                    )

                file.flush()

            return

        except PermissionError:

            if attempt == 4:

                raise

            time.sleep(
                2
            )


# ============================================================
# BUILD FINAL JSON
# ============================================================

def build_final_json(
    total_records
):

    temporary_path = (
        RAW_JSON_PATH + ".tmp"
    )

    collected_at = datetime.now(
        timezone.utc
    ).isoformat()

    with open(
        temporary_path,
        "w",
        encoding="utf-8"
    ) as output:

        output.write("{\n")

        output.write(
            '  "source": "ERR Jeu de Paume",\n'
        )

        output.write(
            f'  "query": {json.dumps(QUERY)},\n'
        )

        output.write(
            f'  "records_total": {total_records},\n'
        )

        output.write(
            f'  "records_collected": {total_records},\n'
        )

        output.write(
            f'  "collected_at": '
            f'{json.dumps(collected_at)},\n'
        )

        output.write(
            '  "records": [\n'
        )

        first_record = True

        with open(
            CHECKPOINT_PATH,
            "r",
            encoding="utf-8"
        ) as checkpoint:

            for line in checkpoint:

                line = line.strip()

                if not line:
                    continue

                if not first_record:
                    output.write(
                        ",\n"
                    )

                output.write(
                    "    "
                )

                output.write(
                    line
                )

                first_record = False

        output.write(
            "\n  ]\n"
        )

        output.write(
            "}\n"
        )

    os.replace(
        temporary_path,
        RAW_JSON_PATH
    )


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(
        os.path.dirname(
            RAW_JSON_PATH
        ),
        exist_ok=True
    )

    print("=" * 80)
    print("ERR FAST FULL CORPUS COLLECTOR")
    print("=" * 80)
    print()

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_records = get_total_records()

    print(
        f"ERR records currently returned by Query=* : "
        f"{total_records:,}"
    )

    # --------------------------------------------------------
    # EXISTING PROGRESS
    # --------------------------------------------------------

    already_collected = (
        count_checkpoint_records()
    )

    print(
        f"Already collected: "
        f"{already_collected:,}"
    )

    if already_collected > total_records:

        raise RuntimeError(
            "Checkpoint contains more records "
            "than the current ERR corpus."
        )

    # --------------------------------------------------------
    # COMPLETE ALREADY?
    # --------------------------------------------------------

    if already_collected == total_records:

        print()
        print(
            "All records are already collected."
        )

        build_final_json(
            total_records
        )

        if os.path.exists(
            CHECKPOINT_PATH
        ):
            os.remove(
                CHECKPOINT_PATH
            )

        print(
            f"Final file: {RAW_JSON_PATH}"
        )

        return

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    next_position = (
        already_collected + 1
    )

    print(
        f"Starting from search position: "
        f"{next_position}"
    )

    print(
        f"Workers: {WORKERS}"
    )

    print(
        f"Batch size: {BATCH_SIZE}"
    )

    print()

    # --------------------------------------------------------
    # PROCESS BATCHES
    # --------------------------------------------------------

    while next_position <= total_records:

        batch_end = min(
            next_position + BATCH_SIZE - 1,
            total_records
        )

        positions = list(
            range(
                next_position,
                batch_end + 1
            )
        )

        print(
            f"Processing "
            f"{next_position:,}"
            f"-"
            f"{batch_end:,}..."
        )

        # ----------------------------------------------------
        # Resolve positions -> CardIds concurrently
        # ----------------------------------------------------

        card_map = {}

        with ThreadPoolExecutor(
            max_workers=WORKERS
        ) as executor:

            futures = {
                executor.submit(
                    get_card_id,
                    position
                ): position
                for position in positions
            }

            for future in as_completed(
                futures
            ):

                position = futures[
                    future
                ]

                try:

                    card_id = future.result()

                    card_map[
                        position
                    ] = card_id

                except Exception as error:

                    print(
                        f"Position {position} "
                        f"failed: {error}"
                    )

                    raise

        # ----------------------------------------------------
        # Fetch cards concurrently
        # ----------------------------------------------------

        records = []

        with ThreadPoolExecutor(
            max_workers=WORKERS
        ) as executor:

            futures = {
                executor.submit(
                    get_card_record,
                    position,
                    card_map[position]
                ): position
                for position in positions
            }

            for future in as_completed(
                futures
            ):

                position = futures[
                    future
                ]

                try:

                    record = future.result()

                    records.append(
                        record
                    )

                except Exception as error:

                    print(
                        f"Position {position} "
                        f"failed: {error}"
                    )

                    raise

        # ----------------------------------------------------
        # Restore original order
        # ----------------------------------------------------

        records.sort(
            key=lambda record:
            record["record_number"]
        )

        # ----------------------------------------------------
        # Save batch
        # ----------------------------------------------------

        save_batch(
            records
        )

        next_position = (
            batch_end + 1
        )

        print(
            f"Saved through "
            f"{batch_end:,}"
            f" / "
            f"{total_records:,}"
        )

        print()

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print()

    build_final_json(
        total_records
    )

    os.remove(
        CHECKPOINT_PATH
    )

    print(
        f"Final file created:"
    )

    print(
        RAW_JSON_PATH
    )


if __name__ == "__main__":
    main()