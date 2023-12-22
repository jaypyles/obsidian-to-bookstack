import json
import os
from enum import Enum

import urllib3

from .Shelf import Shelf


class BookstackAPIEndpoints(Enum):
    PAGES = "/api/pages"
    BOOKS = "/api/books"
    SHELVES = "/api/shelves"

    @staticmethod
    def shelf_details(id_value):
        return f"/api/shelves/{id_value}"


class DetailedBookstackLink(Enum):
    ...


class BookstackItems(Enum):
    PAGE = "page"
    BOOK = "book"
    SHELF = "shelf"


class RequestType(Enum):
    POST = "POST"
    GET = "GET"


BOOKSTACK_ATTR_MAP = {
    BookstackItems.SHELF: "shelves",
    BookstackItems.BOOK: "books",
    BookstackItems.PAGE: "pages",
}


class BookstackClient:
    """Represents the remote Bookstack instance"""

    def __init__(self) -> None:
        self.id = os.getenv("BOOKSTACK_TOKEN_ID")
        self.secret = os.getenv("BOOKSTACK_TOKEN_SECRET")
        self.base_url = os.getenv("BOOKSTACK_BASE_URL")
        self.headers = {"Authorization": f"Token {self.id}:{self.secret}"}
        self.http = urllib3.PoolManager()
        self.shelves = self._get_shelves()
        self.books = self._get_books()
        self.pages = self._get_from_client(BookstackAPIEndpoints.PAGES)

    def _make_request(
        self,
        request_type: RequestType,
        endpoint: BookstackAPIEndpoints | DetailedBookstackLink,
    ) -> urllib3.BaseHTTPResponse:
        """Make a HTTP request to a Bookstack API Endpoint"""

        assert self.base_url

        request_url = self.base_url + endpoint.value
        resp = self.http.request(request_type.value, request_url, headers=self.headers)
        return resp

    def _get_from_client(self, endpoint: BookstackAPIEndpoints):
        """Make a GET request to a Bookstack API Endpoint"""
        resp = self._make_request(RequestType.GET, endpoint)
        assert resp

        data = json.loads(resp.data.decode())
        return data["data"]

    def _get_shelves(self):
        """Gather remote's shelves and add detailed information"""
        shelves = self._get_from_client(BookstackAPIEndpoints.SHELVES)

        for shelf in shelves:

            class DetailedShelf(DetailedBookstackLink):
                SHELF = f"/api/shelves/{shelf['id']}"

            details = json.loads(
                self._make_request(
                    RequestType.GET,
                    DetailedShelf.SHELF,
                ).data.decode()
            )

            shelf["books"] = details["books"]

        return shelves

    def _get_books(self):
        """Get remote books from shelves"""
        books = []

        for shelf in self.shelves:
            for book in shelf["books"]:
                book["shelf"] = shelf["name"]
                books.append(book)

        return books


class Bookstack:
    """Represents the local Bookstack notes instance"""

    def __init__(self, path) -> None:
        self.client = BookstackClient()
        self.path = path
        self.shelves = [
            Shelf(path=os.path.join(self.path, shelf), name=shelf, client=self.client)
            for shelf in os.listdir(self.path)
        ]
        self.books = self._set_books()
        self.pages = self._set_pages()

    def sync_remote(self):
        """Sync local changes to the remote."""

    def sync_local(self):
        """Sync any remote changes to local store"""
        self._create_missing_shelves()
        self._create_missing_books()
        missing_pages = self._get_missing_set(BookstackItems.PAGE)

    def _create_missing_books(self):
        """Create any missing books"""
        missing_books = self._get_missing_set(BookstackItems.BOOK)
        for book in missing_books:
            os.mkdir(os.path.join(self.path, book["shelf"], book["name"]))

    def _create_missing_shelves(self):
        """Create any missing shelves"""
        missing_shelves = self._get_missing_set(BookstackItems.SHELF)
        for shelf in missing_shelves:
            name = shelf["name"]
            os.mkdir(os.path.join(self.path, name))

    def _download_content(self):
        """Download content from item in remote instance"""

    def _get_missing_set(self, item: BookstackItems):
        """Returns a missing set of items compared to the local store. Returns list of missing items."""
        attr = BOOKSTACK_ATTR_MAP[item]

        items = getattr(self, attr)
        client_items = getattr(self.client, attr)

        item_names = set(item.name for item in items)
        client_item_names = set(shelf["name"] for shelf in client_items)

        missing = client_item_names - item_names

        missing_items = [ci for ci in client_items if ci["name"] in missing]

        return missing_items

    def _set_books(self):
        books = []
        for shelf in self.shelves:
            for book in shelf.books:
                books.append(book)

        return books

    def _set_pages(self):
        pages = []
        for book in self.books:
            for page in book.pages:
                pages.append(page)

        return pages
