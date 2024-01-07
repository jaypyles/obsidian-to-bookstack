import os

import click
from dotenv import load_dotenv

from .bookstack.bookstack import Bookstack, BookstackItems
from .config import load_toml
from .console import console

if os.path.exists(".env"):
    load_dotenv()

toml = load_toml()
assert toml is not None

path = toml["wiki"]["path"]
excluded = toml["wiki"]["excluded"]["shelves"]

console.log(f"Looking at Obsidian Vault at: [bold blue]{path}[/bold blue]")

if excluded:
    console.log(f"Excluding shelves: [bold blue]{excluded}[/bold blue]")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Show verbose logs")
@click.pass_context
def cli(ctx, verbose):
    with console.status("Building client..."):
        b = Bookstack(path, excluded, verbose=verbose)
        ctx.obj = {"bookstack": b}


@cli.command(help="Call `local` and `remote`")
@click.pass_context
def sync(ctx):
    b = ctx.obj.get("bookstack")

    with console.status("Downloading any missing files..."):
        b.sync_local()

    with console.status("Uploading missing files to remote..."):
        b.sync_remote()


@cli.command(help="Upload any missing files to Bookstack")
@click.pass_context
def remote(ctx):
    with console.status("Uploading missing files to remote..."):
        b = ctx.obj.get("bookstack")
        b.sync_remote()


@cli.command(help="Download any missing files into the Obsidian Vault")
@click.pass_context
def local(ctx):
    b = ctx.obj.get("bookstack")
    with console.status("Downloading any missing files..."):
        b.sync_local()


@cli.command(help="Update files in Bookstack or Obsidian")
@click.pass_context
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
def update(ctx, remote, local):
    b = ctx.obj.get("bookstack")
    if not any([remote, local]):
        raise click.UsageError("Please provide at least one of --remote or --local")
    if remote:
        with console.status("Updating remote files..."):
            b.update_remote(remote=True, local=False)
    elif local:
        with console.status("Updating local files..."):
            b.update_remote(remote=False, local=True)


@cli.command(help="Delete Bookstack and Obsidian object")
@click.pass_context
@click.argument("path", required=True)
@click.option("--shelf", is_flag=True, help="Delete a shelf")
@click.option("--book", is_flag=True, help="Delete a book")
@click.option("--page", is_flag=True, help="Delete a page")
def delete(ctx, path, shelf, book, page):
    b = ctx.obj.get("bookstack")
    if not any([shelf, book, page]):
        raise click.UsageError(
            "Please provide at least one of --shelf, --book, or --page"
        )

    if shelf:
        with console.status(f"Deleting shelf at {path}"):
            b.delete(BookstackItems.SHELF, path)
    elif book:
        with console.status(f"Deleting book at {path}"):
            b.delete(BookstackItems.BOOK, path)
    elif page:
        with console.status(f"Deleting page at {path}"):
            b.delete(BookstackItems.PAGE, path)


def main():
    cli()


if __name__ == "__main__":
    main()
