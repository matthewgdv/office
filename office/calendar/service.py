from __future__ import annotations

from typing import Union, TYPE_CHECKING

from O365 import calendar

from miscutils import lazy_property

from .calendar import Calendar
from .event import Event

if TYPE_CHECKING:
    from ..office import Office


class CalendarService:
    """A class representing Microsoft Calendar. Controls access to calendar-related services."""

    def __init__(self, office: Office) -> None:
        self.office = office
        self.schedule = Schedule(parent=self.office.account)

    def __getitem__(self, key: Union[str, int]) -> Calendar:
        return self.custom(calendar_name=key) if isinstance(key, str) else (self.custom(calendar_id=key) if isinstance(key, int) else None)

    @lazy_property
    def default(self) -> Calendar:
        """A property that returns the default calendar."""
        return self.schedule.get_default_calendar()

    def custom(self, calendar_name: str = None, calendar_id: int = None) -> Calendar:
        """Return the given custom folder by name or id."""
        return self.schedule.get_calendar(calendar_name=calendar_name, calendar_id=calendar_id)


class Schedule(calendar.Schedule):
    calendar_construcor = Calendar
    event_constructor = Event
