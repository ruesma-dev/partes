# domain/ports/mailbox_client.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from domain.models.email_models import EmailAttachment, EmailMessage


class MailboxClient(ABC):
    @abstractmethod
    def assert_folder_accessible(self, mailbox: str, folder: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def resolve_folder_id(
        self,
        mailbox: str,
        folder: str,
        create_if_missing: bool = False,
    ) -> str:
        """Resuelve ``folder`` (nombre conocido tipo 'inbox', id de carpeta
        o displayName de una carpeta de nivel raiz) a su id real,
        verificando que existe. Si ``create_if_missing`` y la carpeta es
        un displayName que no existe, la crea en la raiz del buzon.
        """
        raise NotImplementedError

    @abstractmethod
    def ensure_folder(
        self,
        mailbox: str,
        display_name: str,
        parent_folder_id: str | None = None,
    ) -> str:
        """Crea (o localiza) una carpeta por ``display_name``. Si se pasa
        ``parent_folder_id``, se crea/busca como SUBcarpeta de esa carpeta;
        en su defecto, en la raiz del buzon.
        """
        raise NotImplementedError

    @abstractmethod
    def list_unread_with_attachments(
        self,
        mailbox: str,
        folder: str,
        top: int,
    ) -> List[EmailMessage]:
        raise NotImplementedError

    @abstractmethod
    def list_attachments(
        self,
        mailbox: str,
        message_id: str,
    ) -> List[EmailAttachment]:
        raise NotImplementedError

    @abstractmethod
    def download_attachment_value(
        self,
        mailbox: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def move_message(
        self,
        mailbox: str,
        message_id: str,
        destination_folder_id: str,
    ) -> None:
        raise NotImplementedError
