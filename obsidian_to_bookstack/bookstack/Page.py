class Page:
    def __init__(self, path, name, client, book) -> None:
        self.path = path
        self.name = name
        self.client = client
        self.content = self._get_content()
        self.book = book

    def __str__(self) -> str:
        return self.name

    def _get_content(self):
        with open(self.path, "r") as f:
            return f.read()
