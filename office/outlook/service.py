from __future__ import annotations

from typing import TYPE_CHECKING

from O365.mailbox import MailBox

from miscutils import cached_property

from .folder import MessageFolder
from .message import FluentMessage

if TYPE_CHECKING:
    from ..office import Office


class OutlookService:
    """A class representing Microsoft Outlook. Controls access to email-related services."""

    def __init__(self, office: Office) -> None:
        self.office = office
        self.mailbox = Mailbox(parent=self.office.account, main_resource=self.office.account.main_resource, name='MailBox')
        self._signature = self.office.config.folder.new_file("signature", "html")

    def __getitem__(self, key: str) -> MessageFolder:
        return self.custom(folder_name=key)

    @property
    def message(self) -> FluentMessage:
        """A property that will create a new fluent message."""
        return FluentMessage(parent=self.main.new_message())

    @property
    def signature(self) -> str:
        """A property controlling access to the user's signature. Changes to it will be persisted to the filesystem across sessions."""
        return self._signature.content

    @signature.setter
    def signature(self, signature: str) -> None:
        self._signature.content = signature

    @cached_property
    def main(self) -> MessageFolder:
        """A property that returns the main folder."""
        return MessageFolder(parent=self.office.account, main_resource=self.office.account.main_resource, root=True, name='Main')

    @cached_property
    def inbox(self) -> MessageFolder:
        """A property that returns the inbox folder."""
        return self.mailbox.inbox_folder()

    @cached_property
    def outbox(self) -> MessageFolder:
        """A property that returns the outbox folder."""
        return self.mailbox.outbox_folder()

    @cached_property
    def sent(self) -> MessageFolder:
        """A property that returns the sent folder."""
        return self.mailbox.sent_folder()

    @cached_property
    def drafts(self) -> MessageFolder:
        """A property that returns the drafts folder."""
        return self.mailbox.drafts_folder()

    @cached_property
    def junk(self) -> MessageFolder:
        """A property that returns the junk folder."""
        return self.mailbox.junk_folder()

    @cached_property
    def deleted(self) -> MessageFolder:
        """A property that returns the deleted folder."""
        return self.mailbox.deleted_folder()

    def custom(self, folder_name: str = None, folder_id: str = None) -> MessageFolder:
        """Return the given custom folder by name or id."""
        return self.mailbox.get_folder(folder_name=folder_name, folder_id=folder_id)


class Mailbox(MailBox):
    folder_constructor = MessageFolder
