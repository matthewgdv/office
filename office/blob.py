from __future__ import annotations

import os
from typing import Any, Iterator

from maybe import Maybe
from subtypes import NameSpace
from pathmagic import File, Dir, PathLike

from office import resources
from .config import Config


class BlobStorage:
    """A class representing a blob storage account. Takes a connection alias which must exist in the library config settings. If none is provided, the default connection will be used."""

    def __init__(self, connection: str = None) -> None:
        import azure.storage.blob as blob

        self.config = Config()
        self.connection = Maybe(connection).else_(self.config.data.default_connections.blob)
        settings = self.config.data.connections.blob[self.connection]

        self.blob, self.service = blob, blob.BlockBlobService(account_name=settings.account, account_key=settings.key)
        self.containers = BlobContainerNameSpace(self)
        self.blob_type_mappings = File.from_resource(package=resources, name="blob_content_types", extension="json").content


class BlobContainerNameSpace(NameSpace):
    """A namespace class representing a collection of blob containers."""

    def __init__(self, blob_manager: BlobStorage) -> None:
        self._manager = blob_manager
        super().__init__({container.name: BlobContainer(container=container, blob_manager=self._manager) for container in self._manager.service.list_containers()})


class BlobContainer:
    """A class representing a blob container, with methods for accessing (supports item access) and iterating over its blobs."""

    def __init__(self, container: Any, blob_manager: BlobStorage) -> None:
        self.raw, self.name, self.manager = container, container.name, blob_manager
        self.service = self.manager.service
        self._cached_len = 0

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={repr(self.name)}, num_blobs={repr(self._cached_len or '?')})"

    def __str__(self) -> str:
        return self.name

    def __len__(self) -> int:
        self._cached_len = sum([1 for blob in self.service.list_blobs(self.name)])
        return self._cached_len

    def __bool__(self) -> bool:
        return len(self) > 0

    def __iter__(self) -> Iterator[Blob]:
        return iter(Blob(blob=name, container=self) for name in self.service.list_blobs(self.name))

    def __getitem__(self, key: str) -> Blob:
        return Blob(blob=self.service.get_blob_properties(container_name=self.name, blob_name=key), container=self)

    def download_blob_to(self, blob_name: str, path: PathLike) -> PathLike:
        """Download the named blob to the given folder. It will keep its blob 'basename' as its new name."""
        return self[blob_name].download_to(path)

    def download_blob_to_path(self, blob_name: str, path: PathLike) -> PathLike:
        """Download the named blob to the given path."""
        return self[blob_name].download_to_path(path)

    def upload_blob_from(self, blob_name: str, path: PathLike) -> Blob:
        """Create a new blob within this container in storage from the given file path."""
        from azure.storage.blob.models import ContentSettings

        file = File(path)
        content_type = self.manager.blob_type_mappings[file.extension]
        self.service.create_blob_from_path(container_name=self.name, blob_name=blob_name, file_path=str(file), content_settings=ContentSettings(content_type=content_type))

        return self[blob_name]


class Blob:
    """A class representing a blob in storage within a container, with methods for interacting with it."""

    def __init__(self, blob: Any, container: BlobContainer) -> None:
        self.raw, self.name, self.container = blob, blob.name, container
        self.service = self.container.manager.service

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={repr(self.name)}, container={repr(self.container.name)})"

    def download_to(self, path: PathLike) -> File:
        """Download this blob to the given folder. It will keep its blob 'basename' as its new name."""
        file = Dir(path).new_file(self.name)
        self.service.get_blob_to_path(container_name=self.container.name, blob_name=self.name, file_path=str(file))
        return file

    def download_to_path(self, path: PathLike) -> File:
        """Download this blob to the given path."""
        self.service.get_blob_to_path(container_name=self.container.name, blob_name=self.name, file_path=os.fspath(path))
        return File.from_pathlike(path)

    def delete(self) -> None:
        """Permanently delete this blob within its container in storage."""
        self.service.delete_blob(container_name=self.container.name, blob_name=self.name)
