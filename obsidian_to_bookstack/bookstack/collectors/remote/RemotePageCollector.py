import json
from typing import List

from obsidian_to_bookstack.bookstack.artifacts import Book, Page, Shelf
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import \
    RemoteCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console
from obsidian_to_bookstack.utils import con_hash


class RemotePageCollector(RemoteCollector):
    def __init__(self, verbose: bool, client: RemoteClient) -> None:
        super().__init__(verbose, client)

    def get_pages(self, books: List[Book], client_pages=None):
        """Get remote pages from books"""
        if not client_pages:
            client_pages = self.client._get_from_client(BookstackAPIEndpoints.PAGES)

        for page in client_pages:

            class DetailedPage(DetailedBookstackLink):
                LINK = f"/api/pages/{page['id']}"

            resp = self.client._make_request(
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

        for book in books:
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

        return pages
