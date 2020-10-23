from __future__ import annotations

from typing import Union, List, Collection, TYPE_CHECKING
from collections.abc import Iterable
import os

from O365.utils import ImportanceLevel

from pathmagic import PathLike

if TYPE_CHECKING:
    from .outlook.message import Message
    from .people.contact import Contact
    from .calendar.event import Event


class FluentEntity:
    """A class representing an entity that doesn't yet exist. All public methods allow chaining."""
    entity: Union[Message, Event] = None
    _signing: bool
    _temp_body: str

    def subject(self, subject: str) -> FluentEntity:
        """Set the subject of the message."""
        self.entity.subject = subject
        return self

    def body(self, body: str) -> FluentEntity:
        """Set the body of the message. The body should be an html string, but python newline and tab characters will be automatically converted to their html equivalents."""
        self._temp_body = body.replace("\n", "<br>").replace("\t", "&nbsp;"*4)
        return self

    def attach(self, attachments: Union[PathLike, Collection[PathLike]]) -> FluentEntity:
        """Attach a file or a collection of files to this message."""
        self.entity.attachments.add([os.fspath(attachment) for attachment in attachments] if isinstance(attachments, Iterable) else os.fspath(attachments))
        return self

    def sign(self, signing: bool = True) -> FluentEntity:
        """Set whether the signature will be appended to the message body prior to sending."""
        self._signing = signing
        return self

    def importance(self, importance_level: str = ImportanceLevel.Normal.value) -> FluentEntity:
        self.entity.importance = importance_level
        return self

    def categories(self, categories: list[str]) -> FluentEntity:
        self.entity.categories = categories
        return self

    def _parse_contacts_to_emails(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> list[str]:
        from .people import Contact

        if isinstance(contacts, str):
            contact_list = [contacts]
        elif isinstance(contacts, Contact):
            contact_list = [contacts.main_email]
        elif isinstance(contacts, Iterable):
            contact_list = [contact.main_email if isinstance(contact, Contact) else contact for contact in contacts]
        else:
            raise TypeError(f"Expected a single email address or {Contact.__name__}, or an iterable of the above, not '{type(contacts).__name__}'.")

        return contact_list
