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
        return str(Str(Markup(self.body).text).re.sub(r"<!--.*?-->", "").re.sub(r"(?<=\S)(\s)*?\n(\s)*?\n(\s)*?(?=\S)", "\n\n").strip())

    @property
    def markup(self) -> Markup:
        return Markup(self.body)

    def reply(self, *args: Any, **kwargs: Any) -> FluentMessage:
        message = super().reply(*args, **kwargs)
        message.office = self.office
        return FluentMessage(message=message)

    def forward(self, *args: Any, **kwargs: Any) -> FluentMessage:
        message = super().forward(*args, **kwargs)
        message.office = self.office
        return FluentMessage(message=message)

    def copy(self, *args: Any, **kwargs: Any) -> FluentMessage:
        message = super().copy(*args, **kwargs)
        message.office = self.office
        return FluentMessage(message=message)

    def fluent(self) -> FluentMessage:
        return FluentMessage(message=self)

    def render(self) -> None:
        HtmlGui(name=self.subject, text=self.body)

    def save_attachments_to(self, path: PathLike) -> bool:
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


class MessageQuery(Query):
    @property
    def bulk(self) -> BulkMessageAction:
        return BulkMessageAction(self)

    def execute(self) -> List[Message]:
        messages = list(self._container.get_messages(limit=self._limit, query=self._query))
        for message_ in messages:
            message_.office = self._container.office

        return messages


class BulkMessageAction(BulkAction):
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
