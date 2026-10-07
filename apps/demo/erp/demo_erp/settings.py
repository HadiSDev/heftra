"""Configuration from the environment."""
from __future__ import annotations

import os

DATABASE_URL = os.environ["DATABASE_URL"]
CREDENTIAL_KEY = os.environ["WEB_API_CREDENTIAL_ENC_KEY"]
PUBLIC_URL = os.getenv("DEMO_ERP_URL", "http://demo-erp:8001")
ERP_TYPE = "mock"
