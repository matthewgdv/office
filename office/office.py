from __future__ import annotations

import webbrowser

from maybe import Maybe
from miscutils import Supressor, lazy_property

with Supressor():
    import O365 as off

if True:
    from .config import Config
    from .contact import ContactNameSpace
    from .fluent import FluentMessage
    from .folder import MessageFolders, ContactFolders


# TODO: Fix the autocompletion for outlook folders which no longer seems to work properly with the newest version of Jedi


class Office:
    """The primary class controlling access to the entirety of this library via its attributes named after Office365 services."""

    scopes = [
        "offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send", "Mail.ReadWrite.Shared", "Mail.Send.Shared",
        "Contacts.ReadWrite", "Contacts.ReadWrite.Shared", "Calendars.ReadWrite", "Calendars.ReadWrite.Shared",
        "Files.ReadWrite", "Files.ReadWrite.All", "Sites.Read.All", "Sites.ReadWrite.All",
    ]

    def __init__(self, email_address: str = None, connection: str = None) -> None:
        self.config = Config()
        self.connection = Maybe(connection).else_(self.config.data.default_connections.office)
        self.token = off.FileSystemTokenBackend(token_path=str(self.config.appdata), token_filename="o365_token.txt")

        settings = self.config.data.connections.office[self.connection]
        self.address = Maybe(email_address).else_(settings.default_email)
        self.account = off.Account((settings.id, settings.secret), main_resource=self.address, token_backend=self.token)

        try:
            self.outlook, self.people = Outlook(self), People(self)
        except RuntimeError:
            self.request_token()
            self.outlook, self.people = Outlook(self), People(self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(account={self.address})"

    def request_token(self) -> None:
        """ """
        auth_url = self.account.connection.get_authorization_url(requested_scopes=self.scopes)
        webbrowser.open(auth_url)
        self.account.connection.request_token(input("Please follow the link that will open momentarily and grant permission. Then enter the url of the inbox page you land on.\n\n"))


class ServiceHandler:
    """Abstract base class for classes representing Office365 services to inherit from."""

    def __init__(self, office: Office) -> None:
        self.office = office


class Outlook(ServiceHandler):
    """A class representing Microsoft Outlook. Controls access to email-related services."""

    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._signature = self.office.config.appdata.new_file("signature", "html")

    @lazy_property
    def folders(self) -> MessageFolders:
        """A property controlling access to a namespace class representing a collection of default message folders. Custom folders can also be accessed."""
        return MessageFolders(self.office)

    @property
    def signature(self) -> str:
        """A property controlling access to the user's signature. Changes to it will be persisted to the filesystem across sessions."""
        return self._signature.contents

    @signature.setter
    def signature(self, signature: str) -> None:
        self._signature.contents = signature

    @property
    def message(self) -> FluentMessage:
        """A property that will create a new fluent message."""
        return FluentMessage(parent=self.folders.main)


class People(ServiceHandler):
    """A class representing Microsoft People. Controls access to contact-related services."""

    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self.contacts = ContactNameSpace(self.office)

    @lazy_property
    def folders(self) -> ContactFolders:
        """A property controlling access to a namespace class representing a collection of default contact folders. Custom folders can also be accessed."""
        return ContactFolders(self.office)
