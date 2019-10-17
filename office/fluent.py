from __future__ import annotations

from typing import Union, Collection, TYPE_CHECKING
from collections.abc import Iterable
import os

from maybe import Maybe
from pathmagic import PathLike

if TYPE_CHECKING:
    from .message import Message
    from .folder import Folder
    from .contact import Contact


class FluentMessage:
    """A class representing a message that doesn't yet exist. All public methods allow chaining. At the end of the method chain call FluentMessage.send() to send the message."""

    def __init__(self, message: Message = None, parent: Union[Folder, Contact] = None) -> None:
        self.message = Maybe(message).else_(Maybe(parent).new_message().else_(None))
        self.office = Maybe(message).office.else_(Maybe(parent).office.else_(None))
        self._signing = False
        self._temp_body: str = None
        self.message.sender.address = self.office.address

    def from_(self, address: str) -> FluentMessage:
        """Set the email address this message will appear to originate from."""
        self.message.sender.address = address
        return self

    def to(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> FluentMessage:
        """Set the email address(es) (a single one or a collection of them) this message will be sent to. Email addresses can be provided either as strings or as contact objects."""
        from .contact import Contact

        if isinstance(contacts, str):
            ret = contacts.main_email if isinstance(contacts, Contact) else contacts
        elif isinstance(contacts, Iterable):
            ret = [contact.main_email if isinstance(contact, Contact) else contact for contact in contacts]
        else:
            raise TypeError(f"Expected a single email address or {Contact.__name__}, or an iterable of the above, not '{type(contacts).__name__}'.")

        self.message.to.add(ret)
        return self

    def subject(self, subject: str) -> FluentMessage:
        """Set the subject of the message."""
        self.message.subject = subject
        return self

    def body(self, body: str) -> FluentMessage:
        """Set the body of the message. The body should be an html string, but python newline and tab characters will be automatically converted to their html equivalents."""
        self._temp_body = body.replace("\n", "<br>").replace("\t", "&nbsp;"*4)
        return self

    def attach(self, attachments: Union[PathLike, Collection[PathLike]]) -> FluentMessage:
        """Attach a file or a collection of files to this message."""
        self.message.attachments.add([os.fspath(attachment) for attachment in attachments] if isinstance(attachments, Iterable) else os.fspath(attachments))
        return self

    def sign(self, signing: bool = True) -> FluentMessage:
        """Set whether the signature will be appended to the message body prior to sending."""
        self._signing = signing
        return self

    def send(self) -> bool:
        """Send this message as it currently is."""
        if self._temp_body is not None:
            self.message.body = f"{self._temp_body}<br><br>{self.office.outlook.signature}" if self._signing else self._temp_body

        return self.message.send()
