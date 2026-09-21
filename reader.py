from __future__ import annotations

import hashlib
import os

from sql_storage_operations_ivy.pg_storage import PGStorage


def read_hashed_entries() -> list[dict[str, str]]:
    db_connection_string = os.environ["DB_CONNECTION_STRING"]
    storage = PGStorage(db_connection_string)

    try:
        all_of_it = storage.read_all_jokes()
    finally:
        storage.close_connection()

    return [
        {
            "category": hashlib.sha256(i[1].encode("utf-8")).hexdigest(),
            "value": hashlib.sha256(i[2].encode("utf-8")).hexdigest(),
        }
        for i in all_of_it
    ]
