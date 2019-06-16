from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING

from maybe import Maybe
from pathmagic import File, PathLike
from miscutils import NameSpace

if TYPE_CHECKING:
    from .office import BlobStorage


class BlobContainerNameSpace(NameSpace):
    def __init__(self, blob_manager: BlobStorage) -> None:
        self._manager = blob_manager
        super().__init__({container.name: BlobContainer(container=container, blob_manager=self._manager) for container in self._manager.service.list_containers()})


class BlobContainer:
    def __init__(self, container: Any, blob_manager: BlobStorage) -> None:
        self.raw, self.name, self.manager = container, container.name, blob_manager
        self.service = self.manager.service

        self._cached_len = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name}, num_blobs={Maybe(self._cached_len).else_('?')})"

    def __str__(self) -> str:
        return self.name

    def __len__(self) -> int:
        self._cached_len = sum([1 for blob in self.service.list_blob_names(self.name)])
        return self._cached_len

    def __bool__(self) -> bool:
        return len(self) > 0

    def __iter__(self) -> BlobContainer:
        self.__iter = iter(self.service.list_blobs(self.name))
        return self

    def __next__(self) -> Any:
        return Blob(blob=next(self.__iter), container=self)

    def __getitem__(self, key: str) -> Blob:
        return Blob(blob=self.service.get_blob_properties(container_name=self.name, blob_name=key), container=self)

    def download_blob_to(self, blob_name: str, path: PathLike) -> PathLike:
        self[blob_name].download_to(path)
        return File.from_pathlike(path)

    def upload_blob_from(self, blob_name: str, path: PathLike) -> Blob:
        self.service.create_blob_from_path(container_name=self.container.name, blob_name=self.name, file_path=os.fspath(path))


class Blob:
    def __init__(self, blob: Any, container: BlobContainer) -> None:
        self.raw, self.name, self.container = blob, blob.name, container
        self.service = self.container.manager.service

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name}, container={self.container.name})"

    def download_to(self, path: PathLike) -> PathLike:
        self.service.get_blob_to_path(container_name=self.container.name, blob_name=self.name, file_path=os.fspath(path))
        return File.from_pathlike(path)
