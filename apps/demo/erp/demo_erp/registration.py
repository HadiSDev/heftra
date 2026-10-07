"""Point the demo company's ERP integration at this service."""
from __future__ import annotations

import json
import uuid

import psycopg2
from cryptography.fernet import Fernet

from . import settings

INTEGRATIONS_SQL = "select id from erp_integrations where erp_type = %s and disconnected_at is null"

UPSERT_SQL = """
insert into erp_credentials (id, erp_integration_id, encrypted_config)
values (%s, %s, %s)
on conflict (erp_integration_id)
do update set encrypted_config = excluded.encrypted_config, updated_at = now()
"""


def register() -> int:
    """Store this service's address as each mock integration's credentials; returns how many."""
    config = json.dumps({"api_key": "demo", "base_url": settings.PUBLIC_URL}, sort_keys=True)
    token = Fernet(settings.CREDENTIAL_KEY.encode()).encrypt(config.encode()).decode()
    with psycopg2.connect(settings.DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(INTEGRATIONS_SQL, (settings.ERP_TYPE,))
        integrations = [row[0] for row in cursor.fetchall()]
        for integration_id in integrations:
            credential_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"demo-erp/{integration_id}"))
            cursor.execute(UPSERT_SQL, (credential_id, integration_id, token))
    return len(integrations)
