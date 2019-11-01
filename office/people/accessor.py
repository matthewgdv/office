from __future__ import annotations

from typing import Any, TYPE_CHECKING

import O365 as off

from miscutils import lazy_property

from .contact import Contact
from .folder import ContactFolder
from .outlook.message import Message

if TYPE_CHECKING:
    from ..office import Office


class PeopleAccessor:
    contact_constructor = Contact
    message_constructor = Message

    def __init__(self, *args: Any, parent: Any = None, office: Office, **kwargs: Any) -> None:
        self.office = office
        super().__init__(*args, parent=self.office.account, **kwargs)
        self.contact = ContactFolderAccessor()


class PeopleAccessor:
    contact_constructor = Contact
    message_constructor = Message

    def __init__(self, *args: Any, parent: Any = None, office: Office, **kwargs: Any) -> None:
        self.office = office
        super().__init__(*args, parent=self.office.account, **kwargs)
        self.contact = ContactFolderAccessor()


class ContactFolderAccessor:
    """A class representing the collection of the default Outlook contact folders."""

    def __init__(self, office: Office) -> None:
        self.office = office
        self._book = office.account.address_book()
        self._book.contact_constructor, self._book.message_constructor = Contact, Message

    @lazy_property
    def main(self) -> ContactFolder:
        """A property that returns the main folder."""
        return ContactFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name='AddressBook', root=True, office=self.office)

    @lazy_property
    def global_(self) -> ContactFolder:
        """A property that returns the global address list."""
        folder = self.office.account.address_book(address_book="gal")
        folder.office = self.office
        folder.contact_constructor = Contact
        return folder
