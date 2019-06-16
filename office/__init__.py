__all__ = ["Office", "MessageFolder", "ContactFolder", "Message", "Contact"]

from .office import Office
from .folder import MessageFolder, ContactFolder
from .message import Message
from .contact import Contact

from pathmagic import File

resourcedir = File(__file__).dir.newdir("resources")
