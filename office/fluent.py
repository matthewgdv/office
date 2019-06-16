from __future__ import annotations

from typing import Any, Union, TYPE_CHECKING
import os

from maybe import Maybe

if TYPE_CHECKING:
    from .message import Message
    from .folder import Folder
    from .contact import Contact


class FluentMessage:
    def __init__(self, message: Message = None, parent: Union[Folder, Contact] = None) -> None:
        self.message = Maybe(message).else_(Maybe(parent).new_message().else_(None))
        self.office = Maybe(message).office.else_(Maybe(parent).office.else_(None))
        self._signing = False
        self._temp_body: str = None
        self.message.sender.address = self.office.address

    def from_(self, address: str) -> FluentMessage:
        self.message.sender.address = address
        return self

    def to(self, contacts: Any) -> FluentMessage:
        if isinstance(contacts, (tuple, set, list)):
            ret = [contact if not hasattr(contact, "main_email") else contact.main_email for contact in contacts]
        else:
            ret = contacts if not hasattr(contacts, "main_email") else contacts.main_email

        self.message.to.add(ret)
        return self

    def subject(self, subject: str) -> FluentMessage:
        self.message.subject = subject
        return self

    def body(self, body: str) -> FluentMessage:
        self._temp_body = body.replace("\n", "<br>").replace("\t", "&nbsp;"*4)
        return self

    def attach(self, attachments: Any) -> FluentMessage:
        self.message.attachments.add([os.fspath(attachment) for attachment in attachments] if isinstance(attachments, (list, tuple, set)) else os.fspath(attachments))
        return self

    def sign(self, signing: bool = True) -> FluentMessage:
        self._signing = signing
        return self

    def send(self) -> bool:
        if self._temp_body is not None:
            self.message.body = f"{self._temp_body}<br><br>{self.office.outlook.signature}" if self._signing else self._temp_body

        return self.message.send()
