from __future__ import annotations

import json

import requests


class ApiRequest:
    def __inin__(self):
        self.base_api_url = "https://api.chucknorris.io/jokes/"

    def get_random(self):
        """
        Returns a random Chuck Norris joke.
        """
        random_chuck_jokes = self.base_api_url + "random"
        response = requests.get(random_chuck_jokes)
        json_data = json.loads(response.text)

        return json_data

    def get_random_joke_from_category(self, category):
        """
        Returns a random Chuck Norris joke from the specified category.
        """
        category_chuck_jokes = "random?category=" + category
        response = requests.get(category_chuck_jokes)
        json_data = json.loads(response.text)

        return json_data

    def find_specific(self, query):
        """
        Returns a list of Chuck Norris jokes that match the query.
        """
        query_chuck_jokes = self.base_api_url + "search?query=" + query
        response = requests.get(query_chuck_jokes)
        json_data = json.loads(response.text)

        return json_data

    def get_categories(self):
        """
        Returns a list of all the categories of Chuck Norris jokes.
        """
        categories_chuck_jokes = self.base_api_url + "categories"
        response = requests.get(categories_chuck_jokes)
        json_data = json.loads(response.text)

        return json_data
