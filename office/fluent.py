from __future__ import annotations

import datetime as dt
from typing import Union, List, Collection, TYPE_CHECKING
from collections.abc import Iterable
import os

from O365.utils import ImportanceLevel

from pathmagic import PathLike

if TYPE_CHECKING:
    from .outlook.message import Message
    from .outlook.folder import Folder
    from .people.contact import Contact
    from .calendar.calendar import Calendar
    from .calendar.event import Event


class FluentEntity:
    """A class representing an entity that doesn't yet exist. All public methods allow chaining."""
    entity: Union[Message, Event] = None

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

    def importance(self, importance_level: str = ImportanceLevel.Normal.value) -> FluentEvent:
        self.entity.importance = importance_level
        return self

    def categories(self, categories: List[str]) -> FluentEvent:
        self.entity.categories = categories
        return self

    def _parse_contacts_to_emails(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> List[str]:
        from .contact import Contact

        if isinstance(contacts, str):
            contact_list = [contacts]
        elif isinstance(contacts, Contact):
            contact_list = [contacts.main_email]
        elif isinstance(contacts, Iterable):
            contact_list = [contact.main_email if isinstance(contact, Contact) else contact for contact in contacts]
        else:
            raise TypeError(f"Expected a single email address or {Contact.__name__}, or an iterable of the above, not '{type(contacts).__name__}'.")

        return contact_list


class FluentMessage(FluentEntity):
    """A class representing a message that doesn't yet exist. All public methods allow chaining. At the end of the method chain call FluentMessage.send() to send the message."""

    def __init__(self, parent: Union[Folder, Contact, Message] = None) -> None:
        self.entity, self.office, self._signing = parent if isinstance(parent, Message) else parent.new_message(), parent.office, False
        self.entity.sender.address = self.office.address
        self._temp_body: str = None

    def from_(self, address: str) -> FluentMessage:
        """Set the email address this message will appear to originate from."""
        self.entity.sender.address = address
        return self

    def to(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> FluentMessage:
        """Set the email address(es) (a single one or a collection of them) this message will be sent to. Email addresses can be provided either as strings or as contact objects."""
        self.entity.to.add(self._parse_contacts_to_emails(contacts=contacts))
        return self

    def cc(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> FluentMessage:
        """Set the email address(es) (a single one or a collection of them) this message will be sent to. Email addresses can be provided either as strings or as contact objects."""
        self.entity.cc.add(self._parse_contacts_to_emails(contacts=contacts))
        return self

    def bcc(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> FluentMessage:
        """Set the email address(es) (a single one or a collection of them) this message will be sent to. Email addresses can be provided either as strings or as contact objects."""
        self.entity.bcc.add(self._parse_contacts_to_emails(contacts=contacts))
        return self

    def request_read_receipt(self, request_read_receipt: bool) -> FluentMessage:
        """Set the email address(es) (a single one or a collection of them) this message will be sent to. Email addresses can be provided either as strings or as contact objects."""
        self.entity.is_read_receipt_requested = request_read_receipt
        return self

    def request_delivery_receipt(self, request_delivery_receipt: bool) -> FluentMessage:
        """Set the email address(es) (a single one or a collection of them) this message will be sent to. Email addresses can be provided either as strings or as contact objects."""
        self.entity.is_delivery_receipt_requested = request_delivery_receipt
        return self

    def send(self) -> bool:
        """Send this message as it currently is."""
        if self._temp_body is not None:
            self.entity.body = f"{self._temp_body}<br><br>{self.office.outlook.signature}" if self._signing else self._temp_body

        return self.entity.send()


class FluentEvent(FluentEntity):
    """A class representing an event that doesn't yet exist. All public methods allow chaining. At the end of the method chain call FluentEvent.create() to create the event."""

    def __init__(self, parent: Union[Calendar, Event] = None) -> None:
        self.entity, self.office = parent if isinstance(parent, Event) else parent.new_event(), parent.office
        self._temp_body: str = None

    def from_(self, address: str) -> FluentEvent:
        """Set the email address this event will appear to originate from."""
        self.entity.organizer = address
        return self

    def to(self, contacts: Union[Union[str, Contact], Collection[Union[str, Contact]]]) -> FluentEvent:
        """Set the email address(es) (a single one or a collection of them) this event will be sent to. Email addresses can be provided either as strings or as contact objects."""
        self.entity.attendees.add(self._parse_contacts_to_emails(contacts=contacts))
        return self

    def start(self, start_time: dt.datetime = None) -> FluentEvent:
        """Set the time at which the event will start."""
        self._start = start_time
        return self

    def end(self, end_time: dt.datetime = None) -> FluentEvent:
        """Set the time at which the event will end."""
        self._end = end_time
        return self

    def all_day(self, is_all_day: bool = True) -> FluentEvent:
        self.entity.is_all_day = is_all_day
        return self

    def location(self, location: str) -> FluentEvent:
        self.entity.location = location
        return self

    def remind_before_minutes(self, remind_before_minutes: int) -> FluentEvent:
        self.entity.remind_before_minutes = remind_before_minutes
        return self

    def response_requested(self, response_requested: bool) -> FluentEvent:
        self.entity.response_requested = response_requested
        return self

    def show_as(self, show_as: str) -> FluentEvent:
        self.entity.show_as = show_as
        return self

    def sensitivity(self, sensitivity: str) -> FluentEvent:
        self.entity.sensitivity = sensitivity
        return self

    def create(self) -> bool:
        """Create this event as it currently is."""
        if self._temp_body is not None:
            self.entity.body = f"{self._temp_body}<br><br>{self.office.outlook.signature}" if self._signing else self._temp_body

        return self.entity.save()
