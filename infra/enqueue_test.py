# enqueue_test.py
"""Encola un mensaje de prueba en q-extraccion con JSON correcto (evita el
mangling de comillas de PowerShell+az). El blob input/{DOCID}.pdf debe existir.

Uso (PowerShell):
    $env:STKEY = az storage account keys list -g $RG -n $STORAGE --query "[0].value" -o tsv
    python enqueue_test.py <STORAGE_ACCOUNT> <DOCID> [cola]

Requisito una sola vez:  pip install azure-storage-queue
"""
from __future__ import annotations

import json
import os
import sys

from azure.storage.queue import QueueClient


def main() -> int:
    if len(sys.argv) < 3:
        print("uso: python enqueue_test.py <STORAGE_ACCOUNT> <DOCID> [cola]")
        return 2
    account = sys.argv[1]
    docid = sys.argv[2]
    cola = sys.argv[3] if len(sys.argv) > 3 else "q-extraccion"
    key = os.environ.get("STKEY")
    if not key:
        print("Falta la variable de entorno STKEY (clave de la storage).")
        return 2

    conn = (
        f"DefaultEndpointsProtocol=https;AccountName={account};"
        f"AccountKey={key};EndpointSuffix=core.windows.net"
    )
    qc = QueueClient.from_connection_string(conn, cola)
    payload = {
        "document_id": docid,
        "filename": "parte.pdf",
        "mime_type": "application/pdf",
        "context": {},
    }
    qc.send_message(json.dumps(payload, ensure_ascii=False))
    print(f"encolado en {cola}: {docid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
