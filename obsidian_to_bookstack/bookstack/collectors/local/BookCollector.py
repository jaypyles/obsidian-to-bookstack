import os
from typing import List

import urllib3

from obsidian_to_bookstack.bookstack.artifacts import Book, Shelf
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import LocalCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console


class LocalBookCollector(LocalCollector):
    """Performs operations with Books pertaining to the local Obsidian Vault"""

    def __init__(
        self, client: RemoteClient, path: str, excluded: list, verbose: bool
    ) -> None:
        super().__init__(client, path, excluded, verbose)

    def set_books(self, shelves: List[Shelf]) -> List[Book]:
        """Set books from Obsidian Vault local directory"""
        books = []
        for shelf in shelves:
            for book in shelf.books:
                books.append(book)

        return books

    def update_shelf_books(self, missing_books: List[Book]):
        """Update's a shelf's books array"""
        new_books = []
        s = {}
        map = self.client._get_temp_book_map()

        for book in missing_books:
            if book.shelf not in s:
                s[book.shelf] = [book]
            else:
                s[book.shelf].append(book)

        for shelf in s:
            new_books = []
            for book in s[shelf]:
                new_books.append(map[book.name])

            client_shelf = self.client._retrieve_from_client_map(shelf)

            if client_shelf:
                books = new_books
                if client_shelf.details.get("books"):
                    books = client_shelf.details["books"] + new_books

                data = {
                    "name": client_shelf.details["name"],
                    "books": books,
                }

                self.client.headers["Content-Type"] = "application/json"

                class ShelfUpdate(DetailedBookstackLink):
                    LINK = f"/api/shelves/{client_shelf.details['id']}"

                self.client._make_request(RequestType.PUT, ShelfUpdate.LINK, json=data)

    def create_local_missing_books(self) -> None:
        """Create any missing books in the local store"""
        missing_books = self._get_missing_set(BookstackItems.BOOK, SyncType.LOCAL)

        for book in missing_books:
            path = os.path.join(self.path, book.shelf.name, book.name)
            os.mkdir(path)

            if self.verbose:
                console.log(f"Creating a book at: {path}")

    def _create_remote_missing_books(self) -> List[Book] | List:
        """Create any books in the remote which are missing"""
        missing_books = self._get_missing_set(BookstackItems.BOOK, SyncType.REMOTE)
        for book in missing_books:
            if self.verbose:
                console.log(f"Bookstack missing book: {book}")

            encoded_data, content_type = urllib3.encode_multipart_formdata(
                {"name": book.name}
            )
            self.client.headers["Content-Type"] = content_type
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.BOOKS, body=encoded_data
            )

        if missing_books:
            return missing_books  # save to update shelf location

        return []
