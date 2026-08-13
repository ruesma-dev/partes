# infrastructure/graph/mail_client.py
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from domain.models.email_models import EmailAttachment, EmailMessage
from domain.ports.mailbox_client import MailboxClient
from infrastructure.graph.token_provider import GraphTokenProvider

logger = logging.getLogger(__name__)


class GraphMailClient(MailboxClient):
    def __init__(self, token_provider: GraphTokenProvider, timeout_s: int) -> None:
        self._token_provider = token_provider
        self._client = httpx.Client(timeout=timeout_s)
        self._base = "https://graph.microsoft.com/v1.0"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token_provider.get_token()}"}

    @staticmethod
    def _escape_odata(value: str) -> str:
        return value.replace("'", "''")

    def assert_folder_accessible(self, mailbox: str, folder: str) -> None:
        url = f"{self._base}/users/{mailbox}/mailFolders/{folder}"
        response = self._client.get(
            url,
            headers=self._headers(),
            params={"$select": "id,displayName"},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                "Graph folder not accessible "
                f"({folder}) {response.status_code}: {response.text[:400]}"
            )
        data = response.json() or {}
        logger.info(
            "SOURCE_FOLDER accesible: %s (%s)",
            data.get("displayName"),
            data.get("id"),
        )

    def resolve_folder_id(
        self,
        mailbox: str,
        folder: str,
        create_if_missing: bool = False,
    ) -> str:
        """Resuelve ``folder`` a su id real.

        Orden de resolucion:
          1. GET directo ``/mailFolders/{folder}`` -> sirve para nombres
             conocidos ('inbox', 'sentitems', ...) e ids de carpeta.
          2. Si no resuelve, busca en la raiz por ``displayName``.
          3. Si sigue sin existir y ``create_if_missing``, la crea en la
             raiz del buzon.

        Verifica siempre la existencia (o la crea); nunca devuelve un id
        inventado.
        """
        # 1) Nombre conocido o id directo.
        url = f"{self._base}/users/{mailbox}/mailFolders/{folder}"
        response = self._client.get(
            url,
            headers=self._headers(),
            params={"$select": "id,displayName"},
        )
        if response.status_code < 300:
            data = response.json() or {}
            folder_id = data["id"]
            logger.info(
                "Carpeta origen resuelta: %s (%s)",
                data.get("displayName"),
                folder_id,
            )
            return folder_id

        # 2) Busqueda por displayName en la raiz.
        list_url = f"{self._base}/users/{mailbox}/mailFolders"
        params = {
            "$filter": f"displayName eq '{self._escape_odata(folder)}'",
            "$select": "id,displayName",
        }
        list_resp = self._client.get(
            list_url,
            headers=self._headers(),
            params=params,
        )
        if list_resp.status_code < 300:
            items = (list_resp.json() or {}).get("value") or []
            if items:
                folder_id = items[0]["id"]
                logger.info(
                    "Carpeta origen encontrada por nombre: %s id=%s",
                    folder,
                    folder_id,
                )
                return folder_id

        # 3) No existe: crear o fallar.
        if not create_if_missing:
            raise RuntimeError(
                f"Carpeta origen '{folder}' no accesible "
                f"({response.status_code}: {response.text[:300]}). "
                "Define un nombre conocido (p.ej. 'inbox'), un id valido, "
                "o activa CREATE_SOURCE_IF_MISSING para crearla."
            )
        logger.info("Carpeta origen no existe, creando: %s", folder)
        create_resp = self._client.post(
            list_url,
            headers=self._headers(),
            json={"displayName": folder},
        )
        if create_resp.status_code >= 300:
            raise RuntimeError(
                f"Graph create source folder {create_resp.status_code}: "
                f"{create_resp.text[:400]}"
            )
        folder_id = create_resp.json()["id"]
        logger.info("Carpeta origen creada: %s id=%s", folder, folder_id)
        return folder_id

    def ensure_folder(
        self,
        mailbox: str,
        display_name: str,
        parent_folder_id: str | None = None,
    ) -> str:
        # Si hay padre, operamos sobre sus childFolders; si no, sobre la
        # raiz del buzon. El $filter por displayName y el POST de creacion
        # usan la MISMA base, asi la carpeta se busca y se crea en el mismo
        # nivel (raiz o subcarpeta).
        if parent_folder_id:
            base = (
                f"{self._base}/users/{mailbox}/mailFolders/"
                f"{parent_folder_id}/childFolders"
            )
            scope = f"subcarpeta de {parent_folder_id}"
        else:
            base = f"{self._base}/users/{mailbox}/mailFolders"
            scope = "raiz"

        params = {
            "$filter": f"displayName eq '{self._escape_odata(display_name)}'",
            "$select": "id,displayName",
        }
        response = self._client.get(
            base,
            headers=self._headers(),
            params=params,
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph list folders {response.status_code}: "
                f"{response.text[:400]}"
            )

        items = (response.json() or {}).get("value") or []
        if items:
            folder_id = items[0]["id"]
            logger.info(
                "Carpeta existe (%s): %s id=%s", scope, display_name, folder_id
            )
            return folder_id

        logger.info("Carpeta no existe (%s), creando: %s", scope, display_name)
        response = self._client.post(
            base,
            headers=self._headers(),
            json={"displayName": display_name},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph create folder {response.status_code}: "
                f"{response.text[:400]}"
            )

        folder_id = response.json()["id"]
        logger.info(
            "Carpeta creada (%s): %s id=%s", scope, display_name, folder_id
        )
        return folder_id

    def list_unread_with_attachments(
        self,
        mailbox: str,
        folder: str,
        top: int,
    ) -> List[EmailMessage]:
        url = f"{self._base}/users/{mailbox}/mailFolders/{folder}/messages"
        params = {
            "$top": str(top),
            "$select": (
                "id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview"
            ),
            "$orderby": "receivedDateTime desc",
            "$filter": (
                "receivedDateTime ge 1900-01-01T00:00:00Z "
                "and isRead eq false and hasAttachments eq true"
            ),
        }
        response = self._client.get(
            url,
            headers=self._headers(),
            params=params,
        )
        if response.status_code >= 300:
            logger.warning(
                "Graph list messages falló (%s). Reintento sin filter. %s",
                response.status_code,
                response.text[:300],
            )
            params.pop("$filter", None)
            response = self._client.get(
                url,
                headers=self._headers(),
                params=params,
            )
            if response.status_code >= 300:
                raise RuntimeError(
                    f"Graph list messages {response.status_code}: "
                    f"{response.text[:400]}"
                )

        items = (response.json() or {}).get("value") or []
        messages: List[EmailMessage] = []
        for item in items:
            if item.get("isRead") is True:
                continue
            if item.get("hasAttachments") is not True:
                continue

            sender = None
            raw_sender = item.get("from") or {}
            email_address = (raw_sender.get("emailAddress") or {})
            sender = email_address.get("address")

            messages.append(
                EmailMessage(
                    id=item["id"],
                    subject=str(item.get("subject") or ""),
                    sender=sender,
                    received_datetime=item.get("receivedDateTime"),
                    body_preview=item.get("bodyPreview"),
                )
            )
        return messages

    def list_attachments(
        self,
        mailbox: str,
        message_id: str,
    ) -> List[EmailAttachment]:
        url = f"{self._base}/users/{mailbox}/messages/{message_id}/attachments"
        params = {"$select": "id,name,contentType,size,isInline"}
        response = self._client.get(
            url,
            headers=self._headers(),
            params=params,
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph list attachments {response.status_code}: "
                f"{response.text[:400]}"
            )

        items = (response.json() or {}).get("value") or []
        attachments: List[EmailAttachment] = []
        for item in items:
            attachments.append(
                EmailAttachment(
                    id=item["id"],
                    name=str(item.get("name") or "attachment.bin"),
                    content_type=str(
                        item.get("contentType") or "application/octet-stream"
                    ),
                    size=int(item.get("size") or 0),
                    is_inline=bool(item.get("isInline") or False),
                    odata_type=(
                        str(item.get("@odata.type"))
                        if item.get("@odata.type")
                        else None
                    ),
                )
            )
        return attachments

    def download_attachment_value(
        self,
        mailbox: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        url = (
            f"{self._base}/users/{mailbox}/messages/{message_id}/attachments/"
            f"{attachment_id}/$value"
        )
        response = self._client.get(url, headers=self._headers())
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph attachment $value {response.status_code}: "
                f"{response.text[:400]}"
            )
        return response.content

    def move_message(
        self,
        mailbox: str,
        message_id: str,
        destination_folder_id: str,
    ) -> None:
        url = f"{self._base}/users/{mailbox}/messages/{message_id}/move"
        response = self._client.post(
            url,
            headers=self._headers(),
            json={"destinationId": destination_folder_id},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph move {response.status_code}: {response.text[:400]}"
            )
