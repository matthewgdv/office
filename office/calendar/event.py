from __future__ import annotations

import datetime as dt
from typing import Union, Collection, TYPE_CHECKING, Optional

import O365.calendar as calendar

from ..query import Query, BulkAction, BulkActionContext
from ..fluent import FluentEntity

if TYPE_CHECKING:
    from ..people import Contact


class Event(calendar.Event):
    """A class representing a Microsoft Outlook message. Provides methods and properties for interacting with it."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __str__(self) -> str:
        return self.body

    @property
    def fluent(self) -> FluentEvent:
        return FluentEvent(parent=self)


class BulkEventAction(BulkAction):
    """A class representing a bulk action performed on the resultset of a folder query."""

    def delete(self) -> BulkActionContext:
        """Delete all events that match the query this bulk action was created from."""
        return BulkActionContext(query=self._query, action=Event.delete)


class EventQuery(Query):
    """A class for querying the message folders within a given collection."""

    @property
    def bulk(self) -> BulkEventAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkEventAction(self)


class FluentEvent(FluentEntity):
    """A class representing an event that doesn't yet exist. All public methods allow chaining. At the end of the method chain call FluentEvent.create() to create the event."""

    def __init__(self, parent: Event = None) -> None:
        self.entity, self.office = parent, parent.con.office
        self._temp_body: Optional[str] = None
        self._start: Optional[dt.datetime] = None
        self._end: Optional[dt.datetime] = None

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
