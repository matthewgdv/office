from __future__ import annotations

from typing import Any, List, Dict, TYPE_CHECKING

from O365.directory import Directory, User

from subtypes import Str, NameSpace
from miscutils import cached_property, is_running_in_ipython

from .contact import Contact
from .folder import ContactFolder

if TYPE_CHECKING:
    from ..office import Office


class PeopleService:
    """A class representing Microsoft People. Controls access to contact-related services."""

    def __init__(self, *args: Any, office: Office, **kwargs: Any) -> None:
        self.office = office

        if is_running_in_ipython():
            assert self.contacts

    @cached_property
    def contacts(self) -> ContactNameSpace:
        return ContactNameSpace(service=self)

    @cached_property
    def personal(self) -> ContactFolder:
        return ContactFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name="Personal Address Book", root=True)

    @cached_property
    def active_directory(self) -> Directory:
        """A property that returns the Azure Active Directory."""
        return Directory(parent=self.office.account, main_resource="users")

    @cached_property
    def me(self) -> User:
        """A property that returns the Azure Active Directory."""
        return Directory(parent=self.office.account, main_resource="me").get_current_user()


class ContactNameSpace(NameSpace):
    """A namespace class containing a collection of the contacts within the global address book of the email address used to instanciate the Office object."""

    def __init__(self, service: PeopleService) -> None:
        contacts_by_name: dict[str, list[Contact]] = {}
        for contact in service.personal.get_contacts():
            contacts_by_name.setdefault(Str(contact.name).case.snake(), []).append(contact)
            contacts_by_name.setdefault(Str(contact.display_name).case.snake(), []).append(contact)

        mappings = {}
        for name, contacts in contacts_by_name.items():
            if len(contacts) == 1 and name and name.lower() != "none" and not hasattr(self, name):
                mappings[name] = contacts[0]

        super().__init__(mappings)
