import os
from typing import Dict, List

from .client import Client


class Shelf:
    def __init__(
        self,
        name: str,
        client: Client | None = None,
        from_client: bool = True,
        path: str = "",
        details: Dict = {},
    ) -> None:
        self.path = path
        self.name = name
        self.client = client
        if from_client:
            self.books = []
        else:
            self.books = self._set_books()
        self.client_books: list[dict] = []
        self.details = details

    def __str__(self) -> str:
        return self.name

    def _set_books(self):
        books = []
        for book in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path, book)) and not book.startswith(
                "."
            ):
                b = Book(
                    path=os.path.join(self.path, book),
                    name=book,
                    client=self.client,
                    shelf=self,
                    from_client=False,
                )
                books.append(b)

        return books


class Book:
    def __init__(
        self,
        name: str,
        shelf: Shelf | None = None,
        client: Client | None = None,
        chapters: List = [],
        path: str = "",
        details: Dict = {},
        from_client: bool = True,
    ) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.shelf = shelf
        self.chapters = chapters
        self.details = details
        if from_client:
            self.pages = []
        else:
            self._set_pages()

    def __str__(self) -> str:
        return self.name

    def _set_pages(self):
        pages = []
        chapters = []

        for item in os.listdir(self.path):
            item_path = os.path.join(self.path, item)
            if os.path.isdir(item_path):
                chapters.append(
                    Chapter(
                        path=os.path.join(self.path, item),
                        name=item,
                        client=self.client,
                        shelf=self.shelf,
                        book=self,
                        from_client=False,
                    )
                )
            else:
                if os.path.splitext(item)[1] == ".md":
                    pages.append(
                        Page(
                            path=os.path.join(self.path, item),
                            name=item,
                            client=self.client,
                            shelf=self.shelf,
                            book=self,
                        )
                    )

        self.pages = pages
        self.chapters = chapters


class Chapter:
    def __init__(
        self,
        name: str,
        shelf: Shelf | None = None,
        book: Book | None = None,
        client: Client | None = None,
        path: str = "",
        details: Dict = {},
        from_client: bool = True,
    ) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.shelf = shelf
        self.book = book
        self.details = details
        if from_client:
            self.pages = []
        else:
            self._set_pages()

    def __str__(self) -> str:
        return self.name

    def _set_pages(self):
        pages = []
        for page in os.listdir(self.path):
            if os.path.splitext(page)[1] == ".md":
                p = Page(
                    path=os.path.join(self.path, page),
                    name=page,
                    client=self.client,
                    book=self.book,
                    chapter=self,
                )
                pages.append(p)

        self.pages = pages


class Page:
    def __init__(
        self,
        name: str,
        path: str = "",
        client: Client | None = None,
        shelf: Shelf | None = None,
        book: Book | None = None,
        chapter: Chapter | None = None,
        details: Dict = {},
    ) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.content = self._get_content() if self.path else ""
        self.shelf = shelf
        self.book = book
        self.chapter = chapter
        self.details = details

    def __str__(self) -> str:
        return self.name

    def _get_content(self):
        with open(self.path, "r") as f:
            return f.read()
