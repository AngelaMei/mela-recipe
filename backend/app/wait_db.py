"""Block until Postgres accepts connections (used by the migrate init container)."""

import sys
import time

from sqlalchemy import text

from .db import engine

for attempt in range(60):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("database is ready")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"waiting for database ({attempt + 1}/60): {exc.__class__.__name__}")
        time.sleep(2)
sys.exit(1)
