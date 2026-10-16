"""Export the simulated showcase as a static site (free static Space / any static host).

    uv run python scripts/export_static.py        # writes dist/site/

Pages are rendered by the real app (embedded Postgres, showcase rebuilt), with the
`X-Static-Export` header so server-only actions become precomputed results or notes.
Links are rewritten to relative .html paths. Nothing live is included.
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import psycopg
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo
from slotledger import read_bundle, verify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "site"
H = {"x-static-export": "1"}
PAGES = {
    "/?lang=en": "index.html",
    "/impact": "impact.html",
    "/console?h=showcase": "console.html",
    "/roi": "roi.html",
    "/evals": "evals.html",
    "/verify": "verify.html",
    "/try": "try.html",
}


def rewrite(html: str, depth: int = 0) -> str:
    up = "../" * depth
    html = re.sub(r'href="/calls/([^"]+)"', lambda m: f'href="{up}calls/{m.group(1)}.html"', html)
    for path, name in [
        ("/impact", "impact.html"),
        ("/roi", "roi.html"),
        ("/evals", "evals.html"),
        ("/verify", "verify.html"),
        ("/try", "try.html"),
    ]:
        html = html.replace(f'href="{path}"', f'href="{up}{name}"')
    html = re.sub(r'href="/console[^"]*"', f'href="{up}console.html"', html)
    html = html.replace('href="/"', f'href="{up}index.html"')
    html = html.replace('"/static/', f'"{up}static/').replace('"/evidence/', f'"{up}evidence/')
    return html


def main() -> None:
    from slotback.api.app import Settings, create_app
    from slotback.localdb import database_url
    from slotback.serve import boot

    base = database_url(str(ROOT / ".data" / "pg-export"))
    schema = f"export_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(base, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{schema}"')
    url = make_conninfo(base, options=f"-csearch_path={schema}")
    boot(url, "live")
    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "calls").mkdir(parents=True)
    settings = Settings(url, "static", "", "", "live", clock=lambda: datetime(2026, 10, 13, 21))
    with TestClient(create_app(settings)) as client:
        for path, name in PAGES.items():
            r = client.get(path, headers=H)
            r.raise_for_status()
            (OUT / name).write_text(rewrite(r.text))
        console = client.get("/console?h=showcase", headers=H).text
        pages = int(re.search(r"Page 1 of (\d+)", console).group(1))
        for p in range(2, pages + 1):
            r = client.get(f"/console?h=showcase&p={p}", headers=H)
            (OUT / f"console-p{p}.html").write_text(rewrite(r.text))
        with psycopg.connect(url, autocommit=True) as conn:
            ids = [
                r[0]
                for r in conn.execute("SELECT call_id FROM calls WHERE hospital_id = 'showcase'")
            ]
        for cid in ids:
            r = client.get(f"/calls/{cid}", headers=H)
            (OUT / "calls" / f"{cid}.html").write_text(rewrite(r.text, depth=1))
        seq = int(
            re.search(
                r'id="tamper-btn" data-seq="(\d+)"', console and (OUT / "impact.html").read_text()
            ).group(1)
        )
        (OUT / "tamper.json").write_text(
            json.dumps(client.post("/api/demo/tamper", json={"seq": seq}).json())
        )
    shutil.copytree(ROOT / "slotback" / "dashboard" / "static", OUT / "static")
    (OUT / "evidence").mkdir()
    for f in ["showcase-2026-10-16.zip", "trusted_key.txt"]:
        shutil.copy2(ROOT / "evidence" / f, OUT / "evidence" / f)
    events, snaps, head = read_bundle((ROOT / "evidence" / "showcase-2026-10-16.zip").read_bytes())
    key = (ROOT / "evidence" / "trusted_key.txt").read_text().strip()
    (OUT / "verify-sample.json").write_text(json.dumps(verify(events, snaps, head, key).to_dict()))
    with psycopg.connect(base, autocommit=True) as c:
        c.execute(f'DROP SCHEMA "{schema}" CASCADE')
    n = sum(1 for _ in OUT.rglob("*.html"))
    print(f"exported {n} pages to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
