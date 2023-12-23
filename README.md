# Summary

Download remote files from Bookstack instance, that you may not have, along with sending any changes to the remote.

# Installing

Run with `pipx install .` inside the project to install to your machine.

# Config

You can use a `.env` file in the root of your project for the following secrets:

`BOOKSTACK_BASE_URL="https://demo.bookstack.com"`
`BOOKSTACK_TOKEN_ID=<your_bookstack_api_token_id>`
`BOOKSTACK_TOKEN_SECRET=<your_bookstack_api_token_secret>`

or you may choose to use whatever secret manager you want, like Doppler, so long as it sets those environment variables.

conf.toml

```toml
[wiki]
url = "https://demo.bookstack.com"
path = "/home/user/notes/"

[wiki.excluded]
shelves = ["private"]
```

## Structure

The structure of the Obsidian Vault is pretty specific as it mirrors the Bookstack structure to be as in sync as possible.

```
- shelves
-- books
--- pages.md
```

I may in the future add extra support for pages with no books, along with more nested structure. Bookstack does currently support "chapters" in Books, but this does not support that currently.

## Commmands

### Sync

Updates both local and remote changes.

### Local

Updates any local changes to the remote.

### Remote

Updates any remote changes to the local store.
