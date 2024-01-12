import os
from typing import List

import urllib3

from obsidian_to_bookstack.bookstack.artifacts import Book
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import LocalCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console


class LocalChapterCollector(LocalCollector):
    def __init__(
        self, local, client: RemoteClient, path: str, excluded: list, verbose: bool
    ) -> None:
        super().__init__(local, client, path, excluded, verbose)

    def set_chapters(self, books: List[Book]):
        """Set chapters from Obsidian Vault local directory"""
        chapters = []
        for book in books:
            for chapter in book.chapters:
                chapters.append(chapter)

        return chapters

    def create_local_missing_chapters(self):
        missing_chapters = self._get_missing_set(BookstackItems.CHAPTER, SyncType.LOCAL)

        for chapter in missing_chapters:
            if chapter.book:
                path = os.path.join(
                    self.path, chapter.book.shelf.name, chapter.book.name, chapter.name
                )
                if self.verbose:
                    console.log(f"Creating a chapter at: {path}")
                os.mkdir(path)

    def create_remote_missing_chapters(self):
        """Create any chapters in the remote which are missing"""
        missing_chapters = self._get_missing_set(
            BookstackItems.CHAPTER, SyncType.REMOTE
        )
        for chapter in missing_chapters:
            if self.verbose:
                console.log(f"Bookstack missing chapter: {chapter}")

            client_book = self.client._retrieve_from_client_map(chapter.book)

            encoded_data, content_type = urllib3.encode_multipart_formdata(
                {"name": chapter.name, "book_id": client_book.details["id"]}
            )
            self.client.headers["Content-Type"] = content_type
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.CHAPTERS, body=encoded_data
            )

        # if missing_chapters:
        #     self.missing_books = missing_chape  # save to update shelf location
