import json

from obsidian_to_bookstack.bookstack.artifacts import Shelf
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import \
    RemoteCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console


class RemoteShelfCollector(RemoteCollector):
    def __init__(self, verbose: bool, client: RemoteClient) -> None:
        super().__init__(verbose, client)

    def get_shelves(self):
        """Gather remote's shelves and add detailed information"""
        client_shelves = self.client._get_from_client(BookstackAPIEndpoints.SHELVES)

        shelves = []

        for shelf in client_shelves:

            class DetailedShelf(DetailedBookstackLink):
                SHELF = f"/api/shelves/{shelf['id']}"

            details = json.loads(
                self.client._make_request(
                    RequestType.GET,
                    DetailedShelf.SHELF,
                ).data.decode()
            )

            s = Shelf(shelf["name"], details=details)
            s.client_books = s.details.pop("books")
            shelves.append(s)

            if self.verbose:
                console.log(f"Found remote shelf: {s}")

        return shelves
