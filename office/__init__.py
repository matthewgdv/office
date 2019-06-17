__all__ = ["Office", "MessageFolder", "ContactFolder", "Message", "Contact"]

from pathmagic import File

resources = File(__file__).dir.newdir("localres")

if True:
    from .office import Office
    from .folder import MessageFolder, ContactFolder
    from .message import Message
    from .contact import Contact
