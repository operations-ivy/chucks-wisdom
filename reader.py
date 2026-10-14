from __future__ import annotations

import hashlib
import os

from sql_storage_operations_ivy.pg_storage import PGStorage

import metrics


def read_hashed_entries() -> list[dict[str, str]]:
    db_connection_string = os.environ["DB_CONNECTION_STRING"]
    try:
        with metrics.DB_READ_SECONDS.time():
            storage = PGStorage(db_connection_string)
            try:
                all_of_it = storage.read_all_jokes()
            finally:
                storage.close_connection()
    except Exception:
        metrics.DB_ERRORS.inc()
        raise
    metrics.JOKES.set(len(all_of_it))

    return [
        {
            "category": hashlib.sha256(i[1].encode("utf-8")).hexdigest(),
            "value": hashlib.sha256(i[2].encode("utf-8")).hexdigest(),
        }
        for i in all_of_it
    ]
