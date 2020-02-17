from O365.utils.token import BaseTokenBackend


class MemoryTokenBackend(BaseTokenBackend):
    def __init__(self, token: dict) -> None:
        super().__init__()
        self.token = token
