import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List

import urllib3

from ..console import console
from ..utils import con_hash
from .artifacts import Book, Chapter, Page, Shelf
from .client import LocalClient, RemoteClient
from .collectors.local import *
from .constants import *


class BookstackClient(RemoteClient):
    """Represents the remote Bookstack instance"""

    def __init__(self, verbose: bool) -> None:
        # if verbose is set, will issue logs
        super().__init__()
        self.verbose = verbose
        if self.verbose:
            console.log("Building remote client...")

        self.shelves: List[Shelf] = self._get_shelves()
        self.shelf_map = self._build_shelf_map()
        self.books = self._get_books()
        self.book_map = self._build_book_map()
        self.pages = self._get_pages()
        self.page_map = self._build_page_map()
        self.chapters = self._get_chapters()

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
        return {con_hash(shelf.name): shelf for shelf in self.shelves}

    def _build_book_map(self):
        """Build a map of all client books"""
        book_map = {}
        for book in self.books:
            if book.shelf:
                book_map[con_hash(book.name + book.shelf.name)] = book
            else:
                book_map[con_hash(book.name)] = book

        return book_map

    def _build_page_map(self):
        """Build a map of all client books"""
        page_map = {}
        for page in self.pages:
            if page.book:
                page_map[con_hash(page.name + page.book.name)] = page
            else:
                page_map[con_hash(page.name)] = page

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

            if self.verbose:
                console.log(f"Found remote shelf: {s}")

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

        BOOK_MAP = {
            con_hash(book.name + str(book.details["id"])): book for book in books
        }

        for shelf in self.shelves:
            for book in shelf.client_books:
                b = BOOK_MAP.get(con_hash(book["name"] + str(book["id"])))
                if b:
                    b.shelf = shelf
                    shelf.books.append(b)

                if self.verbose:
                    console.log(f"Found remote book: {b}")

        return books

    def _get_pages(self, client_pages=None):
        """Get remote pages from books"""
        if not client_pages:
            client_pages = self._get_from_client(BookstackAPIEndpoints.PAGES)

        for page in client_pages:

            class DetailedPage(DetailedBookstackLink):
                LINK = f"/api/pages/{page['id']}"

            resp = self._make_request(
                RequestType.GET,
                DetailedPage.LINK,
            ).data.decode()

            if resp:
                details = json.loads(resp)

                if details:
                    page["details"] = details

        pages = [Page(page["name"], details=page["details"]) for page in client_pages]

        PAGE_MAP = {
            con_hash(page.name + str(page.details["id"])): page for page in pages
        }

        for book in self.books:
            if book.details.get("contents"):
                for item in book.details["contents"]:
                    if item["type"] == "page":
                        p = PAGE_MAP.get(con_hash(item["name"] + str(item["id"])))
                        if p:
                            p.book = book
                            book.pages.append(p)

                        if self.verbose:
                            console.log(f"Found remote page: {p}")

                    if item["type"] == "chapter":
                        for page in item.get("pages"):
                            p = PAGE_MAP.get(con_hash(page["name"] + str(page["id"])))
                            if p:
                                p.book = book
                                book.pages.append(p)

        for page in pages:
            print(f"Page in Pages: {page}")
        return pages

    def _get_chapters(self):
        """Get remote chapters from books"""
        client_chapters = self._get_from_client(BookstackAPIEndpoints.CHAPTERS)

        for chapter in client_chapters:

            class DetailedChapter(DetailedBookstackLink):
                LINK = f"/api/chapters/{chapter['id']}"

            resp = self._make_request(
                RequestType.GET,
                DetailedChapter.LINK,
            ).data.decode()

            if resp:
                details = json.loads(resp)

                if details:
                    chapter["details"] = details

        chapters = [
            Chapter(chapter["name"], details=chapter["details"])
            for chapter in client_chapters
        ]

        CHAPTER_MAP = {
            con_hash(chapter.name + str(chapter.details["id"])): chapter
            for chapter in chapters
        }

        for book in self.books:
            print(f"Book Details: {book.details}")
            if book.details.get("contents"):
                for item in book.details["contents"]:
                    if item["type"] == "chapter":
                        c = CHAPTER_MAP.get(con_hash(item["name"] + str(item["id"])))
                        if c:
                            c.book = book
                            book.chapters.append(c)

                            if item.get("pages"):
                                self.pages.extend(self._get_pages(item["pages"]))

                        if self.verbose:
                            console.log(f"Found chapter page: {c}")

        return chapters

    def _retrieve_from_client_map(self, obj: Page | Shelf | Book):
        """Retrieve the client version of the local object"""
        if isinstance(obj, Page):
            name = os.path.splitext(obj.name)[0]
            book = None
            if obj.book:
                book = obj.book.name

            return (
                self.page_map[con_hash(name + book)]
                if book
                else self.page_map[con_hash(name)]
            )

        if isinstance(obj, Book):
            return (
                self.book_map[con_hash(obj.name + obj.shelf.name)]
                if obj.shelf
                else self.book_map[con_hash(obj.name)]
            )

        if isinstance(obj, Shelf):
            return self.shelf_map[con_hash(obj.name)]


class Bookstack(LocalClient):
    """Represents the local Bookstack notes instance"""

    def __init__(self, path, excluded, verbose: bool) -> None:
        self.verbose = verbose
        if self.verbose:
            console.log("Building local client...")

        self.client = BookstackClient(verbose=self.verbose)
        self.path = path
        self.excluded = excluded
        self.__set_collectors()
        self.__set_artifacts()
        self.missing_books = set()

    def __set_collectors(self):
        self.shelf_collector = LocalShelfCollector(
            self.client, self.path, self.excluded, self.verbose
        )
        self.book_collector = LocalBookCollector(
            self.client, self.path, self.excluded, self.verbose
        )
        self.page_collector = LocalPageCollector(
            self.client, self.path, self.excluded, self.verbose
        )

    def __set_artifacts(self):
        self.shelves = self.shelf_collector.set_shelves()
        self.books = self.book_collector.set_books(self.shelves)
        self.chapters = self._set_chapters()
        self.pages = self.page_collector.set_pages(self.books)

    def _refresh(self):
        # refresh objects
        if self.verbose:
            console.log("Refreshing local client")

        self.__set_artifacts()

    def delete(self, arg: BookstackItems, item: str):
        """Delete item from both local Obsidian Vault and remote Bookstack instance"""
        item_sections = item.split(os.path.sep)
        len_item_sections = len(item_sections)

        if arg == BookstackItems.SHELF:
            assert len_item_sections == 1
            path = os.path.join(self.path, item)
            if self.verbose:
                console.log(f"Deleting path: {path}")

            shutil.rmtree(path)
            shelf = Shelf(item)

            client_shelf = self.client._retrieve_from_client_map(shelf)

            class ShelfLink(DetailedBookstackLink):
                LINK = f"/api/shelves/{client_shelf.details['id']}"

            if self.verbose:
                console.log(f"Deleting shelf in Bookstack: {client_shelf}")

            self._delete_from_bookstack(ShelfLink.LINK)

            for book in client_shelf.books:

                class ShelfBookLink(DetailedBookstackLink):
                    LINK = f"/api/books/{book.details['id']}"

                if self.verbose:
                    console.log(f"Deleting book in Bookstack: {book}")

                self._delete_from_bookstack(ShelfBookLink.LINK)

        if arg == BookstackItems.BOOK:
            assert len_item_sections == 2
            path = os.path.join(self.path, item_sections[0], item_sections[1])
            if self.verbose:
                console.log(f"Deleting path at: {path}")

            shutil.rmtree(path)

            shelf = Shelf(item_sections[0])
            book = Book(item_sections[1], shelf=shelf)

            client_book = self.client._retrieve_from_client_map(book)

            class BookLink(DetailedBookstackLink):
                LINK = f"/api/books/{client_book.details['id']}"

            if self.verbose:
                console.log(f"Deleting book in Bookstack: {client_book}")

            self._delete_from_bookstack(BookLink.LINK)

        if arg == BookstackItems.PAGE:
            assert len_item_sections == 3
            path = os.path.join(
                self.path, item_sections[0], item_sections[1], item_sections[2] + ".md"
            )
            if self.verbose:
                console.log(f"Deleting path at: {path}")

            os.remove(path)
            book = Book(item_sections[1])
            page = Page(item_sections[2], book=book)
            client_page = self.client._retrieve_from_client_map(page)

            class PageLink(DetailedBookstackLink):
                LINK = f"/api/pages/{client_page.details['id']}"

            if self.verbose:
                console.log(f"Deleting page in Bookstack: {client_page}")

            self._delete_from_bookstack(PageLink.LINK)

    def _delete_from_bookstack(self, link: DetailedBookstackLink):
        """Make a DELETE request to a Bookstack API link"""
        resp = self.client._make_request(RequestType.DELETE, link)
        return resp

    def sync_remote(self):
        """Sync local changes to the remote."""
        self.shelf_collector.create_remote_missing_shelves()
        self.missing_books = self.book_collector._create_remote_missing_books()
        self.client._refresh()  # refresh to update book and page ids
        self._refresh()
        self.book_collector.update_shelf_books(self.missing_books)
        self.client._refresh()  # refresh to update book and page ids
        self.page_collector.create_remote_missing_pages()

    def sync_local(self):
        """Sync any remote changes to local store"""
        self.shelf_collector.create_local_missing_shelves()
        self.book_collector.create_local_missing_books()
        self.page_collector.create_local_missing_pages()

    def update_remote(self, remote: bool, local: bool):
        """Sync page contents to the remote"""
        updated_pages = []

        for page in self.pages:
            file_stat = os.stat(page.path)

            updated_at = datetime.utcfromtimestamp(file_stat.st_mtime)

            client_page = self.client._retrieve_from_client_map(page)

            client_updated = datetime.strptime(
                client_page.details["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            if remote:
                if updated_at > client_updated and (
                    updated_at - client_updated
                ) > timedelta(
                    seconds=5  # TODO: Surely there's a better way to tell the difference without downloading content
                ):
                    updated_pages.append(client_page)
                    self.page_collector.update_local_content(page, client_page)
            elif local:
                if updated_at < client_updated and (
                    client_updated - updated_at
                ) > timedelta(seconds=5):
                    console.log(f"Updating local page: {page}")
                    updated_pages.append(page)
                    content = self.page_collector.update(client_page)
                    with open(page.path, "wb") as f:
                        f.write(content)

        if not updated_pages and self.verbose:
            console.log("No pages changed to update")

    def _create_remote_missing_chapters(self):
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
            self.missing_books = missing_books  # save to update shelf location

    def _set_chapters(self):
        chapters = []
        for book in self.books:
            for chapter in book.chapters:
                chapters.append(chapter)

        return chapters
