import json
from typing import List

from obsidian_to_bookstack.bookstack.artifacts import Book, Shelf
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import \
    RemoteCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console
from obsidian_to_bookstack.utils import con_hash


class RemoteBookCollector(RemoteCollector):
    def __init__(self, verbose: bool, client: RemoteClient) -> None:
        super().__init__(verbose, client)

    def get_books(self, shelves: List[Shelf]):
        """Get remote books from shelves"""
        client_books = self.client._get_from_client(BookstackAPIEndpoints.BOOKS)

        for book in client_books:

            class DetailedBook(DetailedBookstackLink):
                LINK = f"/api/books/{book['id']}"

            details = json.loads(
                self.client._make_request(
                    RequestType.GET,
                    DetailedBook.LINK,
                ).data.decode()
            )

            book["details"] = details

        books = [Book(book["name"], details=book["details"]) for book in client_books]

        BOOK_MAP = {
            con_hash(book.name + str(book.details["id"])): book for book in books
        }

        for shelf in shelves:
            for book in shelf.client_books:
                b = BOOK_MAP.get(con_hash(book["name"] + str(book["id"])))
                if b:
                    b.shelf = shelf
                    shelf.books.append(b)

                if self.verbose:
                    console.log(f"Found remote book: {b}")

        return books
