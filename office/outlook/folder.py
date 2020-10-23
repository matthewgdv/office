from __future__ import annotations

from typing import List

import O365.mailbox as mailbox

from .message import Message, MessageQuery
from ..attribute import Attribute, NonFilterableAttribute
from ..query import Query, BulkAction, BulkActionContext


class MessageFolder(mailbox.Folder):
    """A class representing a Microsoft Outlook message folder. Can initiate queries on any messages or folders it contains."""

    message_constructor = Message

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name})"

    @property
    def folders(self) -> MessageFolderQuery:
        """A property that will create a new query against the folders contained within this folder."""
        return MessageFolderQuery(container=self)

    @property
    def messages(self) -> MessageQuery:
        """A property that will create a new query against the messages contained within this folder."""
        return MessageQuery(container=self)

    @staticmethod
    def order_messages_by_date(messages: list, descending: bool = True) -> list:
        """Order a collection of messages by datetime received."""
        return sorted(messages, reverse=descending, key=lambda val: val.received)

    class Attributes:
        class ChildFolderCount(Attribute):
            name = "child_folder_count"

        class TotalItemCount(Attribute):
            name = "total_item_count"

        class UnreadItemCount(Attribute):
            name = "unread_item_count"

        class Name(Attribute):
            name = "display_name"

        class ChildFolders(NonFilterableAttribute):
            name = "child_folders"

        class Messages(NonFilterableAttribute):
            name = "messages"


class BulkMessageFolderAction(BulkAction):
    """A class representing a bulk action performed on the resultset of a message folder query."""

    def move(self, folder: MessageFolder) -> BulkActionContext:
        """Move all folders that match the query this bulk action was created from into the given folder."""
        return BulkActionContext(query=self._query, action=MessageFolder.move_folder, args=(folder,))

    def delete(self) -> BulkActionContext:
        """Delete all folders that match the query this bulk action was created from."""
        return BulkActionContext(query=self._query, action=MessageFolder.delete)

    def copy(self, folder: MessageFolder) -> BulkActionContext:
        """Copy all folders that match the query this bulk action was created from into the given folder."""
        return BulkActionContext(query=self._query, action=MessageFolder.copy_folder, args=(folder,))


class MessageFolderQuery(Query):
    """A class for querying the message folders within a given collection."""

    def __getitem__(self, key: str) -> MessageFolder:
        return self._container.get_folder(folder_name=key)

    def execute(self) -> list[Message]:
        """Execute this query and return any folders that match."""
        return list(self._container.get_folders(limit=self._limit, query=self._query))

    @property
    def bulk(self) -> BulkMessageFolderAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkMessageFolderAction(self)
