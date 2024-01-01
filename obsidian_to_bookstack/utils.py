import hashlib


def con_hash(key: str) -> int:
    """Get a consistent hash of a key"""
    hash_obj = hashlib.md5(key.encode())
    hex_digest = hash_obj.hexdigest()
    return int(hex_digest, 16)
