from __future__ import annotations

import os

from chucks_wisdom.api_request.api_request import ApiRequest
from chucks_wisdom.sqlite_storage.sqlite_storage import SqliteStorage


if __name__ == "__main__":
    # db_location = sys.argv[1]
    db_location = os.environ["DB_LOCATION"]
    chuck_api_url = "https://api.chucknorris.io/jokes/"
    api = ApiRequest()
    storage = SqliteStorage(db_path=db_location)

    joke_categories = api.get_categories()
    joke_count = 0
    desired_joke_count = 250
    joke_range = 500
    max_duplicates = 50

    while joke_count < desired_joke_count:
        for category in joke_categories:
            print("###")
            print("Running " + str(joke_range) + " GETs from the random API for category: " + category + "...")
            print("Stopping when " + str(desired_joke_count) + " total jokes are added.")
            print("Still need " + str(desired_joke_count - joke_count) + " jokes.")
            print("Max duplicate checks allowed: " + str(max_duplicates))
            print("###")

            duplicate_count = 0
            for i in range(joke_range):
                joke_data = api.get_random_joke_from_category(category)
                joke_id = joke_data["id"]
                joke_category = category
                joke_value = joke_data["value"]

                if storage.check_for_duplicate(joke_id, joke_value) is False and duplicate_count < max_duplicates:
                    storage.insert_joke(joke_id, category, joke_value)
                    joke_count += 1
                    print("Joke " + str(joke_count) + " added: " + joke_id)
                elif duplicate_count >= max_duplicates:
                    print(str(max_duplicates) + " Duplicate checks made, moving to next category.")
                    break
                else:
                    duplicate_count += 1
                    duplicate_checks_remaining = max_duplicates - duplicate_count
                    continue

        print("Total Jokes Added this run: " + str(joke_count))
    storage.close_connection()
