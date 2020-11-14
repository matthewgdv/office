from __future__ import annotations

from io import BytesIO
from typing import Iterator, TYPE_CHECKING

from subtypes import NameSpace, Str, Dict
from pathmagic import File, Dir, PathLike
from miscutils import cached_property, ReprMixin

from .config import BlobConfig as Config

if TYPE_CHECKING:
    from azure.storage.blob import ContainerClient, BlobClient


class BlobStorage:
    """A class representing a blob storage account. Takes a connection alias which must exist in the library config settings. If none is provided, the default connection will be used."""

    def __init__(self, url: str, key: str) -> None:
        from azure.storage.blob import BlobServiceClient

        self.config = Config()
        self.client = BlobServiceClient(account_url=url, credential=key)
        self.containers = BlobContainerNameSpace(self)

    def new_container(self, name: str) -> BlobContainer:
        self.client.create_container(name)
        self.containers()
        return self.containers[name]

    def blob_from_url(self, url: str) -> Blob:
        container, blob = Str(url).slice.after(f"{self.client.primary_hostname}/").split("/", 1)
        return self.containers[container][blob]

    @classmethod
    def from_connection(cls, connection: str = None) -> BlobStorage:
        config = Config()
        connection = connection or config.data.default_connection
        credentials = config.data.connections[connection]
        return cls(url=credentials.url, key=credentials.key)


class BlobContainerNameSpace(NameSpace):
    """A namespace class representing a collection of blob containers."""

    def __init__(self, storage: BlobStorage) -> None:
        self._storage = storage
        self()

    def __call__(self, *args, **kwargs) -> BlobContainerNameSpace:
        super().__call__({container.name: BlobContainer(name=container.name, storage=self._storage) for container in self._storage.client.list_containers()})
        return self

    def __getitem__(self, name: str) -> BlobContainer:
        return super().__getitem__(name=name)


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

    @cached_property
    def properties(self) -> Dict:
        return Dict(self.client.get_container_properties())

    def upload_file(self, file: PathLike, name: str = None) -> UploadAccessor:
        return self[name if name else File.from_pathlike(file).name].upload.from_file(file)

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
        return f"{type(self).__name__}(name={repr(self.name)}, container={repr(self.container.name)}, exists={bool(self)})"

    def __bool__(self) -> bool:
        return self.exists()

    @cached_property
    def client(self) -> BlobClient:
        return self.container.client.get_blob_client(self.name)

    @cached_property
    def properties(self) -> Dict:
        return Dict(self.client.get_blob_properties())

    @property
    def url(self) -> str:
        return self.client.url

    @cached_property
    def upload(self) -> UploadAccessor:
        return UploadAccessor(parent=self)

    @cached_property
    def download(self) -> DownloadAccessor:
        return DownloadAccessor(parent=self)

    def delete(self) -> None:
        """Permanently delete this blob within its container in storage."""
        self.client.delete_blob()

    def exists(self) -> bool:
        try:
            if self.properties:
                return True
        except Exception:
            return False


class UploadAccessor(ReprMixin):
    def __init__(self, parent: Blob) -> None:
        self.parent = parent
        self()

    def __call__(self, overwrite: bool = False) -> UploadAccessor:
        self.overwrite = overwrite
        return self

    def from_file(self, file: PathLike) -> Blob:
        """Create a new blob within this container in storage from the given file path."""
        file = File.from_pathlike(file)

        with open(file, "rb") as stream:
            self.parent.client.upload_blob(data=stream, overwrite=self.overwrite)

        return self.parent

    def from_bytes(self, data: bytes) -> Blob:
        """Create a new blob within this container in storage from the given file path."""
        self.parent.client.upload_blob(data=data, overwrite=self.overwrite)
        return self.parent

    def from_stream(self, stream: BytesIO) -> Blob:
        """Create a new blob within this container in storage from the given file path."""
        stream.seek(0)
        self.parent.client.upload_blob(data=stream, overwrite=self.overwrite)
        return self.parent


class DownloadAccessor(ReprMixin):
    def __init__(self, parent: Blob) -> None:
        self.parent = parent
        self()

    def __call__(self) -> UploadAccessor:
        return self

    def to_folder(self, folder: PathLike, name: str = None) -> File:
        """Download this blob to the given folder. It will keep its blob 'basename' as its new name."""
        file = Dir.from_pathlike(folder).new_file(Str(self.parent.name).slice.after_last("/") or self.parent.name if name is None else name)

        with open(file, "wb") as stream:
            self.parent.client.download_blob().readinto(stream)

        return file

    def as_file(self, file: PathLike) -> File:
        """Download this blob to the given path."""
        file = File.from_pathlike(file)

        with open(file, "wb") as stream:
            self.parent.client.download_blob().readinto(stream)

        return file

    def as_bytes(self) -> bytes:
        return self.parent.client.download_blob().readall()

    def as_stream(self, stream: BytesIO = None) -> BytesIO:
        stream = stream or BytesIO()
        self.parent.client.download_blob().readinto(stream)
        stream.seek(0)
        return stream
