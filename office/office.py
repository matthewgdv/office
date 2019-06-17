from __future__ import annotations

from typing import Tuple

import webbrowser
from pathmagic import Dir
from miscutils import Supressor, Secrets

with Supressor():
    import O365 as off

if True:
    from .contact import ContactNameSpace
    from .fluent import FluentMessage
    from .folder import MessageFolders, ContactFolders


class Office:
    scopes = [
        "offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send", "Mail.ReadWrite.Shared", "Mail.Send.Shared",
        "Contacts.ReadWrite", "Contacts.ReadWrite.Shared", "Calendars.ReadWrite", "Calendars.ReadWrite.Shared"
    ]

    def __init__(self, email_address: str = "matt.gdv@optimaconnect.co.uk") -> None:
        from office import localres

        self.address, self.resources = email_address, localres
        self.token, self.credfile = off.FileSystemTokenBackend(token_path=Dir.from_home().path, token_filename="o365_token.txt"), self.resources.newfile("credentials.pkl")
        self._blobs: BlobStorage = None

        if self.credfile:
            self.authenticate()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(account={self.address})"

    @property
    def credentials(self) -> str:
        return Secrets(self.credfile).decrypt()

    @credentials.setter
    def credentials(self, val: Tuple[str, str]) -> None:
        Secrets(self.credfile).encrypt(val)

    @property
    def blobs(self) -> BlobStorage:
        if self._blobs is None:
            self._blobs = BlobStorage(self)

        return self._blobs

    def request_token(self) -> None:
        auth_url = self.account.connection.get_authorization_url(requested_scopes=self.scopes)
        webbrowser.open(auth_url)
        self.account.connection.request_token(input("Please follow the link that will open momentarily and grant permission. Then enter the url of the inbox page you land on.\n\n"))

    def authenticate(self) -> None:
        self.account = off.Account(self.credentials, main_resource=self.address, token_backend=self.token)
        self.outlook, self.people = Outlook(self), People(self)


class Manager:
    def __init__(self, office: Office) -> None:
        self.office = office


class Outlook(Manager):
    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self._folders: MessageFolders = None
        self._signature = self.office.resources.f.signature

    @property
    def folders(self) -> MessageFolders:
        if self._folders is None:
            self._folders = MessageFolders(self.office)
        return self._folders

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
        self._folders: ContactFolders = None
        self.contacts = ContactNameSpace(self.office)

    @property
    def folders(self) -> ContactFolders:
        if self._folders is None:
            self._folders = ContactFolders(self.office)
        return self._folders


class BlobStorage(Manager):
    def __init__(self, office: Office) -> None:
        super().__init__(office=office)
        self.credfile = self.office.resources.newfile("blob_credentials.pkl")

        if self.credfile:
            self.authenticate()

    @property
    def credentials(self) -> Tuple[str, str]:
        return Secrets(self.credfile).decrypt()

    @credentials.setter
    def credentials(self, val: Tuple[str, str]) -> None:
        Secrets(self.credfile).encrypt(val)

    def authenticate(self) -> None:
        import azure.storage.blob as blob
        from .blob import BlobContainerNameSpace

        name, key = self.credentials
        self.blob, self.service = blob, blob.BlockBlobService(account_name=name, account_key=key)
        self.containers = BlobContainerNameSpace(self)
