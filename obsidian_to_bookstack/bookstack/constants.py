from enum import Enum


class BookstackAPIEndpoints(Enum):
    PAGES = "/api/pages"
    BOOKS = "/api/books"
    SHELVES = "/api/shelves"
    CHAPTERS = "/api/chapters"


class DetailedBookstackLink(Enum):
    ...


class BookstackItems(Enum):
    PAGE = "page"
    BOOK = "book"
    SHELF = "shelf"
    CHAPTER = "chapter"


class RequestType(Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"


class SyncType(Enum):
    LOCAL = "local"
    REMOTE = "remote"


BOOKSTACK_ATTR_MAP = {
    BookstackItems.SHELF: "shelves",
    BookstackItems.BOOK: "books",
    BookstackItems.PAGE: "pages",
    BookstackItems.CHAPTER: "chapters",
}

__all__ = [
    "BookstackAPIEndpoints",
    "DetailedBookstackLink",
    "BookstackItems",
    "RequestType",
    "SyncType",
    "BOOKSTACK_ATTR_MAP",
]
