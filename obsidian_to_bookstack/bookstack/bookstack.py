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
from .collectors.remote import *
from .constants import *


class BookstackClient(RemoteClient):
    """Represents the remote Bookstack instance"""

    def __init__(self, verbose: bool) -> None:
        # if verbose is set, will issue logs
        super().__init__()
        self.verbose = verbose
        if self.verbose:
            console.log("Building remote client...")

        self.__set_collectors()
        self.__set_artifacts()
        self.__set_maps()

    def __set_collectors(self):
        self.shelf_collector = RemoteShelfCollector(self.verbose, self)
        self.book_collector = RemoteBookCollector(self.verbose, self)
        self.page_collector = RemotePageCollector(self.verbose, self)
        self.chapter_collector = RemoteChapterCollector(self.verbose, self)

    def __set_artifacts(self):
        self.shelves: List[Shelf] = self.shelf_collector.get_shelves()
        self.books: List[Book] = self.book_collector.get_books(self.shelves)
        self.pages: List[Page] = self.page_collector.get_pages(self.books)
        self.chapters: List[Chapter] = self.chapter_collector.get_chapters(self.books)

    def __set_maps(self):
        self.shelf_map = self._build_shelf_map()
        self.book_map = self._build_book_map()
        self.page_map = self._build_page_map()
        self.chapter_map = self._build_chapter_map()

    def _refresh(self):
        """Simply update the client"""
        self.http = urllib3.PoolManager()
        self.__set_collectors()
        self.__set_artifacts()
        self.__set_maps()

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
        """Build a map of all client pages"""
        page_map = {}
        for page in self.pages:
            if page.chapter and page.book:
                page_map[
                    con_hash(page.name + page.book.name + page.chapter.name)
                ] = page

            elif page.book:
                page_map[con_hash(page.name + page.book.name)] = page

            else:
                page_map[con_hash(page.name)] = page

        return page_map

    def _build_chapter_map(self):
        """Build a map of all client chapters"""
        page_map = {}
        for chapter in self.chapters:
            if chapter.book:
                page_map[con_hash(chapter.name + chapter.book.name)] = chapter

        return page_map

    def _get_temp_book_map(self):
        """Get books from the client, but don't add to the client"""
        books = self._get_from_client(BookstackAPIEndpoints.BOOKS)
        return {book["name"]: book["id"] for book in books}

    def _retrieve_from_client_map(self, obj: Page | Shelf | Book | Chapter):
        """Retrieve the client version of the local object"""
        if isinstance(obj, Page):
            name = os.path.splitext(obj.name)[0]

            if obj.chapter and obj.book:
                return self.page_map[con_hash(name + obj.book.name + obj.chapter.name)]

            return (
                self.page_map[con_hash(name + obj.book.name)]
                if obj.book
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

        if isinstance(obj, Chapter):
            return self.chapter_map[con_hash(obj.name + obj.book.name)]


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
            self, self.client, self.path, self.excluded, self.verbose
        )
        self.book_collector = LocalBookCollector(
            self, self.client, self.path, self.excluded, self.verbose
        )
        self.page_collector = LocalPageCollector(
            self, self.client, self.path, self.excluded, self.verbose
        )
        self.chapter_collector = LocalChapterCollector(
            self, self.client, self.path, self.excluded, self.verbose
        )

    def __set_artifacts(self):
        self.shelves = self.shelf_collector.set_shelves()
        self.books = self.book_collector.set_books(self.shelves)
        self.chapters = self.chapter_collector.set_chapters(self.books)
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

        if arg == BookstackItems.CHAPTER:
            assert len_item_sections == 3
            path = os.path.join(
                self.path, item_sections[0], item_sections[1], item_sections[2]
            )
            if self.verbose:
                console.log(f"Deleting path at: {path}")

            shutil.rmtree(path)

            shelf = Shelf(item_sections[0])
            book = Book(item_sections[1], shelf=shelf)
            chapter = Chapter(item_sections[2], book=book)

            client_chapter = self.client._retrieve_from_client_map(chapter)

            class ChapterLink(DetailedBookstackLink):
                LINK = f"/api/books/{client_chapter.details['id']}"

            if self.verbose:
                console.log(f"Deleting chapter in Bookstack: {client_chapter}")

            self._delete_from_bookstack(ChapterLink.LINK)

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
        self.chapter_collector.create_remote_missing_chapters()
        self.page_collector.create_remote_missing_pages()

    def sync_local(self):
        """Sync any remote changes to local store"""
        self.shelf_collector.create_local_missing_shelves()
        self.book_collector.create_local_missing_books()
        self.chapter_collector.create_local_missing_chapters()
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
