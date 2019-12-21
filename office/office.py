from __future__ import annotations

from typing import Any, Optional
import webbrowser

from maybe import Maybe
from miscutils import Supressor

with Supressor():
    from O365 import Account as SuperAccount, FileSystemTokenBackend

if True:
    from .config import Config
    from .calendar import CalendarService
    from .outlook import OutlookService
    from .people import PeopleService


class Office:
    """The primary class controlling access to the entirety of this library via its attributes named after Office365 services."""

    scopes = [
        "offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send", "Mail.ReadWrite.Shared", "Mail.Send.Shared",
        "Contacts.ReadWrite", "Contacts.ReadWrite.Shared", "Calendars.ReadWrite", "Calendars.ReadWrite.Shared",
        "Files.ReadWrite", "Files.ReadWrite.All", "Sites.Read.All", "Sites.ReadWrite.All",
    ]

    def __init__(self, email_address: str = None, connection: str = None) -> None:
        self.outlook: Optional[OutlookService] = None
        self.people: Optional[PeopleService] = None
        self.calendar: Optional[CalendarService] = None

        self.config = Config()
        self.connection = Maybe(connection).else_(self.config.data.default_connections.office)
        self.token = FileSystemTokenBackend(token_path=str(self.config.folder.new_dir("tokens")), token_filename=f"{self.connection}.txt")

        settings = self.config.data.connections.office[self.connection]
        self.address = Maybe(email_address).else_(settings.default_email)
        self.account = Account((settings.id, settings.secret), main_resource=self.address, token_backend=self.token, office=self)

        try:
            self._establish_services()
        except Exception:
            self.request_token()
            self._establish_services()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(account={self.address})"

    def request_token(self) -> None:
        """ """
        auth_url, state = self.account.connection.get_authorization_url(requested_scopes=self.scopes)
        webbrowser.open(auth_url)
        self.account.connection.request_token(input("Please follow the link that will open momentarily and grant permission. Then enter the url of the inbox page you land on.\n\n"))

    def _establish_services(self) -> None:
        self.outlook, self.people, self.calendar = OutlookService(office=self), PeopleService(office=self), CalendarService(office=self)


class Account(SuperAccount):
    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.con.office = office
