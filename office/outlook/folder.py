from __future__ import annotations

from typing import Any, List, Union, TYPE_CHECKING

import O365.mailbox as mailbox

from miscutils import lazy_property

from .message import Message, MessageQuery
from ..attribute import Attribute, NonFilterableAttribute
from ..query import Query, BulkAction, BulkActionContext

if TYPE_CHECKING:
    from .office import Office


class MessageFolder(mailbox.Folder):
    """A class representing a Microsoft Outlook message folder. Can initiate queries on any messages or folders it contains."""

    message_constructor = Message

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

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


class MessageFolderAccessor:
    """A class representing the collection of the default Outlook message folders. Custom folders can be accessed via the the MessageFolders.custom() method."""

    def __init__(self, office: Office) -> None:
        self.office = office
        self._mailbox = office.account.mailbox()
        self._mailbox.folder_constructor = MessageFolder

    def __getitem__(self, key: Union[str, int]) -> MessageFolder:
        return self.custom(folder_name=key) if isinstance(key, str) else (self.custom(folder_id=key) if isinstance(key, int) else None)

    @lazy_property
    def main(self) -> MessageFolder:
        """A property that returns the main folder."""
        return MessageFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name='MailBox', root=True, office=self.office)

    @lazy_property
    def inbox(self) -> MessageFolder:
        """A property that returns the inbox folder."""
        folder = self._mailbox.inbox_folder()
        folder.office = self.office
        return folder

    @lazy_property
    def outbox(self) -> MessageFolder:
        """A property that returns the outbox folder."""
        folder = self._mailbox.outbox_folder()
        folder.office = self.office
        return folder

    @lazy_property
    def sent(self) -> MessageFolder:
        """A property that returns the sent folder."""
        folder = self._mailbox.sent_folder()
        folder.office = self.office
        return folder

    @lazy_property
    def drafts(self) -> MessageFolder:
        """A property that returns the drafts folder."""
        folder = self._mailbox.drafts_folder()
        folder.office = self.office
        return folder

    @lazy_property
    def junk(self) -> MessageFolder:
        """A property that returns the junk folder."""
        folder = self._mailbox.junk_folder()
        folder.office = self.office
        return folder

    @lazy_property
    def deleted(self) -> MessageFolder:
        """A property that returns the deleted folder."""
        folder = self._mailbox.deleted_folder()
        folder.office = self.office
        return folder

    def custom(self, folder_name: str = None, folder_id: int = None) -> MessageFolder:
        """Return the given custom folder by name or id."""
        folder = self._mailbox.get_folder(folder_name=folder_name, folder_id=folder_id)
        folder.office = self.office
        return folder


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
        folder = self._container.get_folder(folder_name=key)
        folder.office = self._container.office
        return folder

    def execute(self) -> List[Message]:
        """Execute this query and return any folders that match."""
        folders = list(self._container.get_folders(limit=self._limit, query=self._query))
        for folder in folders:
            folder.office = self._container.office

        return folders

    @property
    def bulk(self) -> BulkMessageFolderAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkMessageFolderAction(self)
