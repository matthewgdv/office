from __future__ import annotations

from typing import Iterator, TYPE_CHECKING

from maybe import Maybe
from subtypes import NameSpace, Str
from pathmagic import File, Dir, PathLike
from miscutils import cached_property

from office.resources import blob_content_types
from .config import Config

if TYPE_CHECKING:
    from azure.storage.blob import ContainerClient, BlobClient


class BlobStorage:
    """A class representing a blob storage account. Takes a connection alias which must exist in the library config settings. If none is provided, the default connection will be used."""

    def __init__(self, connection: str = None) -> None:
        from azure.storage.blob import BlobServiceClient

        self.config = Config()
        self.connection = Maybe(connection).else_(self.config.data.default_connections.blob)
        settings = self.config.data.connections.blob[self.connection]

        self.client = BlobServiceClient(account_url=settings.account, credential=settings.key)
        self.containers = BlobContainerNameSpace(self)
        self.blob_type_mappings = blob_content_types.content_types

    def new_container(self, name: str) -> BlobContainer:
        self.client.create_container(name)
        self.containers()
        return self.containers[name]


class BlobContainerNameSpace(NameSpace):
    """A namespace class representing a collection of blob containers."""

    def __init__(self, storage: BlobStorage) -> None:
        self._storage = storage
        self()

    def __call__(self, *args, **kwargs) -> BlobContainerNameSpace:
        super().__call__({container.name: BlobContainer(name=container.name, storage=self._storage) for container in self._storage.client.list_containers()})
        return self


class BlobContainer:
    """A class representing a blob container, with methods for accessing (supports item access) and iterating over its blobs."""

    def __init__(self, name: str, storage: BlobStorage) -> None:
        self.name, self.storage = name, storage
        self._cached_len = 0

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={repr(self.name)}, num_blobs={repr(self._cached_len or '?')})"

    def __str__(self) -> str:
        return self.name

    def __len__(self) -> int:
        self._cached_len = sum([1 for blob in self.client.list_blobs(self.name)])
        return self._cached_len

    def __bool__(self) -> bool:
        return len(self) > 0

    def __iter__(self) -> Iterator[Blob]:
        return iter(Blob(name=blob.name, container=self) for blob in self.client.list_blobs())

    def __getitem__(self, key: str) -> Blob:
        return Blob(name=key, container=self)

    @cached_property
    def client(self) -> ContainerClient:
        return self.storage.client.get_container_client(self.name)

    def download_blob_to(self, name: str, folder: PathLike) -> PathLike:
        """Download the named blob to the given folder. It will keep its blob 'basename' as its new name."""
        return self[name].download_to(folder)

    def download_blob_as(self, name: str, path: PathLike) -> PathLike:
        """Download the named blob to the given path."""
        return self[name].download_as(path)

    def upload_blob_from(self, file: PathLike, name: str = None) -> Blob:
        """Create a new blob within this container in storage from the given file path."""
        file = File.from_pathlike(file)
        blob_name = file.name if name is None else name

        with open(file, "rb") as stream:
            self.client.upload_blob(name=blob_name, data=stream)

        return self[blob_name]

    def delete(self) -> None:
        if list(self):
            raise PermissionError(f"May not delete non-empty ({len(self)} blobs found) container '{self.name}'.")
        else:
            self.storage.client.delete_container(self.name)
            self.storage.containers()


class Blob:
    """A class representing a blob in storage within a container, with methods for interacting with it."""

    def __init__(self, name, container: BlobContainer) -> None:
        self.name, self.container = name, container

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={repr(self.name)}, container={repr(self.container.name)})"

    @cached_property
    def client(self) -> BlobClient:
        return self.container.client.get_blob_client(self.name)

    def download_to(self, folder: PathLike, name: str = None) -> File:
        """Download this blob to the given folder. It will keep its blob 'basename' as its new name."""
        file = Dir.from_pathlike(folder).new_file(Str(self.name).slice.after_last("/") or self.name if name is None else name)

        with open(file, "wb") as stream:
            self.client.download_blob().readinto(stream)

        return file

    def download_as(self, file: PathLike) -> File:
        """Download this blob to the given path."""
        file = File.from_pathlike(file)

        with open(file, "wb") as stream:
            self.client.download_blob().readinto(stream)

        return file

    def delete(self) -> None:
        """Permanently delete this blob within its container in storage."""
        self.client.delete_blob()
