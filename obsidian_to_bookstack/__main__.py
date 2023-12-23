import logging

from .bookstack.Bookstack import Bookstack, BookstackClient
from .config import load_toml

if __name__ == "__main__":
    toml = load_toml()
    assert toml is not None

    path = toml["wiki"]["path"]
    print(path)

    b = Bookstack(path)

    # for s in b.shelves:
    #     print(s)
    #     for book in s.books:
    #         print(book)
    #         for p in book.pages:
    #             print(p)

    # print(b.client.shelves)
    # print(b.client.books)
    # print(b.client.pages)

    # print(b.books)
    # print(b.shelves)
    # print(b.pages)

    # b.sync_local()
    b.sync_remote()
