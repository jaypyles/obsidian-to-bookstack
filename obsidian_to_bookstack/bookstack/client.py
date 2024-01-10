import os
from abc import ABC, abstractmethod

import urllib3

from .constants import *


class Client(ABC):
    ...


class RemoteClient(Client):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.id = os.getenv("BOOKSTACK_TOKEN_ID")
        self.secret = os.getenv("BOOKSTACK_TOKEN_SECRET")
        self.base_url = os.getenv("BOOKSTACK_BASE_URL")
        self.headers = {"Authorization": f"Token {self.id}:{self.secret}"}
        self.http = urllib3.PoolManager()

    def _make_request(
        self,
        request_type: RequestType,
        endpoint: BookstackAPIEndpoints | DetailedBookstackLink,
        body=None,
        json=None,
    ) -> urllib3.BaseHTTPResponse:
        """Make a HTTP request to a Bookstack API Endpoint"""

        assert self.base_url

        request_url = self.base_url + endpoint.value
        resp = self.http.request(
            request_type.value, request_url, headers=self.headers, body=body, json=json
        )
        return resp


class LocalClient(Client):
    ...
