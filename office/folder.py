from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

import O365.mailbox as mailbox
import O365.address_book as address_book

from .attribute import Attribute, NonFilterableAttribute
from .message import Message, MessageQuery
from .contact import Contact, ContactQuery
from .query import Query, BulkAction, BulkActionContext
from .fluent import FluentMessage

if TYPE_CHECKING:
    from .office import Office


class Folder:
    @property
    def message(self) -> FluentMessage:
        return FluentMessage(parent=self)


class MessageFolder(mailbox.Folder, Folder):
    message_constructor = Message

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

    @property
    def folders(self) -> MessageFolderQuery:
        return MessageFolderQuery(container=self)

    @property
    def messages(self) -> MessageQuery:
        return MessageQuery(container=self)

    @staticmethod
    def order_messages_by_date(messages: list, desc: bool = True) -> list:
        return sorted(messages, reverse=desc, key=lambda val: val.received)

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


class ContactFolder(address_book.ContactFolder, Folder):
    message_constructor = Message
    contact_constructor = Contact

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

    @property
    def folders(self) -> ContactFolderQuery:
        return ContactFolderQuery(container=self)

    @property
    def contacts(self) -> ContactQuery:
        return ContactQuery(container=self)

    class Attributes:
        class Name(Attribute):
            name = "display_name"

        class Contacts(NonFilterableAttribute):
            name = "contacts"

        class ChildFolders(NonFilterableAttribute):
            name = "child_folders"


class Folders:
    def __init__(self, office: Office) -> None:
        self.office = office


class MessageFolders(Folders):
    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._mailbox = office.account.mailbox()
        self._mailbox.folder_constructor = MessageFolder
        self._main = self._inbox = self._outbox = self._sent = self._drafts = self._junk = self._deleted = None  # type: MessageFolder

    @property
    def main(self) -> MessageFolder:
        if self._main is None:
            self._main = MessageFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name='MailBox', root=True, office=self.office)
        return self._main

    @property
    def inbox(self) -> MessageFolder:
        if self._inbox is None:
            self._inbox = self._mailbox.inbox_folder()
            self._inbox.office = self.office
        return self._inbox

    @property
    def outbox(self) -> MessageFolder:
        if self._outbox is None:
            self._outbox = self._mailbox.outbox_folder()
            self._outbox.office = self.office
        return self._outbox

    @property
    def sent(self) -> MessageFolder:
        if self._sent is None:
            self._sent = self._mailbox.sent_folder()
            self._sent.office = self.office
        return self._sent

    @property
    def drafts(self) -> MessageFolder:
        if self._drafts is None:
            self._drafts = self._mailbox.drafts_folder()
            self._drafts.office = self.office
        return self._drafts

    @property
    def junk(self) -> MessageFolder:
        if self._junk is None:
            self._junk = self._mailbox.junk_folder()
            self._junk.office = self.office
        return self._junk

    @property
    def deleted(self) -> MessageFolder:
        if self._deleted is None:
            self._deleted = self._mailbox.deleted_folder()
            self._deleted.office = self.office
        return self._deleted

    def custom(self, folder_name: str = None, folder_id: int = None) -> MessageFolder:
        folder = self._mailbox.get_folder(folder_name=folder_name, folder_id=folder_id)
        folder.office = self.office
        return folder


class ContactFolders(Folders):
    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._book = office.account.address_book()
        self._book.contact_constructor, self._book.message_constructor = Contact, Message
        self._main = self._global = None  # type: ContactFolder

    @property
    def main(self) -> ContactFolder:
        if self._main is None:
            self._main = ContactFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name='AddressBook', root=True, office=self.office)
        return self._main

    @property
    def global_(self) -> ContactFolder:
        if self._global is None:
            self._global = self.office.account.address_book(address_book="gal")
            self._global.office = self.office
        return self._global


class BulkFolderAction(BulkAction):
    def move(self, folder: Folder) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=MessageFolder.move_folder, args=(folder,))

    def delete(self) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=MessageFolder.delete)


class BulkMessageFolderAction(BulkFolderAction):
    def copy(self, folder: Folder) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=MessageFolder.copy_folder, args=(folder,))


class BulkContactFolderAction(BulkFolderAction):
    pass


class FolderQuery(Query):
    def __getitem__(self, key: str) -> Folder:
        raise NotImplementedError()

    def execute(self) -> List[Message]:
        super().execute()
        folders = list(self._container.get_folders(limit=self._limit, query=self._query, order_by=self._order))
        for folder in folders:
            folder.office = self._container.Office

        return folders


class MessageFolderQuery(FolderQuery):
    def __getitem__(self, key: str) -> MessageFolder:
        folder = self._container.get_folder(folder_name=key)
        folder.office = self._container.office
        return folder

    @property
    def bulk(self) -> BulkMessageFolderAction:
        return BulkMessageFolderAction(self)


class ContactFolderQuery(FolderQuery):
    def __getitem__(self, key: str) -> ContactFolder:
        return self._container.get_folder(folder_name=key)

    @property
    def bulk(self) -> BulkContactFolderAction:
        return BulkContactFolderAction(self)
