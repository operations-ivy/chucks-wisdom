from __future__ import annotations

import unittest

from api_request import ApiRequest


class TestApiRequest(unittest.TestCase):
    def setUp(self):
        self.api = ApiRequest()

    def test_get_random(self):
        response = self.api.get_random()
        self.assertEqual(response["categories"], [])

    def test_get_random_joke_from_category(self):
        response = self.api.get_random_joke_from_category("animal")
        self.assertEqual(response["categories"], ["animal"])

    def test_find_specific(self):
        response = self.api.find_specific("animal")
        self.assertEqual(response["total"], 17)

    def test_get_categories(self):
        response = self.api.get_categories()
        self.assertEqual(
            response,
            [
                "animal",
                "career",
                "celebrity",
                "dev",
                "explicit",
                "fashion",
                "food",
                "history",
                "money",
                "movie",
                "music",
                "political",
                "religion",
                "science",
                "sport",
                "travel",
            ],
        )


if __name__ == "__main__":
    unittest.main()
