from __future__ import annotations

import iotools
import office


class OfficeConfig(iotools.Config):
    """A config class granting access to an os-specific appdata directory for use by this library."""

    name = office.__name__
    default = {"default_connection": "", "connections": {}}
    systemwide = False

    # noinspection PyShadowingBuiltins
    def add_office_connection(self, connection: str, id: str, secret: str, default_email: str, is_default: bool = False) -> None:
        """Add a new office connection with the given application key, secret and default email resource."""
        self.data.connections[connection] = dict(id=id, secret=secret, default_email=default_email)
        if is_default:
            self.set_default_office_connection(connection=connection)

    def set_default_office_connection(self, connection: str):
        """Set one of the existing office connections to be the default one by its connection alias."""
        if connection in self.data.connections:
            self.data.default_connection = connection
        else:
            raise ValueError(f"Connection {connection} is not one of the currently registered connections: {', '.join(self.data.connections)}. Use {type(self).__name__}.add_connection() first.")


class BlobConfig(iotools.Config):
    """A config class granting access to an os-specific appdata directory for use by this library."""

    name = "blob"
    default = {"default_connection": "", "connections": {}}

    def add_blob_connection(self, connection: str, account: str, key: str = None, is_default: bool = False) -> None:
        """Add a new blob storage connection with the given account name and key."""
        self.data.connections[connection] = dict(url=f"https://{account}.blob.core.windows.net/", key=key)
        if is_default:
            self.set_default_blob_connection(connection=connection)

    def set_default_blob_connection(self, connection: str):
        """Set one of the existing blob storage connections to be the default one by its connection alias."""
        if connection in self.data.connections:
            self.data.default_connection = connection
        else:
            raise ValueError(f"Connection {connection} is not one of the currently registered connections: {', '.join(self.data.connections)}. Use {type(self).__name__}.add_connection() first.")
