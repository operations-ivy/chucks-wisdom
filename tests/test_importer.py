from __future__ import annotations

import unittest

import importer
from importer import Settings


class FakeApi:
    def __init__(self, categories=("dev", "food"), jokes=None, search=None):
        self.categories = list(categories)
        self.jokes = iter(jokes or [])
        self.search = search or {"total": 0, "result": []}
        self.queries = []

    def get_categories(self):
        return self.categories

    def get_random_joke_from_category(self, category):
        return next(self.jokes)

    def find_specific(self, query):
        self.queries.append(query)
        return self.search


class FakeStorage:
    def __init__(self, existing=()):
        self.ids = set(existing)
        self.inserted = []

    def check_for_duplicate(self, joke_id, value):
        return joke_id in self.ids

    def insert_joke(self, joke_id, category, value):
        self.ids.add(joke_id)
        self.inserted.append((joke_id, category))


def joke(joke_id, categories=()):
    return {"id": joke_id, "value": f"joke {joke_id}", "categories": list(categories)}


class SettingsTest(unittest.TestCase):
    def test_defaults_are_the_original_behaviour(self):
        s = Settings.from_env({})
        self.assertEqual((s.query, s.categories, s.jokes, s.tries_per_category, s.max_duplicates, s.sleep_seconds),
                         ("", [], 1000, 1000, 50, 60.0))

    def test_from_env(self):
        s = Settings.from_env({"IMPORTER_QUERY": " kick ", "IMPORTER_CATEGORIES": "dev, food,,",
                               "IMPORTER_JOKES": "5", "IMPORTER_SLEEP_SECONDS": "0.5",
                               "IMPORTER_TRIES_PER_CATEGORY": "", "IMPORTER_MAX_DUPLICATES": "3"})
        self.assertEqual((s.query, s.categories, s.jokes, s.sleep_seconds, s.tries_per_category, s.max_duplicates),
                         ("kick", ["dev", "food"], 5, 0.5, 1000, 3))


class SearchTest(unittest.TestCase):
    def test_imports_new_matches_up_to_the_limit(self):
        api = FakeApi(search={"total": 4, "result": [joke("a", ["dev"]), joke("b"), joke("c"), joke("d")]})
        storage = FakeStorage(existing={"b"})
        added = importer.import_search(api, storage, Settings(query="round house", jokes=2))
        self.assertEqual(added, 2)
        self.assertEqual(storage.inserted, [("a", "dev"), ("c", importer.UNCATEGORIZED)])
        self.assertEqual(api.queries, ["round%20house"])

    def test_search_error_fails_the_run(self):
        api = FakeApi(search={"error": "HTTP error occurred: 400"})
        with self.assertRaises(RuntimeError):
            importer.import_search(api, FakeStorage(), Settings(query="x"))


class RandomTest(unittest.TestCase):
    def test_only_requested_categories_and_stops_at_the_limit(self):
        api = FakeApi(jokes=[joke("a"), joke("b"), joke("c")])
        storage = FakeStorage()
        added = importer.import_random(api, storage, Settings(categories=["food", "nope"], jokes=2, sleep_seconds=0),
                                       sleep=lambda s: None)
        self.assertEqual(added, 2)
        self.assertEqual(storage.inserted, [("a", "food"), ("b", "food")])

    def test_no_known_categories_fails(self):
        with self.assertRaises(RuntimeError):
            importer.import_random(FakeApi(), FakeStorage(), Settings(categories=["nope"]), sleep=lambda s: None)

    def test_stops_after_a_pass_with_nothing_new(self):
        api = FakeApi(categories=["dev"], jokes=[joke("a")] * 10)
        storage = FakeStorage(existing={"a"})
        added = importer.import_random(api, storage, Settings(tries_per_category=3, max_duplicates=50),
                                       sleep=lambda s: None)
        self.assertEqual(added, 0)


if __name__ == "__main__":
    unittest.main()
