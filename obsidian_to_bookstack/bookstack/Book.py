import os

from .Page import Page


class Book:
    def __init__(self, path, name, client) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.pages = [
            Page(path=os.path.join(self.path, page), name=page, client=self.client)
            for page in os.listdir(self.path)
        ]

    def __str__(self) -> str:
        return self.name
