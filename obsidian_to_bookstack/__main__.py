import os

import click
from dotenv import load_dotenv

from .bookstack.Bookstack import Bookstack
from .config import load_toml

if os.path.exists(".env"):
    load_dotenv()

toml = load_toml()
assert toml is not None

path = toml["wiki"]["path"]
excluded = toml["wiki"]["excluded"]["shelves"]

b = Bookstack(path, excluded)


@click.group()
def cli():
    pass


@cli.command()
def sync():
    b.sync_local()
    b.sync_remote()


@cli.command()
def remote():
    b.sync_remote()


@cli.command()
def local():
    b.sync_local()


@cli.command()
def update():
    b.update_remote()


def main():
    cli()


if __name__ == "__main__":
    main()
