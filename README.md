# Summary

Download remote files from Bookstack instance, that you may not have, along with sending any changes to the remote.

# 🆕 What's New

- Logging (with verbosity option)

Ex: running obsidian_to_bookstack commands will now show progress and running with `-v` and `--verbose` will show more detail.
`obsidian_to_bookstack -v sync`

# Installing

Run with `pipx install .` inside the project to install to your machine.

# Config

You can use a `.env` file in the root of your project for the following secrets:

`BOOKSTACK_BASE_URL="https://demo.bookstack.com"`

`BOOKSTACK_TOKEN_ID=<your_bookstack_api_token_id>`

`BOOKSTACK_TOKEN_SECRET=<your_bookstack_api_token_secret>`

or you may choose to use whatever secret manager you want, like Doppler, so long as it sets those environment variables.

Make sure to setup a conf.toml in the root of your project, example:

```toml
[wiki]
path = "/home/user/notes/"

[wiki.excluded]
shelves = ["private"]
```

Any shelves in `wiki.excluded.shelves` will not be uploaded to Bookstack.

## Structure

The structure of the Obsidian Vault is pretty specific as it mirrors the Bookstack structure to be as in sync as possible.

```
- Shelves
  - Books
    - Pages.md
```

I may in the future add extra support for pages with no books, along with more nested structure. Bookstack does currently support "chapters" in Books, but this does not support that currently.

## Commands

### Sync

Calls `local` and `remote`

### Local

Pulls down any missing local files

### Remote

Pushes up any missing files in the remote

### Update

Requires either the `--remote` or the `--local` flag.
If `--remote` is specified, any files which have been updated locally will be changed in the remote and vice-versa for `--local`.

### Delete

Requires one of `--shelf`, `--book`, `--page`. Will delete Obsidian files and Bookstack files at the same time. Anything nested under a shelf or book will also be deleted.
Must be called in a path like structure. Ex:

```bash
- Shelf
  - Book
    - Page.md
```

The command would be called as `obsidian_to_bookstack delete Shelf/Book/Page --page` to delete a page.

## In Progress

- Chapter suppport
