import os
from typing import List, Type

from obsidian_to_bookstack.bookstack.artifacts import Book, Page
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import LocalCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console


class LocalPageCollector(LocalCollector):
    """Performs operations with Pages pertaining to the local Obsidian Vault"""

    def __init__(
        self, local, client: RemoteClient, path: str, excluded: list, verbose: bool
    ) -> None:
        super().__init__(local, client, path, excluded, verbose)

    def set_pages(self, books: List[Book]):
        """Set pages from Obsidian Vault local directory"""
        pages = []
        for book in books:
            for chapter in book.chapters:
                for page in chapter.pages:
                    pages.append(page)

            for page in book.pages:
                pages.append(page)

        return pages

    def __download_content(self, page):
        """Download content from item in remote instance"""

        class PageMarkdownLink(DetailedBookstackLink):
            LINK = f"/api/pages/{page.details['id']}/export/markdown"

        content = self.client._make_request(RequestType.GET, PageMarkdownLink.LINK)
        return content.data

    def __remove_header(self, content, end, inc=False):  # oof
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

    def __remove_full_header(self, content):
        content = self.__remove_header(content, "#")
        content = self.__remove_header(content, "\n\n", inc=True)
        return content

    def create_local_missing_pages(self):
        """Create any missing pages in the local store, and write content to files which are missing."""
        missing_pages = self._get_missing_set(BookstackItems.PAGE, SyncType.LOCAL)
        for page in missing_pages:
            content = self.__download_content(page)
            path_components = [self.path, page.book.shelf.name, page.book.name]

            if page.chapter:
                path_components.append(page.chapter.name)

            path_components.append(page.name + ".md")

            path = os.path.join(*path_components)

            if content is not None:
                if self.verbose:
                    console.log(f"Creating a page at: {path}")

                with open(path, "wb") as f:
                    content = self.__remove_header(content, "\n\n", inc=True)
                    f.write(content)

    def create_remote_missing_pages(self):
        """Create any pages in the remote which are missing"""
        missing_pages = self._get_missing_set(BookstackItems.PAGE, SyncType.REMOTE)
        for page in missing_pages:
            if self.verbose:
                console.log(f"Bookstack missing page: {page}")

            client_book = self.client._retrieve_from_client_map(page.book)

            client_chapter = None

            if page.chapter:
                client_chapter = self.client._retrieve_from_client_map(page.chapter)

            book_id = client_book.details["id"]

            content = ""

            with open(page.path, "r") as f:
                content = str(f.read())

            data = {
                "book_id": book_id,
                "name": os.path.splitext(page.name)[0],
                "markdown": content,
            }

            if client_chapter:
                data["chapter_id"] = client_chapter.details["id"]

            self.client.headers["Content-Type"] = "application/json"
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.PAGES, json=data
            )

    def update_local_content(self, page: Page, client_page: Page):
        """Update the content of a page in the remote"""
        assert page.book

        client_book = self.client._retrieve_from_client_map(page.book)
        client_chapter = self.client._retrieve_from_client_map(page.chapter)

        content = None

        with open(page.path, "r") as f:
            content = "".join(f.readlines()[0:])  # remove header

        if content:
            if self.verbose:
                console.log(f"Updating remote page: {page}")

            data = {
                "book_id": client_book.details["id"],
                "name": os.path.splitext(page.name)[0],
                "markdown": content,
            }

            if client_chapter:
                data["chapter_id"] = client_chapter.details["id"]

            class PageLink(DetailedBookstackLink):
                LINK = f"/api/pages/{client_page.details['id']}"

            self.client._make_request(RequestType.PUT, PageLink.LINK, json=data)

    def update(self, client_page: Page):
        """Downloads and removes full header"""
        content = self.__download_content(client_page)
        return self.__remove_full_header(content)
