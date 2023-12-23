from .bookstack.Bookstack import Bookstack
from .config import load_toml

if __name__ == "__main__":
    toml = load_toml()
    assert toml is not None

    path = toml["wiki"]["path"]
    excluded = toml["wiki"]["excluded"]["shelves"]

    b = Bookstack(path, excluded)

    b.sync_remote()
    b.sync_local()
