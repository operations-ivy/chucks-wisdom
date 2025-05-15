from __future__ import annotations

import os
import time

import structlog
from api_request_operations_ivy.api_request import ApiRequest
from sql_storage_operations_ivy.pg_storage import PGStorage

log = structlog.get_logger()

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
                    log.info("Joke added: %s", joke_id)
                elif duplicate_count >= max_duplicates:
                    log.info("Duplicate found: %s", joke_id)
                    break
                else:
                    duplicate_count += 1
                    duplicate_checks_remaining = max_duplicates - duplicate_count
                    continue

        log.info("Total Jokes Added this run: %s", str(joke_count))
    storage.close_connection()
