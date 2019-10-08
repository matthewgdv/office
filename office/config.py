from __future__ import annotations

import miscutils
import office


class Config(miscutils.Config):
    app_name = office.__name__
    default = {"default_connections": {"office": "", "blob": ""}, "connections": {"office": {}, "blob": {}}}

    def add_office_connection(self, connection: str, id: str, secret: str = None, is_default: bool = False) -> None:
        self.data.connections.office[connection] = miscutils.NameSpaceDict(id=id, secret=secret)
        if is_default:
            self.set_default_office_connection(connection=connection)

    def set_default_office_connection(self, connection: str):
        if connection in self.data.connections.office:
            self.data.default_connections.office = connection
        else:
            raise ValueError(f"Connection {connection} is not one of the currently registered connections: {', '.join(self.data.connections.office)}. Use {type(self).__name__}.add_connection() first.")

    def add_blob_connection(self, connection: str, account: str, key: str = None, is_default: bool = False) -> None:
        self.data.connections.blob[connection] = miscutils.NameSpaceDict(account=account, key=key)
        if is_default:
            self.set_default_blob_connection(connection=connection)

    def set_default_blob_connection(self, connection: str):
        if connection in self.data.connections.blob:
            self.data.default_connections.blob = connection
        else:
            raise ValueError(f"Connection {connection} is not one of the currently registered connections: {', '.join(self.data.connections.blob)}. Use {type(self).__name__}.add_connection() first.")
