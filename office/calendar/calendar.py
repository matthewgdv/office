from __future__ import annotations

import O365.calendar as calendar

from .event import Event, EventQuery, FluentEvent


class Calendar(calendar.Calendar):
    """A class representing a Microsoft Outlook calendar. Provides methods and properties for interacting with it."""

    event_constructor = Event

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    @property
    def events(self) -> EventQuery:
        return EventQuery(container=self)

    @property
    def event(self) -> FluentEvent:
        """A property that will create a new fluent event."""
        return self.new_event().fluent

    def new_event(self, subject: str = None) -> Event:
        return super().new_event(subject=subject)
