from __future__ import annotations

from typing import Any, List, Union, TYPE_CHECKING

import O365.mailbox as mailbox
import O365.address_book as address_book

from miscutils import LazyProperty

from .attribute import Attribute, NonFilterableAttribute
from .message import Message, MessageQuery
from .contact import Contact, ContactQuery
from .query import Query, BulkAction, BulkActionContext

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


class ContactFolder(address_book.ContactFolder):
    """A class representing a Microsoft People contact folder. Can initiate queries on any contacts or folders it contains."""

    message_constructor, contact_constructor = Message, Contact

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

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
        contact = self.get_contact_by_email(address)
        if contact is None:
            return None
        else:
            contact.office = self.office
            return contact

    class Attributes:
        class Name(Attribute):
            name = "display_name"

        class Contacts(NonFilterableAttribute):
            name = "contacts"

        class ChildFolders(NonFilterableAttribute):
            name = "child_folders"


class FolderCollection:
    """An abstract base class representing a collection of folders."""

    def __init__(self, office: Office) -> None:
        self.office = office


class MessageFolders(FolderCollection):
    """A class representing the collection of the default Outlook message folders. Custom folders can be accessed via the the MessageFolders.custom() method."""

    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._mailbox = office.account.mailbox()
        self._mailbox.folder_constructor = MessageFolder

    @LazyProperty
    def main(self) -> MessageFolder:
        """A property that returns the main folder."""
        return MessageFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name='MailBox', root=True, office=self.office)

    @LazyProperty
    def inbox(self) -> MessageFolder:
        """A property that returns the inbox folder."""
        folder = self._mailbox.inbox_folder()
        folder.office = self.office
        return folder

    @LazyProperty
    def outbox(self) -> MessageFolder:
        """A property that returns the outbox folder."""
        folder = self._mailbox.outbox_folder()
        folder.office = self.office
        return folder

    @LazyProperty
    def sent(self) -> MessageFolder:
        """A property that returns the sent folder."""
        folder = self._mailbox.sent_folder()
        folder.office = self.office
        return folder

    @LazyProperty
    def drafts(self) -> MessageFolder:
        """A property that returns the drafts folder."""
        folder = self._mailbox.drafts_folder()
        folder.office = self.office
        return folder

    @LazyProperty
    def junk(self) -> MessageFolder:
        """A property that returns the junk folder."""
        folder = self._mailbox.junk_folder()
        folder.office = self.office
        return folder

    @LazyProperty
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


class ContactFolders(FolderCollection):
    """A class representing the collection of the default Outlook contact folders."""

    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._book = office.account.address_book()
        self._book.contact_constructor, self._book.message_constructor = Contact, Message

    @LazyProperty
    def main(self) -> ContactFolder:
        """A property that returns the main folder."""
        return ContactFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name='AddressBook', root=True, office=self.office)

    @LazyProperty
    def global_(self) -> ContactFolder:
        """A property that returns the global address list."""
        folder = self.office.account.address_book(address_book="gal")
        folder.office = self.office
        folder.contact_constructor = Contact
        return folder


class BulkFolderAction(BulkAction):
    """A class representing a bulk action performed on the resultset of a folder query."""

    def move(self, folder: Union[MessageFolder, ContactFolder]) -> BulkActionContext:
        """Move all folders that match the query this bulk action was created from into the given folder."""
        return BulkActionContext(query=self._query, action=MessageFolder.move_folder, args=(folder,))

    def delete(self) -> BulkActionContext:
        """Delete all folders that match the query this bulk action was created from."""
        return BulkActionContext(query=self._query, action=MessageFolder.delete)


class BulkMessageFolderAction(BulkFolderAction):
    """A class representing a bulk action performed on the resultset of a message folder query."""

    def copy(self, folder: MessageFolder) -> BulkActionContext:
        """Copy all folders that match the query this bulk action was created from into the given folder."""
        return BulkActionContext(query=self._query, action=MessageFolder.copy_folder, args=(folder,))


class BulkContactFolderAction(BulkFolderAction):
    """A class representing a bulk action performed on the resultset of a contact folder query."""


class FolderQuery(Query):
    """A class for querying the contents of a given collection."""

    def __getitem__(self, key: str) -> Union[MessageFolder, ContactFolder]:
        raise NotImplementedError

    def execute(self) -> List[Message]:
        """Execute this query and return any folders that match."""
        folders = list(self._container.get_folders(limit=self._limit, query=self._query))
        for folder in folders:
            folder.office = self._container.office

        return folders


class MessageFolderQuery(FolderQuery):
    """A class for querying the message folders within a given collection."""

    def __getitem__(self, key: str) -> MessageFolder:
        folder = self._container.get_folder(folder_name=key)
        folder.office = self._container.office
        return folder

    @property
    def bulk(self) -> BulkMessageFolderAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkMessageFolderAction(self)


class ContactFolderQuery(FolderQuery):
    """A class for querying the contact folders within a given collection."""

    def __getitem__(self, key: str) -> ContactFolder:
        return self._container.get_folder(folder_name=key)

    @property
    def bulk(self) -> BulkContactFolderAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkContactFolderAction(self)
