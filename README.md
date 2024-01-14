# Summary

Download remote files from Bookstack instance, that you may not have, along with sending any changes to the remote.
After configuration, consider installing the companion plugin at https://github.com/jaypyles/ObsidianToBookstackPlugin.

# 🆕 What's New

- All commands will now also be available to use with chapters. This means that
  a structure like this is now allowed:

```
- Shelf/
-- Book/
--- Chapter/
---- Note.md
--- Note.md
```

# Installing

Run with `pipx install .` inside the project to install to your machine.

# Config

You can use a `.env` file in the root of your project for the following secrets:

`BOOKSTACK_BASE_URL="https://demo.bookstack.com"`

`BOOKSTACK_TOKEN_ID=<your_bookstack_api_token_id>`

`BOOKSTACK_TOKEN_SECRET=<your_bookstack_api_token_secret>`

or you may choose to use whatever secret manager you want, like Doppler, so long as it sets those environment variables.

Make sure to setup a conf.toml in ~/.config/obsidian_to_bookstack, example:

## Configuring CLI Options

The CLI tool provides various options for configuration using the `click` library in Python. Here's a breakdown of the available options:

- **Verbose Mode**

  - `-v`, `--verbose`: This optional flag enables verbose logs, providing more detailed information during command execution.

- **Config File**

  - `-c`, `--config`: Specify the path to a configuration file (`config`). If provided, the CLI will load settings from this file. If not specified, default settings will be used.

- **Environment File**
  - `-e`, `--env`: Specify the path to an environment file (`env`) containing variables, such as API tokens or other sensitive information. This allows for easy management of environment-specific configurations.

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
    - Chapter
      - Pages.md
    - Pages.md
```

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

- Statistical/table view of uploaded, downloaded, deleted, or updated objects
