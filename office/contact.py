from __future__ import annotations

from typing import List, Dict, Any, TYPE_CHECKING

import O365.address_book as address_book
from subtypes import Str
from miscutils import NameSpace

from .attribute import Attribute, NonFilterableAttribute
from .message import Message
from .query import Query, BulkAction, BulkActionContext
from .fluent import FluentMessage

if TYPE_CHECKING:
    from .office import Office


class Contact(address_book.Contact):
    message_constructor = Message

    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.office = office

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={repr(self.full_name)}, email={repr(self.main_email)})"

    @property
    def message(self) -> FluentMessage:
        message = self.new_message()
        message.office = self.office
        return FluentMessage(message=message)

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


class ContactNameSpace(NameSpace):
    def __init__(self, office: Office) -> None:
        self._office = office

        book = self._office.account.address_book()
        book.contact_constructor = Contact

        contacts_by_name: Dict[str, List[Contact]] = {}
        for contact in book.get_contacts():
            contacts_by_name.setdefault(Str(contact.name).case.snake(), []).append(contact)
            contacts_by_name.setdefault(Str(contact.display_name).case.snake(), []).append(contact)

        mappings = {}
        for name, contacts in contacts_by_name.items():
            if len(contacts) == 1 and name and name.lower() != "none" and not hasattr(self, name):
                contacts[0].office = self._office
                mappings[name] = contacts[0]

        super().__init__(mappings)


class ContactQuery(Query):
    @property
    def bulk(self) -> BulkContactAction:
        return BulkContactAction(self)

    def execute(self) -> List[Contact]:
        super().execute()
        result = self._container.get_contacts(limit=self._limit, query=self._query, order_by=self._order)

        for contact in result:
            contact.office = self._container.office

        return result


class BulkContactAction(BulkAction):
    def delete(self) -> BulkActionContext:
        return BulkActionContext(query=self._query, action=Contact.delete)
