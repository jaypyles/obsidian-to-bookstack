import hashlib
from collections.abc import Callable

from .console import console


def con_hash(key: str) -> int:
    """Get a consistent hash of a key"""
    hash_obj = hashlib.md5(key.encode())
    hex_digest = hash_obj.hexdigest()
    return int(hex_digest, 16)


def with_status(func: Callable, status_message: str):
    """Wrap a function with a status"""
    with console.status(status_message, spinner="pong"):
        return func()
