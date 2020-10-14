from __future__ import annotations

from typing import Any, Optional
import os
import threading
import webbrowser

from maybe import Maybe
from miscutils import Supressor
from pathmagic import Dir

with Supressor():
    from O365 import account, FileSystemTokenBackend

if True:
    from .config import OfficeConfig as Config
    from .calendar import CalendarService
    from .outlook import OutlookService
    from .people import PeopleService
    from .token import MemoryTokenBackend, BaseTokenBackend


class Office:
    """The primary class controlling access to the entirety of this library via its attributes named after Office365 services."""

    scopes = [
        "offline_access",
        "User.Read", "User.ReadBasic.All",
        "Mail.ReadWrite", "Mail.ReadWrite.Shared", "Mail.Send", "Mail.Send.Shared",
        "Contacts.ReadWrite", "Contacts.ReadWrite.Shared",
        "Calendars.ReadWrite", "Calendars.ReadWrite.Shared",
        "Files.ReadWrite", "Files.ReadWrite.All",
        "Sites.Read.All", "Sites.ReadWrite.All",
    ]

    outlook: Optional[OutlookService] = None
    people: Optional[PeopleService] = None
    calendar: Optional[CalendarService] = None

    connection: Optional[str] = None

    def __init__(self, client_id: str, client_secret: str, token_backend: BaseTokenBackend, resource: str) -> None:
        self.config, self.token, self.resource, self._auth_state = Config(), token_backend, resource, None
        self.account = Account((client_id, client_secret), main_resource=self.resource, token_backend=self.token, office=self)

        if not self.account.con.token_backend.load_token():
            self.request_token()

        self._establish_services()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(account={self.resource})"

    def request_token(self) -> None:
        """ """
        import flask

        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        auth_url, callback_url = "http://localhost:5000/", "http://localhost:5000/callback/"
        app = flask.Flask("Authentication")

        @app.route('/')
        def auth_step_one():
            url, state = self.account.con.get_authorization_url(requested_scopes=Office.scopes, redirect_uri=callback_url)
            self._auth_state = state
            return flask.redirect(url)

        @app.route('/callback/')
        def auth_step_two_callback():
            self.account.con.request_token(flask.request.url, state=self._auth_state, redirect_uri=callback_url)
            flask.request.environ.get("werkzeug.server.shutdown")()
            return "Successfully authenticated. You may now close the tab."

        threading.Timer(2, lambda: webbrowser.open(auth_url)).start()

        with Supressor():
            app.run()

    def request_token_old(self) -> None:
        """ """
        auth_url, state = self.account.connection.get_authorization_url(requested_scopes=self.scopes)
        webbrowser.open(auth_url)
        self.account.connection.request_token(input("Please follow the link that will open momentarily and grant permission. Then enter the url of the inbox page you land on.\n\n"))

    def _establish_services(self) -> None:
        self.outlook, self.people, self.calendar = OutlookService(office=self), PeopleService(office=self), CalendarService(office=self)

    @classmethod
    def from_token(cls, client_id: str, client_secret: str, token: dict, resource: str = "me") -> Office:
        return cls(client_id=client_id, client_secret=client_secret, token_backend=MemoryTokenBackend(token), resource=resource)

    @classmethod
    def from_connection(cls, connection: str = None, resource: str = None) -> Office:
        config = Config()
        connection = Maybe(connection).else_(config.data.default_connection)
        token_backend = FileSystemTokenBackend(token_path=str(config.folder.new_dir("tokens")), token_filename=f"{connection}.txt")

        settings = config.data.connections[connection]
        resource = Maybe(resource).else_(settings.default_email)
        return cls(client_id=settings.id, client_secret=settings.secret, token_backend=token_backend, resource=resource)


class Account(account.Account):
    def __init__(self, *args: Any, office: Office = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.con.office = office
