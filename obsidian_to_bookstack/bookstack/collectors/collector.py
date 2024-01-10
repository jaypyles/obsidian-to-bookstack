import os
from abc import ABC, abstractmethod
from typing import Type

from ..client import RemoteClient
from ..constants import *


class BaseCollector(ABC):
    @abstractmethod
    def __init__(self, verbose: bool) -> None:
        super().__init__()
        self.verbose = verbose


class LocalCollector(BaseCollector):
    @abstractmethod
    def __init__(
        self, client: RemoteClient, path: str, excluded: list, verbose: bool
    ) -> None:
        super().__init__(verbose)
        self.client = client
        self.path = path
        self.excluded = excluded

    def _get_missing_set(self, item: BookstackItems, sync_type: SyncType):
        """Returns a missing set of items, can either compare to local or remote. Returns list of missing items."""
        attr = BOOKSTACK_ATTR_MAP[item]

        items = getattr(self, attr)
        client_items = getattr(self.client, attr)

        item_names = set(os.path.splitext(item.name)[0] for item in items)
        client_item_names = set(item.name for item in client_items)

        if sync_type == SyncType.LOCAL:
            missing = client_item_names - item_names
            missing_items = [ci for ci in client_items if ci.name in missing]
        else:
            missing = item_names - client_item_names
            missing_items = [
                ci for ci in items if os.path.splitext(ci.name)[0] in missing
            ]

        return missing_items


class RemoteCollector(BaseCollector):
    ...
