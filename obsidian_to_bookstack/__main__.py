import logging

from obsidian_to_bookstack.bookstack import Bookstack
from obsidian_to_bookstack.config import load_toml

if __name__ == "__main__":
    toml = load_toml()
    assert toml is not None

    path = toml["wiki"]["path"]
    print(path)

    b = Bookstack(path)

    for s in b.shelves:
        print(s)
        for book in s.books:
            print(book)
            for p in book.pages:
                print(p)
