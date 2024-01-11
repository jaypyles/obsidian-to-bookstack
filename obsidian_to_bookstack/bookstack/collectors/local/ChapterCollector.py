from typing import List

import urllib3

from obsidian_to_bookstack.bookstack.artifacts import Book
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import LocalCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console


class LocalChapterCollector(LocalCollector):
    def __init__(
        self, client: RemoteClient, path: str, excluded: list, verbose: bool
    ) -> None:
        super().__init__(client, path, excluded, verbose)

    def set_chapters(self, books: List[Book]):
        """Set chapters from Obsidian Vault local directory"""
        chapters = []
        for book in books:
            for chapter in book.chapters:
                chapters.append(chapter)

        return chapters

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
