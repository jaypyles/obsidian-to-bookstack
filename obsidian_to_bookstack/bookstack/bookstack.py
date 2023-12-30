import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import List

import urllib3

from .artifacts import Book, Page, Shelf
from .client import Client


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


class BookstackClient(Client):
    """Represents the remote Bookstack instance"""

    def __init__(self) -> None:
        self.id = os.getenv("BOOKSTACK_TOKEN_ID")
        self.secret = os.getenv("BOOKSTACK_TOKEN_SECRET")
        self.base_url = os.getenv("BOOKSTACK_BASE_URL")
        self.headers = {"Authorization": f"Token {self.id}:{self.secret}"}
        self.http = urllib3.PoolManager()
        self.shelves: List[Shelf] = self._get_shelves()
        self.shelf_map = self._build_shelf_map()
        self.books = self._get_books()
        self.book_map = self._build_book_map()
        self.pages = self._get_pages()
        self.page_map = self._build_page_map()

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
        self.shelves: List[Shelf] = self._get_shelves()
        self.shelf_map = self._build_shelf_map()
        self.books = self._get_books()
        self.book_map = self._build_book_map()
        self.pages = self._get_pages()
        self.page_map = self._build_page_map()

    def _build_shelf_map(self):
        """Build a map of all client shelves"""
        return {hash(shelf.name): shelf for shelf in self.shelves}

    def _build_book_map(self):
        """Build a map of all client books"""
        book_map = {}
        for book in self.books:
            if book.shelf:
                book_map[hash(book.name + book.shelf.name)] = book
            else:
                book_map[hash(book.name)] = book

        return book_map

    def _build_page_map(self):
        """Build a map of all client books"""
        page_map = {}
        for page in self.pages:
            if page.book:
                page_map[hash(page.name + page.book.name)] = page
            else:
                page_map[hash(page.name)] = page

        return page_map

    def _get_temp_book_map(self):
        """Get books from the client, but don't add to the client"""
        books = self._get_from_client(BookstackAPIEndpoints.BOOKS)
        return {book["name"]: book["id"] for book in books}

    def _get_from_client(self, endpoint: BookstackAPIEndpoints):
        """Make a GET request to a Bookstack API Endpoint"""
        resp = self._make_request(RequestType.GET, endpoint)
        assert resp

        data = json.loads(resp.data.decode())
        print(data)
        return data["data"]

    def _get_shelves(self):
        """Gather remote's shelves and add detailed information"""
        client_shelves = self._get_from_client(BookstackAPIEndpoints.SHELVES)

        shelves = []

        for shelf in client_shelves:

            class DetailedShelf(DetailedBookstackLink):
                SHELF = f"/api/shelves/{shelf['id']}"

            details = json.loads(
                self._make_request(
                    RequestType.GET,
                    DetailedShelf.SHELF,
                ).data.decode()
            )

            s = Shelf(shelf["name"], details=details)
            s.client_books = s.details.pop("books")
            shelves.append(s)

        return shelves

    def _get_books(self):
        """Get remote books from shelves"""
        client_books = self._get_from_client(BookstackAPIEndpoints.BOOKS)

        for book in client_books:

            class DetailedBook(DetailedBookstackLink):
                LINK = f"/api/books/{book['id']}"

            details = json.loads(
                self._make_request(
                    RequestType.GET,
                    DetailedBook.LINK,
                ).data.decode()
            )

            book["details"] = details

        books = [Book(book["name"], details=book["details"]) for book in client_books]

        BOOK_MAP = {hash(book.name + str(book.details["id"])): book for book in books}

        for shelf in self.shelves:
            for book in shelf.client_books:
                b = BOOK_MAP.get(hash(book["name"] + book["id"]))
                if b:
                    b.shelf = shelf

        return books

    def _get_pages(self):
        """Get remote pages from books"""
        client_pages = self._get_from_client(BookstackAPIEndpoints.PAGES)

        for page in client_pages:

            class DetailedPage(DetailedBookstackLink):
                LINK = f"/api/books/{page['id']}"

            details = json.loads(
                self._make_request(
                    RequestType.GET,
                    DetailedPage.LINK,
                ).data.decode()
            )

            page["details"] = details

        pages = [Page(page["name"], details=page["details"]) for page in client_pages]

        PAGE_MAP = {hash(page.name + str(page.details["id"])): page for page in pages}

        for book in self.books:
            if book.details["contents"]:
                for page in book.details["contents"][0]["pages"]:
                    p = PAGE_MAP.get(hash(page["name"] + page["id"]))
                    if p:
                        p.book = book

        return pages


class Bookstack(Client):
    """Represents the local Bookstack notes instance"""

    def __init__(self, path, excluded) -> None:
        self.client = BookstackClient()
        self.path = path
        self.excluded = excluded
        self.shelves = self._set_shelves()
        self.books = self._set_books()
        self.pages = self._set_pages()
        self.missing_books = set()

    def _refresh(self):
        # refresh objects
        self.shelves = self._set_shelves()
        self.books = self._set_books()
        self.pages = self._set_pages()

    def delete(self):
        """Delete item from both local Obsidian Vault and remote Bookstack instance"""
        ...

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

    def _retrieve_from_client_map(self, obj: Page | Shelf | Book):
        """Retrieve the client version of the local object"""
        if isinstance(obj, Page):
            name = os.path.splitext(obj.name)[0]
            book = None
            if obj.book:
                book = obj.book.name

            print(f"Page: {name}, Book: {obj.book.name}")

            return (
                self.client.page_map[hash(name + book)]
                if book
                else self.client.page_map[hash(name)]
            )

        if isinstance(obj, Book):
            return (
                self.client.book_map[hash(obj.name + obj.shelf.name)]
                if obj.shelf
                else self.client.book_map[hash(obj.name)]
            )

        if isinstance(obj, Shelf):
            return self.client.shelf_map[hash(obj.name)]

    def update_remote(self, remote: bool, local: bool):
        """Sync page contents to the remote"""
        for page in self.pages:
            file_stat = os.stat(page.path)

            updated_at = datetime.utcfromtimestamp(file_stat.st_mtime)

            client_page = self._retrieve_from_client_map(page)

            client_updated = datetime.strptime(
                client_page.details["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            if remote:
                if updated_at > client_updated and (
                    updated_at - client_updated
                ) > timedelta(
                    seconds=5  # TODO: Surely there's a better way to tell the difference without downloading content
                ):
                    self._update_local_content(page, client_page)
            elif local:
                if updated_at < client_updated and (
                    client_updated - updated_at
                ) > timedelta(seconds=5):
                    content = self._download_content(client_page)
                    content = self._remove_full_header(content)
                    with open(page.path, "wb") as f:
                        f.write(content)

    def _remove_full_header(self, content):
        content = self._remove_header(content, "#")
        content = self._remove_header(content, "\n\n", inc=True)
        return content

    def _remove_header(self, content, end, inc=False):  # oof
        first_index = content.find(b"#")
        end = f"{end}".encode()
        second_index = content.find(end, first_index + 1)

        if inc:
            second_index += 2

        if first_index != -1 and second_index != -1:
            new_content = content[:first_index] + content[second_index:]
            return new_content
        else:
            return content

    def _update_local_content(self, page, client_page):
        """Update the content of a page in the remote"""
        client_book = self._retrieve_from_client_map(page.book)

        content = None

        with open(page.path, "r") as f:
            content = "".join(f.readlines()[0:])  # remove header

        if content:
            data = {
                "book_id": client_book,
                "name": os.path.splitext(page.name)[0],
                "markdown": content,
            }

            class PageLink(DetailedBookstackLink):
                LINK = f"/api/pages/{client_page['id']}"

            self.client._make_request(RequestType.PUT, PageLink.LINK, json=data)

    def _update_shelf_books(self):
        """Update's a shelf's books array"""
        new_books = []
        s = {}

        map = self.client._get_temp_book_map()

        for book in self.missing_books:
            if book.shelf.name not in s:
                s[book.shelf.name] = [book]
            else:
                s[book.shelf.name].append(book)

        for shelf in s:
            new_books = []
            for book in s[shelf]:
                new_books.append(map[book.name])

            client_shelf = self.client.shelf_map[shelf]
            books = client_shelf.details["books"] + new_books

            data = {
                "name": client_shelf.details["name"],
                "books": books,
            }

            self.client.headers["Content-Type"] = "application/json"

            class ShelfUpdate(DetailedBookstackLink):
                LINK = f"/api/shelves/{client_shelf.details['id']}"

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

        if missing_books:
            self.missing_books = missing_books  # save to update shelf location

    def _create_remote_missing_pages(self):
        """Create any pages in the remote which are missing"""
        missing_pages = self._get_missing_set(BookstackItems.PAGE, SyncType.REMOTE)
        for page in missing_pages:
            client_page = self._retrieve_from_client_map(page)
            book_id = client_page.book.details["id"]
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
        print(f"Self PAges: {self.pages}")

        items = getattr(self, attr)
        client_items = getattr(self.client, attr)

        item_names = set(os.path.splitext(item.name)[0] for item in items)
        client_item_names = set(shelf.name for shelf in client_items)

        print(f"ITEM NAMES: {item_names}")
        print(f"CLIENT ITEM NAMES: {client_item_names}")

        if sync_type == SyncType.LOCAL:
            missing = client_item_names - item_names
            missing_items = [ci for ci in client_items if ci.name in missing]
        else:
            missing = item_names - client_item_names
            missing_items = [
                ci for ci in items if os.path.splitext(ci.name)[0] in missing
            ]

        return missing_items

    def _set_shelves(self):
        """Assert shelves are folders in DIR"""
        shelves = []
        for shelf in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path, shelf)) and shelf != ".obsidian":
                if not shelf.startswith(".") and shelf not in self.excluded:
                    s = Shelf(
                        path=os.path.join(self.path, shelf),
                        name=shelf,
                        client=self.client,
                        from_client=False,
                    )
                    shelves.append(s)

        return shelves

    def _set_books(self):
        books = []
        for shelf in self.shelves:
            for book in shelf.books:
                books.append(book)

        return books

    def _set_pages(self):
        pages = []
        for book in self.books:
            print(f"Book: {book}")
            for page in book.pages:
                print(f"Page: {page}")
                pages.append(page)

        return pages
