import os

from .Book import Book


class Shelf:
    def __init__(self, path, name, client) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.books = self._set_books()

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
                )
                books.append(b)

        return books
