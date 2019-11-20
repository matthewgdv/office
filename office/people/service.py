from __future__ import annotations

from typing import Any, List, Dict, TYPE_CHECKING

from O365 import directory

from subtypes import Str, NameSpace
from miscutils import lazy_property, is_running_in_ipython

from .contact import Contact
from .folder import ContactFolder

if TYPE_CHECKING:
    from ..office import Office


class PeopleService:
    """A class representing Microsoft People. Controls access to contact-related services."""

    def __init__(self, *args: Any, office: Office, **kwargs: Any) -> None:
        self.office = office

        if is_running_in_ipython():
            self.contacts

    @lazy_property
    def contacts(self) -> ContactNameSpace:
        return ContactNameSpace(service=self)

    @lazy_property
    def personal(self) -> ContactFolder:
        return ContactFolder(parent=self.office.account, main_resource=self.office.account.main_resource, name="Personal Address Book", root=True)

    @lazy_property
    def active_directory(self) -> ContactFolder:
        """A property that returns the global address list."""
        return directory.Directory(parent=self.office.account)


class ContactNameSpace(NameSpace):
    """A namespace class containing a collection of the contacts within the global address book of the email address used to instanciate the Office object."""

    def __init__(self, service: PeopleService) -> None:
        contacts_by_name: Dict[str, List[Contact]] = {}
        for contact in service.personal.get_contacts():
            contacts_by_name.setdefault(Str(contact.name).case.snake(), []).append(contact)
            contacts_by_name.setdefault(Str(contact.display_name).case.snake(), []).append(contact)

        mappings = {}
        for name, contacts in contacts_by_name.items():
            if len(contacts) == 1 and name and name.lower() != "none" and not hasattr(self, name):
                mappings[name] = contacts[0]

        super().__init__(mappings)