from __future__ import annotations

import miscutils
import office


class Config(miscutils.Config):
    app_name = office.__name__
    default = {"default_connection": "", "connections": {}}

    def add_connection(self, connection: str, account: str, key: str = None, is_default: bool = False) -> None:
        self.data.connections[connection] = miscutils.NameSpaceDict(account=account, key=key)
        if is_default:
            self.set_default_connection(connection=connection)

    def set_default_connection(self, connection: str):
        if connection in self.data.connections:
            self.data.default_connection = connection
        else:
            raise ValueError(f"Connection {connection} is not one of the currently registered connections: {', '.join(self.data.connections)}. Use {type(self).__name__}.add_connection() first.")
