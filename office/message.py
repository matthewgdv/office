from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

import O365.message as message
import O365.utils.utils as utils

from subtypes import Str, Markup
from pathmagic import Dir, PathLike
from iotools import HtmlGui

from .attribute import Attribute, NonFilterableAttribute, EnumerativeAttribute, BooleanAttribute
from .query import Query, BulkAction, BulkActionContext
from .fluent import FluentMessage

if TYPE_CHECKING:
    from .office import Office


class Message(message.Message):
    """A class representing a Microsoft Outlook message. Provides methods and properties for interacting with it."""

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

    def __repr__(self) -> str:
        return f"{type(self).__name__}(subject={repr(self.subject)}, from={repr(self.sender.address)}, is_read={self.is_read}, importance={repr(self.importance.value)}, attachments={len(self.attachments)}, received={self.received})"

    def __str__(self) -> str:
        return self.text

    def _repr_html_(self) -> str:
        return f"<strong><mark>{self.subject}</mark></strong><br><br>{self.body}"

    @property
    def text(self) -> str:
        """A property controlling access to the string form of the message body, with all html tags and constructs handled and stripped out."""
        return str(Str(Markup(self.body).text).re.sub(r"<!--.*?-->", "").re.sub(r"(?<=\S)(\s)*?\n(\s)*?\n(\s)*?(?=\S)", "\n\n").strip())

    @property
    def markup(self) -> Markup:
        """A property controlling access to the subtypes.Markup object corresponding to this message's html body."""
        return Markup(self.body)

    def reply(self, *args: Any, **kwargs: Any) -> FluentMessage:
        """Create a new FluentMessage serving as a reply to this message."""
        message = super().reply(*args, **kwargs)
        message.office = self.office
        return FluentMessage(message=message)

    def forward(self, *args: Any, **kwargs: Any) -> FluentMessage:
        """Create a new FluentMessage serving as a forward of this message."""
        message = super().forward(*args, **kwargs)
        message.office = self.office
        return FluentMessage(message=message)

    def copy(self, *args: Any, **kwargs: Any) -> FluentMessage:
        """Create a new FluentMessage serving as a copy of this message."""
        message = super().copy(*args, **kwargs)
        message.office = self.office
        return FluentMessage(message=message)

    def render(self) -> None:
        """Render the message body html in a separate window. Will block until the window has been closed by a user."""
        HtmlGui(name=self.subject, text=self.body)

    def save_attachments_to(self, path: PathLike) -> bool:
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

    def execute(self) -> List[Message]:
        """Execute this query and return any messages that match."""
        messages = list(self._container.get_messages(limit=self._limit, query=self._query))
        for message_ in messages:
            message_.office = self._container.office

        return messages
