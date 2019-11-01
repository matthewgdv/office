from __future__ import annotations

from typing import Any, Union, TYPE_CHECKING

import O365.calendar as calendar

from miscutils import lazy_property

from ..event import Event, EventQuery
from ..fluent import FluentEvent

if TYPE_CHECKING:
    from ..office import Office


class Calendar(calendar.Calendar):
    """A class representing a Microsoft Outlook calendar. Provides methods and properties for interacting with it."""

    event_constructor = Event

    def __init__(self, *args: Any, parent: Any = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = parent.office

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    @property
    def events(self) -> EventQuery:
        return EventQuery(container=self)

    @property
    def event(self) -> FluentEvent:
        """A property that will create a new fluent event."""
        return FluentEvent(parent=self)


class CalendarAccessor:
    """A class representing the collection of the default Outlook message folders. Custom folders can be accessed via the the MessageFolders.custom() method."""

    def __init__(self, office: Office, schedule: office.Schedule) -> None:
        self.office, self.schedule = office, schedule

    def __getitem__(self, key: Union[str, int]) -> Calendar:
        return self.custom(calendar_name=key) if isinstance(key, str) else (self.custom(calendar_id=key) if isinstance(key, int) else None)

    @lazy_property
    def default(self) -> Calendar:
        """A property that returns the default calendar."""
        return self.schedule.get_default_calendar()

    def custom(self, calendar_name: str = None, calendar_id: int = None) -> Calendar:
        """Return the given custom folder by name or id."""
        folder = self.schedule.get_calendar(calendar_name=calendar_name, calendar_id=calendar_id)
        folder.office = self.office
        return folder
