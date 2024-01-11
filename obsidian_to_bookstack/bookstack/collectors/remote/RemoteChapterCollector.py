import json
from typing import List

from obsidian_to_bookstack.bookstack.artifacts import (Book, Chapter, Page,
                                                       Shelf)
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import \
    RemoteCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console
from obsidian_to_bookstack.utils import con_hash


class RemoteChapterCollector(RemoteCollector):
    def get_chapters(self, books: List[Book]):
        """Get remote chapters from books"""
        client_chapters = self.client._get_from_client(BookstackAPIEndpoints.CHAPTERS)

        for chapter in client_chapters:

            class DetailedChapter(DetailedBookstackLink):
                LINK = f"/api/chapters/{chapter['id']}"

            resp = self.client._make_request(
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

        for book in books:
            print(f"Book Details: {book.details}")
            if book.details.get("contents"):
                for item in book.details["contents"]:
                    if item["type"] == "chapter":
                        c = CHAPTER_MAP.get(con_hash(item["name"] + str(item["id"])))
                        if c:
                            c.book = book
                            book.chapters.append(c)

                            if item.get("pages"):
                                self.client.pages.extend(
                                    self.client.page_collector.get_pages(
                                        self.client.books, client_pages=item["pages"]
                                    )
                                )

                        if self.verbose:
                            console.log(f"Found chapter page: {c}")

        return chapters
