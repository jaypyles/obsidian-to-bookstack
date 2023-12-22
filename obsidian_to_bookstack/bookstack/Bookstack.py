import os

from .Shelf import Shelf


class BookstackClient:
    def __init__(self) -> None:
        self.api_id = None
        self.api_secret = None


class Bookstack:
    def __init__(self, path, client) -> None:
        self.client = client
        self.path = path
        self.shelves = [
            Shelf(path=os.path.join(self.path, shelf), name=shelf, client=self.client)
            for shelf in os.listdir(self.path)
        ]

    def _get_shelves():
        ...  # make request
