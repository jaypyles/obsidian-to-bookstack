import os

import click
from dotenv import load_dotenv

from .bookstack.bookstack import Bookstack, BookstackItems
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
@click.option(
    "-r",
    "--remote",
    flag_value="remote",
    is_flag=True,
    help="Update remote pages from local copies",
)
@click.option(
    "-l",
    "--local",
    flag_value="local",
    is_flag=True,
    help="Update local pages from from copies",
)
def update(remote, local):
    if not any([remote, local]):
        raise click.UsageError("Please provide at least one of --remote or --local")
    if remote:
        b.update_remote(remote=True, local=False)
    elif local:
        b.update_remote(remote=False, local=True)


@cli.command()
@click.argument("path", required=True)
@click.option("--shelf", is_flag=True, help="Delete a shelf")
@click.option("--book", is_flag=True, help="Delete a book")
@click.option("--page", is_flag=True, help="Delete a page")
def delete(path, shelf, book, page):
    if not any([shelf, book, page]):
        raise click.UsageError(
            "Please provide at least one of --shelf, --book, or --page"
        )

    if shelf:
        click.echo(f"Deleting shelf at {path}")
        b.delete(BookstackItems.SHELF, path)
    elif book:
        click.echo(f"Deleting book at {path}")
        b.delete(BookstackItems.BOOK, path)
    elif page:
        click.echo(f"Deleting page at {path}")
        b.delete(BookstackItems.PAGE, path)


def main():
    cli()


if __name__ == "__main__":
    main()
