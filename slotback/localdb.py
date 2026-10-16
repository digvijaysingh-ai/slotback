"""DATABASE_URL if set, otherwise an embedded Postgres (pgserver) under .data/pg.

Used by the simulator locally and by the Space container (Postgres co-located with
the app, no third-party database account).
"""

from __future__ import annotations

import os
from pathlib import Path


def database_url(data_dir: str | None = None) -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    import pgserver

    path = Path(data_dir or os.environ.get("PGDATA_DIR", ".data/pg")).resolve()
    path.mkdir(parents=True, exist_ok=True)
    server = pgserver.get_server(path, cleanup_mode=None)
    return server.get_uri()
