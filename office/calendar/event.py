from __future__ import annotations

from typing import Any, TYPE_CHECKING

import O365.calendar as calendar

from ..query import Query, BulkAction, BulkActionContext

if TYPE_CHECKING:
    from ..office import Office


class Event(calendar.Event):
    """A class representing a Microsoft Outlook message. Provides methods and properties for interacting with it."""

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __str__(self) -> str:
        return self.text


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
