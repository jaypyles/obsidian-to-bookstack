import os
from typing import List

import urllib3

from obsidian_to_bookstack.bookstack.artifacts import Shelf
from obsidian_to_bookstack.bookstack.client import RemoteClient
from obsidian_to_bookstack.bookstack.collectors.collector import LocalCollector
from obsidian_to_bookstack.bookstack.constants import *
from obsidian_to_bookstack.console import console


class LocalShelfCollector(LocalCollector):
    """Performs operations with Shelves pertaining to the local Obsidian Vault"""

    def __init__(
        self, local, client: RemoteClient, path: str, excluded: list, verbose: bool
    ) -> None:
        super().__init__(local, client, path, excluded, verbose)

    def set_shelves(self) -> List[Shelf]:
        """Set shelves from Obsidian Vault local directory"""
        shelves = []
        for shelf in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path, shelf)) and shelf != ".obsidian":
                if not shelf.startswith(".") and shelf not in self.excluded:
                    s = Shelf(
                        path=os.path.join(self.path, shelf),
                        name=shelf,
                        client=self.client,
                        from_client=False,
                    )
                    shelves.append(s)

        return shelves

    def create_local_missing_shelves(self):
        """Create any missing shelves in the local store"""
        missing_shelves = self._get_missing_set(BookstackItems.SHELF, SyncType.LOCAL)
        for shelf in missing_shelves:
            path = os.path.join(self.path, shelf.name)
            os.mkdir(path)

            if self.verbose:
                console.log(f"Creating a shelf at: {path}")

    def create_remote_missing_shelves(self):
        """Create any shelves in the remote which are missing"""
        missing_shelves = self._get_missing_set(BookstackItems.SHELF, SyncType.REMOTE)
        for shelf in missing_shelves:
            if self.verbose:
                console.log(f"Bookstack missing shelf: {shelf}")

            encoded_data, content_type = urllib3.encode_multipart_formdata(
                {"name": shelf.name}
            )
            self.client.headers["Content-Type"] = content_type
            self.client._make_request(
                RequestType.POST, BookstackAPIEndpoints.SHELVES, body=encoded_data
            )
