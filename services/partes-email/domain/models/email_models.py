# domain/models/email_models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EmailMessage:
    id: str
    subject: str
    sender: Optional[str]
    received_datetime: Optional[str]
    body_preview: Optional[str] = None


@dataclass(frozen=True)
class EmailAttachment:
    id: str
    name: str
    content_type: str
    size: int
    is_inline: bool
    odata_type: Optional[str] = None
