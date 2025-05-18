from __future__ import annotations

import os
import time

import structlog
from api_request_operations_ivy.api_request import ApiRequest
from prometheus_client import Counter
from prometheus_client import start_http_server
from sql_storage_operations_ivy.pg_storage import PGStorage

log = structlog.get_logger()

JOKES_WRITTEN = Counter("jokes_written_total", "Number of jokes written to DB this session")
DUPLICATES_RECEIVED = Counter("duplicate_joke_total", "duplicate joke hits from API")
CATEGORY_SWITCH = Counter("category_switch_total", "amount of times category has switched due to duplicates")

start_http_server(8000)

if __name__ == "__main__":
    db_connection_string = os.environ["DB_CONNECTION_STRING"]
    chuck_api_url = "https://api.chucknorris.io/jokes/"
    api = ApiRequest()
    try:
        log.info("Creating DB Connection")
        log.info("...")
        storage = PGStorage(db_connection_string)
        log.info("DB Connection Established!")
    except:  # noqa: E722
        raise Exception("No connection, did you export DB_CONNECTION_STRING?")

    # TODO: offload these variables to helm chart
    joke_categories = api.get_categories()
    joke_count = 0
    desired_joke_count = 1000
    joke_range = 1000
    max_duplicates = 50
    sleep_interval = 60

    while joke_count < desired_joke_count:
        for category in joke_categories:
            duplicate_count = 0
            for i in range(joke_range):
                log.info("Checking API.. %s", i)
                joke_data = api.get_random_joke_from_category(category)
                joke_id = joke_data["id"]
                joke_category = category
                joke_value = joke_data["value"]

                time.sleep(sleep_interval)
                if storage.check_for_duplicate(joke_id, joke_value) == False and duplicate_count < max_duplicates:
                    storage.insert_joke(joke_id, category, joke_value)
                    joke_count += 1
                    JOKES_WRITTEN.inc()
                    log.info("Thats a new one!: %s", joke_id)
                elif duplicate_count >= max_duplicates:
                    CATEGORY_SWITCH.inc()
                    log.info("Ok let's move on: %s", category)
                    break
                else:
                    DUPLICATES_RECEIVED.inc()
                    log.info("I've heard that one before: %s", joke_id)
                    duplicate_count += 1
                    duplicate_checks_remaining = max_duplicates - duplicate_count
                    continue

        log.info("Total Jokes Added this run: %s", str(joke_count))
    storage.close_connection()
