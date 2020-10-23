from __future__ import annotations

from typing import Any, List, Union, Collection, TYPE_CHECKING, Optional

import O365.message as message
import O365.utils.utils as utils

from subtypes import Str, Html
from pathmagic import Dir, PathLike, File

from ..attribute import Attribute, NonFilterableAttribute, EnumerativeAttribute, BooleanAttribute
from ..query import Query, BulkAction, BulkActionContext
from ..fluent import FluentEntity

if TYPE_CHECKING:
    from ..people import Contact


class Message(message.Message):
    """A class representing a Microsoft Outlook message. Provides methods and properties for interacting with it."""

    style = {
        "font-size": 11,
        "font-family": "Calibri, sans-serif, serif, &quot;EmojiFont&quot;",
        "margin": 0
    }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(subject={repr(self.subject)}, from={repr(self.sender.address)}, is_read={self.is_read}, importance={repr(self.importance.value)}, attachments={len(self.attachments)}, received={self.received})"

    def __str__(self) -> str:
        return self.text

    def __hash__(self) -> int:
        return id(self)

    def _repr_html_(self) -> str:
        return f"<strong><mark>{self.subject}</mark></strong><br><br>{self.body}"

    @property
    def text(self) -> str:
        """A property controlling access to the string form of the message body, with all html tags and constructs handled and stripped out."""
        return Html(self.body).text.strip()

    @property
    def html(self) -> Html:
        """A property controlling access to the subtypes.Html object corresponding to this message's html body."""
        return Html(self.body)

    @property
    def fluent(self) -> FluentMessage:
        """Convert this Message to an equivalent FluentMessage."""
        return FluentMessage(parent=self)

    def reply(self, *args: Any, **kwargs: Any) -> FluentMessage:
        """Create a new FluentMessage serving as a reply to this message."""
        new: Message = super().reply(*args, **kwargs)
        return new.fluent

    def forward(self) -> FluentMessage:
        """Create a new FluentMessage serving as a forward of this message."""
        new: Message = super().forward()
        return new.fluent

    def copy(self, *args: Any, **kwargs: Any) -> FluentMessage:
        """Create a new FluentMessage serving as a copy of this message."""
        new: Message = super().copy(*args, **kwargs)
        return new.fluent

    def render(self) -> None:
        """Render the message body html in a separate window. Will block until the window has been closed by a user."""
        from iotools import HtmlGui
        HtmlGui(name=self.subject, text=self.body).start()

    def save_attachments_to(self, path: PathLike) -> list[File]:
        """Save all attachments of this message to the given folder path."""
        if not self.has_attachments:
            return []
        else:
            self.attachments.download_attachments()
            for attachment in self.attachments:
                attachment.save(path)

            return [Dir(path).files[attachment.name] for attachment in self.attachments]

    class Attributes:
        class From(Attribute):
            name = "from"

        class Sender(Attribute):
            name = "sender"

        class Subject(Attribute):
            name = "subject"

        class ReceivedOn(Attribute):
            name = "received_date_time"

        class LastModified(Attribute):
            name = "last_modified_date_time"

        class Categories(Attribute):
            name = "categories"

        class IsRead(BooleanAttribute):
            name = "is_read"

        class HasAttachments(BooleanAttribute):
            name = "has_attachments"

        class IsDraft(BooleanAttribute):
            name = "is_draft"

        class HasDeliveryReceipt(BooleanAttribute):
            name = "is_delivery_receipt_requested"

        class HasReadReceipt(BooleanAttribute):
            name = "is_read_receipt_requested"

        class Importance(EnumerativeAttribute):
            name, enumeration = "importance", utils.ImportanceLevel

        class Body(NonFilterableAttribute):
            name = "body"

        class Cc(NonFilterableAttribute):
            name = "cc_recipients"

        class Bcc(NonFilterableAttribute):
            name = "bcc_recipients"

        class To(NonFilterableAttribute):
            name = "to_recipients"


class BulkMessageAction(BulkAction):
    """A class representing a bulk action performed on the resultset of a message query."""

    def copy(self, folder: Any) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=Message.copy, args=(folder,))

    def move(self, folder: Any) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=Message.move, args=(folder,))

    def delete(self) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=Message.delete)

    def mark_as_read(self) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=Message.mark_as_read)

    def save_draft(self) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=Message.save_draft)


class MessageQuery(Query):
    """A class for querying the messages within a given collection."""

    @property
    def bulk(self) -> BulkMessageAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkMessageAction(self)

    def execute(self) -> list[Message]:
        """Execute this query and return any messages that match."""
        return list(self._container.get_messages(limit=self._limit, query=self._query))


class FluentMessage(FluentEntity):
    """A class representing a message that doesn't yet exist. All public methods allow chaining. At the end of the method chain call FluentMessage.send() to send the message."""

    def __init__(self, parent: Message = None) -> None:
        self.entity, self.office, self._signing = parent, parent.con.office, False
        self.entity.sender.address = self.office.resource
        self._temp_body: Optional[str] = None

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
            start, end = f"""<p style="font-size: {self.entity.style["font-size"]}pt; font-family: {self.entity.style["font-family"]}; margin: {self.entity.style["margin"]}px;">""", "</p>"
            body = f"{start}{self._temp_body}{end}"
            self.entity.body = f"{body}<br>{self.office.outlook.signature}" if self._signing else body

        return self.entity.send()
