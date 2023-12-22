import os

from .Book import Book


class Shelf:
    def __init__(self, path, name, client) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.books = [
            Book(path=os.path.join(self.path, book), name=book, client=self.client)
            for book in os.listdir(self.path)
        ]

    def __str__(self) -> str:
        return self.name
