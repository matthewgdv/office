from __future__ import annotations

from typing import List

import O365.address_book as address_book

from .contact import Contact, ContactQuery
from ..attribute import Attribute, NonFilterableAttribute
from ..query import Query, BulkAction, BulkActionContext
from ..outlook import Message


class ContactFolder(address_book.ContactFolder):
    """A class representing a Microsoft People contact folder. Can initiate queries on any contacts or folders it contains."""

    message_constructor, contact_constructor = Message, Contact

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name})"

    @property
    def folders(self) -> ContactFolderQuery:
        """A property that will create a new query against the folders contained within this folder."""
        return ContactFolderQuery(container=self)

    @property
    def contacts(self) -> ContactQuery:
        """A property that will create a new query against the contacts contained within this folder."""
        return ContactQuery(container=self)

    def from_address(self, address: str) -> Contact:
        """Return the contact with the given address if one exists. Otherwise return None."""
        return self.get_contact_by_email(address)

    class Attributes:
        class Name(Attribute):
            name = "display_name"

        class Contacts(NonFilterableAttribute):
            name = "contacts"

        class ChildFolders(NonFilterableAttribute):
            name = "child_folders"


class BulkContactFolderAction(BulkAction):
    """A class representing a bulk action performed on the resultset of a contact folder query."""

    def move(self, folder: ContactFolder) -> BulkActionContext:
        """Move all folders that match the query this bulk action was created from into the given folder."""
        return BulkActionContext(query=self._query, action=ContactFolder.move_folder, args=(folder,))

    def delete(self) -> BulkActionContext:
        """Delete all folders that match the query this bulk action was created from."""
        return BulkActionContext(query=self._query, action=ContactFolder.delete)


class ContactFolderQuery(Query):
    """A class for querying the contact folders within a given collection."""

    def __getitem__(self, key: str) -> ContactFolder:
        return self._container.get_folder(folder_name=key)

    def execute(self) -> list[Contact]:
        """Execute this query and return any folders that match."""
        return list(self._container.get_folders(limit=self._limit, query=self._query))

    @property
    def bulk(self) -> BulkContactFolderAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkContactFolderAction(self)
