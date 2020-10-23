from __future__ import annotations

from typing import List

import O365.address_book as address_book

from ..attribute import Attribute, NonFilterableAttribute
from ..query import Query, BulkAction, BulkActionContext
from ..outlook.message import Message, FluentMessage


class Contact(address_book.Contact):
    """A class representing a Microsoft People Contact. Contains various methods for interacting with them and their details."""

    message_constructor = Message

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={repr(self.full_name)}, email={repr(self.main_email)})"

    def __str__(self) -> str:
        return self.name

    @property
    def message(self) -> FluentMessage:
        """A property that will create a new FluentMessage with the send target set to be this contact."""
        return FluentMessage(parent=self.new_message())

    class Attributes:
        class Name(Attribute):
            name = "given_name"

        class Surname(Attribute):
            name = "surname"

        class DisplayName(Attribute):
            name = "display_name"

        class Company(Attribute):
            name = "company_name"

        class Department(Attribute):
            name = "department"

        class Created(Attribute):
            name = "created_date_time"

        class LastModified(Attribute):
            name = "last_modified_date_time"

        class HomeAddress(Attribute):
            name = "home_address"

        class JobTitle(Attribute):
            name = "job_title"

        class Manager(Attribute):
            name = "manager"

        class MiddleName(Attribute):
            name = "middle_name"

        class Mobile(Attribute):
            name = "mobile_phone1"

        class OfficeLocation(Attribute):
            name = "office_location"

        class Profession(Attribute):
            name = "profession"

        class EmailAddresses(NonFilterableAttribute):
            name = "email_addresses"


class ContactQuery(Query):
    """A class for querying the contacts within a given collection."""

    @property
    def bulk(self) -> BulkContactAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkContactAction(self)

    def execute(self) -> list[Contact]:
        """Execute this query and return any contacts that match."""
        return self._container.get_contacts(limit=self._limit, query=self._query)


class BulkContactAction(BulkAction):
    """A class representing a bulk action performed on the resultset of a contact query."""

    def delete(self) -> BulkActionContext:
        """Delete all contacts that match the query this bulk action was created from."""
        return BulkActionContext(query=self._query, action=Contact.delete)
