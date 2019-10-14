from __future__ import annotations

import webbrowser

from maybe import Maybe
from pathmagic import Dir, File
from miscutils import Supressor, LazyProperty

with Supressor():
    import O365 as off

if True:
    from .config import Config
    from .contact import ContactNameSpace
    from .fluent import FluentMessage
    from .folder import MessageFolders, ContactFolders
    from office import resources


class Office:
    scopes = [
        "offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send", "Mail.ReadWrite.Shared", "Mail.Send.Shared",
        "Contacts.ReadWrite", "Contacts.ReadWrite.Shared", "Calendars.ReadWrite", "Calendars.ReadWrite.Shared",
        "Files.ReadWrite", "Files.ReadWrite.All", "Sites.Read.All", "Sites.ReadWrite.All",
    ]

    def __init__(self, email_address: str = None, connection: str = None) -> None:
        self.token = off.FileSystemTokenBackend(token_path=str(Dir.from_home()), token_filename="o365_token.txt")

        self.config = Config()
        self.connection = Maybe(connection).else_(self.config.data.default_connections.office)

        settings = self.config.data.connections.office[self.connection]

        self.address = Maybe(email_address).else_(settings.default_email)
        self.account = off.Account((settings.id, settings.secret), main_resource=self.address, token_backend=self.token)

        self.outlook, self.people = Outlook(self), People(self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(account={self.address})"

    def request_token(self) -> None:
        auth_url = self.account.connection.get_authorization_url(requested_scopes=self.scopes)
        webbrowser.open(auth_url)
        self.account.connection.request_token(input("Please follow the link that will open momentarily and grant permission. Then enter the url of the inbox page you land on.\n\n"))


class Manager:
    def __init__(self, office: Office) -> None:
        self.office = office


class Outlook(Manager):
    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._signature = self.office.config.appdata.new_file("signature", "html")

    @LazyProperty
    def folders(self) -> MessageFolders:
        return MessageFolders(self.office)

    @property
    def signature(self) -> str:
        return self._signature.contents

    @signature.setter
    def signature(self, signature: str) -> None:
        self._signature.contents = signature

    @property
    def message(self) -> FluentMessage:
        return FluentMessage(parent=self.folders.main)


class People(Manager):
    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self.contacts = ContactNameSpace(self.office)

    @LazyProperty
    def folders(self) -> ContactFolders:
        return ContactFolders(self.office)


class BlobStorage:
    def __init__(self, connection: str = None) -> None:
        self.blob_type_mappings = File.from_resource(package=resources, name="blob_content_types", extension="json").contents

        self.config = Config()
        self.connection = Maybe(connection).else_(self.config.data.default_connection)

        self.authenticate()

    def authenticate(self) -> None:
        import azure.storage.blob as blob
        from .blob import BlobContainerNameSpace

        settings = self.config.data.connections.blob[self.connection]
        self.blob, self.service = blob, blob.BlockBlobService(account_name=settings.account, account_key=settings.key)
        self.containers = BlobContainerNameSpace(self)
