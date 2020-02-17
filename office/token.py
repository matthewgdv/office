from O365.utils.token import BaseTokenBackend


class MemoryTokenBackend(BaseTokenBackend):
    def __init__(self, token: dict) -> None:
        super().__init__()
        self.token = token

    def load_token(self):
        return self.token

    def save_token(self):
        pass
