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
    PUT = "PUT"


class SyncType(Enum):
    LOCAL = "local"
    REMOTE = "remote"


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
        self.shelf_map = {shelf["name"]: shelf for shelf in self.shelves}
        self.books = self._get_books()
        self.book_map = {book["name"]: book["id"] for book in self.books}
        self.pages = self._get_pages()

    def _make_request(
        self,
        request_type: RequestType,
        endpoint: BookstackAPIEndpoints | DetailedBookstackLink,
        body=None,
        json=None,
    ) -> urllib3.BaseHTTPResponse:
        """Make a HTTP request to a Bookstack API Endpoint"""

        assert self.base_url

        request_url = self.base_url + endpoint.value
        resp = self.http.request(
            request_type.value, request_url, headers=self.headers, body=body, json=json
        )
        return resp

    def _refresh(self):
        """Simply update the client"""
        self.http = urllib3.PoolManager()
        self.shelves = self._get_shelves()
        self.shelf_map = {shelf["name"]: shelf for shelf in self.shelves}
        self.books = self._get_books()
        self.book_map = {book["name"]: book for book in self.books}
        self.pages = self._get_pages()

    def _get_temp_book_map(self):
        """Get books from the client, but don't add to the client"""
        books = self._get_from_client(BookstackAPIEndpoints.BOOKS)
        return {book["name"]: book["id"] for book in books}

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
                book["shelf_id"] = shelf["id"]
                books.append(book)

        return books

    def _get_pages(self):
        """Get remote pages from books"""
        pages = []
        for book in self.books:

            class DetailedBook(DetailedBookstackLink):
                SHELF = f"/api/books/{book['id']}"

            details = json.loads(
                self._make_request(
                    RequestType.GET,
                    DetailedBook.SHELF,
                ).data.decode()
            )

            contents = details["contents"]

            for page in contents:
                page["book_name"] = book["name"]
                page["shelf_name"] = book["shelf"]
                page["book_id"] = book["id"]

            pages.extend(contents)

        return pages


class Bookstack:
    """Represents the local Bookstack notes instance"""

    def __init__(self, path, excluded) -> None:
        self.client = BookstackClient()
        self.path = path
        self.excluded = excluded
        self.shelves = [
            Shelf(path=os.path.join(self.path, shelf), name=shelf, client=self.client)
            for shelf in os.listdir(self.path)
            if not shelf.startswith(".") or shelf not in self.excluded
        ]
        self.books = self._set_books()
        self.pages = self._set_pages()
        self.missing_books = set()

    def _refresh(self):
        # refresh objects
        self.shelves = [
            Shelf(path=os.path.join(self.path, shelf), name=shelf, client=self.client)
            for shelf in os.listdir(self.path)
        ]
        self.books = self._set_books()
        self.pages = self._set_pages()

    def sync_remote(self):
        """Sync local changes to the remote."""
        self._create_remote_missing_shelves()
        self._create_remote_missing_books()
        self.client._refresh()  # refresh to update book and page ids
        self._refresh()
        self._update_shelf_books()
        self.client._refresh()  # refresh to update book and page ids
        self._create_remote_missing_pages()

    def sync_local(self):
        """Sync any remote changes to local store"""
        self._create_local_missing_shelves()
        self._create_local_missing_books()
        self._create_local_missing_pages()

    def _update_shelf_books(self):
        """Update's a shelf's books array"""
        new_books = []
        s = {}

        map = self.client._get_temp_book_map()

        for book in self.missing_books:
            if book.shelf.name not in s:
                s[book.shelf.name] = [book]
            else:
                s[book.shelf.name] += book

        for shelf in s:
            new_books = []
            for book in s[shelf]:
                new_books.append(map[book.name])

            client_shelf = self.client.shelf_map[shelf]
            books = client_shelf["books"] + new_books

            data = {
                "name": client_shelf["name"],
                "description": "Testing the description",
                "books": books,
            }

            self.client.headers["Content-Type"] = "application/json"

            class ShelfUpdate(DetailedBookstackLink):
                LINK = f"/api/shelves/{client_shelf['id']}"

            self.client._make_request(RequestType.PUT, ShelfUpdate.LINK, json=data)

    def _create_remote_missing_shelves(self):
        """Create any shelves in the remote which are missing"""
        missing_shelves = self._get_missing_set(BookstackItems.SHELF, SyncType.REMOTE)
        for shelf in missing_shelves:
            encoded_data, content_type = urllib3.encode_multipart_formdata(
                {"name": shelf.name}
            )
            self.client.headers["Content-Type"] = content_type
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.SHELVES, body=encoded_data
            )

    def _create_remote_missing_books(self):
        """Create any books in the remote which are missing"""
        missing_books = self._get_missing_set(BookstackItems.BOOK, SyncType.REMOTE)
        for book in missing_books:
            encoded_data, content_type = urllib3.encode_multipart_formdata(
                {"name": book.name}
            )
            self.client.headers["Content-Type"] = content_type
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.BOOKS, body=encoded_data
            )

        self.missing_books = missing_books  # save to update shelf location

    def _create_remote_missing_pages(self):
        """Create any pages in the remote which are missing"""
        missing_pages = self._get_missing_set(BookstackItems.PAGE, SyncType.REMOTE)
        for page in missing_pages:
            book_id = self.client.book_map[page.book.name]["id"]
            content = ""

            with open(page.path, "r") as f:
                content = str(f.read())

            data = {
                "book_id": book_id,
                "name": os.path.splitext(page.name)[0],
                "markdown": content,
            }

            self.client.headers["Content-Type"] = "application/json"
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.PAGES, json=data
            )

    def _create_local_missing_pages(self):
        """Create any missing pages in the local store, and write content to files which are missing."""
        missing_pages = self._get_missing_set(BookstackItems.PAGE, SyncType.LOCAL)
        for page in missing_pages:
            content = self._download_content(page)
            path = os.path.join(
                self.path, page["shelf_name"], page["book_name"], page["name"] + ".md"
            )
            if content is not None:
                with open(path, "wb") as f:
                    f.write(content)

    def _create_local_missing_books(self):
        """Create any missing books in the local store"""
        missing_books = self._get_missing_set(BookstackItems.BOOK, SyncType.LOCAL)
        for book in missing_books:
            os.mkdir(os.path.join(self.path, book["shelf"], book["name"]))

    def _create_local_missing_shelves(self):
        """Create any missing shelves in the local store"""
        missing_shelves = self._get_missing_set(BookstackItems.SHELF, SyncType.LOCAL)
        for shelf in missing_shelves:
            name = shelf["name"]
            os.mkdir(os.path.join(self.path, name))

    def _download_content(self, page):
        """Download content from item in remote instance"""

        class PageMarkdownLink(DetailedBookstackLink):
            LINK = f"/api/pages/{page['id']}/export/markdown"

        content = self.client._make_request(RequestType.GET, PageMarkdownLink.LINK)
        return content.data

    def _get_missing_set(self, item: BookstackItems, sync_type: SyncType):
        """Returns a missing set of items, can either compare to local or remote. Returns list of missing items."""
        attr = BOOKSTACK_ATTR_MAP[item]

        items = getattr(self, attr)
        client_items = getattr(self.client, attr)

        item_names = set(os.path.splitext(item.name)[0] for item in items)
        client_item_names = set(shelf["name"] for shelf in client_items)

        if sync_type == SyncType.LOCAL:
            missing = client_item_names - item_names
            missing_items = [ci for ci in client_items if ci["name"] in missing]
        else:
            missing = item_names - client_item_names
            missing_items = [
                ci for ci in items if os.path.splitext(ci.name)[0] in missing
            ]

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
