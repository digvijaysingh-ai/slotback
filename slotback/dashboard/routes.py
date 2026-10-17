"""Dashboard pages (DESIGN.md + docs/07_ux.md). Server-rendered, read-only by default.

Every number on a page comes from metrics/registry.json or from the database, and
carries a provenance tag. Actions (kill switch, demo sessions) need the access code.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from voiceledger.pg import load_events, load_snapshots

from slotback.dashboard.i18n import STRINGS
from slotback.ledger import verify
from slotback.services.scheduling import chain_id

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SHOWCASE = "showcase"
CARE_TYPES = {
    "ai_disclosed": "AI disclosed",
    "identity_verified": "Identity verified",
    "read_back": "Read back",
    "handoff_to_human": "Handed to a human",
}
REPLAY_TYPES = {
    "slot_freed",
    "list_snapshot",
    "call_attempt",
    "identity_verified",
    "identity_failed",
    "offer_started",
    "offer_accepted",
    "offer_declined",
    "offer_expired",
    "rank_skipped",
    "read_back",
    "slot_filled",
    "slot_unfilled",
    "late_accept_rejected",
}
SPECIALTY_LABEL = {
    "cardiology": "Cardiology",
    "dermatology": "Dermatology",
    "orthopaedics": "Orthopaedics",
    "ophthalmology": "Ophthalmology",
    "gastroenterology": "Gastroenterology",
}


def load_registry() -> dict:
    path = ROOT / "metrics" / "registry.json"
    return json.loads(path.read_text()) if path.exists() else {}


def load_eval_results() -> dict | None:
    path = ROOT / "evals" / "results" / "latest.json"
    return json.loads(path.read_text()) if path.exists() else None


class TamperRequest(BaseModel):
    seq: int


def mount_dashboard(app: FastAPI) -> None:
    templates = Jinja2Templates(directory=str(HERE / "templates"))
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
    registry = load_registry()

    def lang_of(request: Request) -> str:
        q = request.query_params.get("lang")
        return q if q in ("en", "es") else request.cookies.get("lang", "en")

    def render(request: Request, name: str, **ctx):
        lang = lang_of(request)
        t = STRINGS[lang]
        resp = templates.TemplateResponse(
            request,
            name,
            {
                "t": t,
                "lang": lang,
                "reg": registry,
                "page": name.split(".")[0],
                "static_mode": request.headers.get("x-static-export") == "1",
                **ctx,
            },
        )
        if request.query_params.get("lang") in ("en", "es"):
            resp.set_cookie("lang", lang, max_age=60 * 60 * 24 * 180, samesite="lax")
        return resp

    def pool():
        return app.state.pool

    def showcase_events():
        with pool().connection() as conn:
            cid = chain_id(conn, SHOWCASE)
            return cid, load_events(conn, cid), load_snapshots(conn, cid)

    def hospital_param(request: Request) -> str:
        h = request.query_params.get("h", SHOWCASE)
        return h if h in (SHOWCASE, app.state.settings.live_hospital) else SHOWCASE

    @app.get("/", response_class=HTMLResponse)
    def landing(request: Request):
        return render(request, "landing.html")

    @app.get("/impact", response_class=HTMLResponse)
    def impact(request: Request):
        cid, events, snaps = showcase_events()
        report = verify(events, snaps)
        with pool().connection() as conn:
            slots = {
                s: (sp, st)
                for s, sp, st in conn.execute(
                    "SELECT slot_id, specialty, starts_at FROM slots WHERE hospital_id = %s",
                    (SHOWCASE,),
                )
            }
        lanes: dict[str, list] = {k: [] for k in SPECIALTY_LABEL}
        marks: dict[str, dict] = {}
        replay = []
        for e in events:
            if e.type not in REPLAY_TYPES:
                continue
            replay.append(
                {
                    "seq": e.seq,
                    "ts": e.ts[11:16],
                    "type": e.type,
                    "slot": e.slot_id,
                    "rank": e.payload.get("rank"),
                    "outcome": e.payload.get("outcome"),
                    "care": e.type in CARE_TYPES,
                }
            )
            if e.type == "slot_freed":
                hh, mm = int(e.ts[11:13]), int(e.ts[14:16])
                pos = max(3.0, min(95.0, ((hh * 60 + mm) - 9 * 60) / (11 * 60) * 100))
                marks[e.slot_id] = {
                    "slot": e.slot_id,
                    "pos": round(pos, 2),
                    "state": "freed",
                    "rank": None,
                    "time": e.ts[11:16],
                }
            elif e.type == "slot_filled" and e.slot_id in marks:
                marks[e.slot_id] |= {"state": "ok", "rank": e.payload.get("rank")}
            elif e.type == "slot_unfilled" and e.slot_id in marks:
                marks[e.slot_id]["state"] = "un"
        for m in sorted(marks.values(), key=lambda m: m["pos"]):
            spec = slots.get(m["slot"], ("cardiology", None))[0]
            row = 0  # stack markers that would overlap (closer than 6% of the day)
            while any(abs(o["pos"] - m["pos"]) < 6 and o["row"] == row for o in lanes[spec]):
                row += 1
            lanes[spec].append(m | {"row": row})
        trusted = ROOT / "evidence" / "trusted_key.txt"
        return render(
            request,
            "impact.html",
            lanes={SPECIALTY_LABEL[k]: v for k, v in lanes.items()},
            replay=replay,
            report=report.to_dict(),
            chain_id=cid,
            last_events=replay[-14:],
            trusted_key=trusted.read_text().strip() if trusted.exists() else None,
        )

    @app.post("/api/demo/tamper")
    def tamper(req: TamperRequest):
        """Change one event in an in-memory COPY and verify it. The stored ledger is untouched."""
        _, events, snaps = showcase_events()
        idx = next((i for i, e in enumerate(events) if e.seq == req.seq), None)
        if idx is None:
            raise HTTPException(404, "no such event")
        copy = list(events)
        copy[idx] = replace(copy[idx], payload={**copy[idx].payload, "edited_after_the_fact": True})
        return verify(copy, snaps).to_dict()

    @app.get("/console", response_class=HTMLResponse)
    def console(request: Request):
        h = hospital_param(request)
        status = request.query_params.get("status", "all")
        page = max(1, int(request.query_params.get("p", "1") or 1))
        with pool().connection() as conn:
            exists = conn.execute("SELECT 1 FROM hospitals WHERE hospital_id = %s", (h,)).fetchone()
            if not exists:
                return render(
                    request,
                    "console.html",
                    h=h,
                    calls=[],
                    slots=[],
                    handoffs=[],
                    counts={},
                    statuses=[],
                    page=1,
                    pages=1,
                    status=status,
                    paused=False,
                    stats=app.state.stats.summary(),
                    alerts=[],
                )
            where, params = "c.hospital_id = %s", [h]
            if status != "all":
                where += " AND coalesce(c.outcome, 'in_progress') = %s"
                params.append(status)
            total = conn.execute(f"SELECT count(*) FROM calls c WHERE {where}", params).fetchone()[
                0
            ]
            rows = conn.execute(
                "SELECT c.call_id, c.pid, c.purpose, c.verified,"
                " coalesce(c.outcome, 'in_progress'),"
                " c.started_at, c.ended_at, c.rank,"
                " coalesce(sl.specialty, (SELECT a.specialty FROM appointments a WHERE"
                "   a.hospital_id = c.hospital_id AND a.pid = c.pid LIMIT 1))"
                f" FROM calls c LEFT JOIN slots sl ON sl.hospital_id = c.hospital_id"
                f" AND sl.slot_id = c.slot_id WHERE {where}"
                " ORDER BY c.started_at DESC, c.call_id LIMIT 50 OFFSET %s",
                [*params, (page - 1) * 50],
            ).fetchall()
            ids = [r[0] for r in rows]
            care = {}
            if ids:
                for cid_, typ in conn.execute(
                    "SELECT payload->>'call_id', type FROM ledger_events WHERE chain_id LIKE %s"
                    " AND payload->>'call_id' = ANY(%s) AND type = ANY(%s)",
                    (f"{h}:%", ids, list(CARE_TYPES)),
                ):
                    care.setdefault(cid_, []).append(CARE_TYPES[typ])
            counts = dict(
                conn.execute(
                    "SELECT coalesce(outcome, 'in_progress'), count(*) FROM calls"
                    " WHERE hospital_id = %s GROUP BY 1",
                    (h,),
                ).fetchall()
            )
            slots = conn.execute(
                "SELECT b.slot_id, s.specialty, b.status, b.rank, b.filled_by,"
                " jsonb_array_length(b.ranked_pids) FROM backfills b JOIN slots s"
                " USING (hospital_id, slot_id) WHERE b.hospital_id = %s ORDER BY s.starts_at",
                (h,),
            ).fetchall()
            handoffs = conn.execute(
                "SELECT ts, payload->>'call_id', payload->>'reason' FROM ledger_events"
                " WHERE chain_id LIKE %s AND type = 'handoff_to_human' ORDER BY seq DESC LIMIT 20",
                (f"{h}:%",),
            ).fetchall()
            paused_row = conn.execute(
                "SELECT calling_paused FROM settings WHERE hospital_id = %s", (h,)
            ).fetchone()
        calls = [
            {
                "call_id": r[0],
                "pid": r[1] or "—",
                "purpose": r[2],
                "verified": r[3],
                "outcome": r[4],
                "started": r[5].strftime("%H:%M") if r[5] else "—",
                "duration": _dur(r[5], r[6]),
                "rank": r[7],
                "specialty": SPECIALTY_LABEL.get(r[8], "—") if r[3] else "—",
                "care": care.get(r[0], []),
            }
            for r in rows
        ]
        stats = app.state.stats.summary()
        unreached = {"voicemail", "no_answer", "busy", "wrong_number", "failed", "in_progress"}
        summary = {
            "answered": sum(n for k, n in counts.items() if k not in unreached),
            "voicemail": counts.get("voicemail", 0),
            "no_answer": counts.get("no_answer", 0) + counts.get("busy", 0),
        }
        return render(
            request,
            "console.html",
            h=h,
            calls=calls,
            counts=summary,
            statuses=sorted(counts),
            status=status,
            page=page,
            pages=max(1, -(-total // 50)),
            total=total,
            paused=bool(paused_row and paused_row[0]),
            slots=[
                {
                    "slot": s,
                    "specialty": SPECIALTY_LABEL.get(sp, sp),
                    "status": st,
                    "rank": rk,
                    "filled_by": fb,
                    "depth": d,
                }
                for s, sp, st, rk, fb, d in slots
            ],
            handoffs=handoffs,
            stats=stats,
            alerts=_alerts(stats, handoffs),
        )

    @app.get("/calls/{call_id}", response_class=HTMLResponse)
    def call_detail(request: Request, call_id: str):
        with pool().connection() as conn:
            row = conn.execute(
                "SELECT hospital_id, pid, purpose, verified, coalesce(outcome, 'in_progress'),"
                " started_at, ended_at, transcript, conversation_id, rank, slot_id"
                " FROM calls WHERE call_id = %s",
                (call_id,),
            ).fetchone()
            if row is None:
                return render(request, "call_detail.html", call=None, events=[], call_id=call_id)
            events = conn.execute(
                "SELECT seq, ts, type, payload FROM ledger_events WHERE chain_id LIKE %s"
                " AND payload->>'call_id' = %s ORDER BY seq",
                (f"{row[0]}:%", call_id),
            ).fetchall()
        flags = []
        types = [e[2] for e in events]
        if "detail_disclosed" in types and (
            "identity_verified" not in types
            or types.index("detail_disclosed") < types.index("identity_verified")
        ):
            flags.append(("privacy", "Detail disclosed before identity was verified"))
        if "handoff_to_human" in types:
            flags.append(("escalation", "Handed to a human"))
        call = {
            "call_id": call_id,
            "hospital": row[0],
            "pid": row[1] or "—",
            "purpose": row[2],
            "verified": row[3],
            "outcome": row[4],
            "duration": _dur(row[5], row[6]),
            "transcript": row[7],
            "conversation_id": row[8],
            "rank": row[9],
            "slot": row[10],
            "simulated": row[0] == SHOWCASE,
        }
        return render(
            request,
            "call_detail.html",
            call=call,
            flags=flags,
            call_id=call_id,
            events=[
                {
                    "seq": s,
                    "ts": ts[11:19],
                    "type": ty,
                    "care": ty in CARE_TYPES,
                    "payload": {k: v for k, v in p.items() if k not in ("call_id",)},
                }
                for s, ts, ty, p in events
            ],
        )

    @app.get("/roi", response_class=HTMLResponse)
    def roi(request: Request):
        return render(request, "roi.html")

    @app.get("/evals", response_class=HTMLResponse)
    def evals(request: Request):
        return render(request, "evals.html", results=load_eval_results())

    @app.get("/verify", response_class=HTMLResponse)
    def verify_page(request: Request):
        trusted = ROOT / "evidence" / "trusted_key.txt"
        return render(
            request,
            "verify.html",
            trusted_key=trusted.read_text().strip() if trusted.exists() else None,
        )

    @app.get("/evidence/{name}")
    def evidence(name: str):
        path = (ROOT / "evidence" / name).resolve()
        if path.parent != (ROOT / "evidence").resolve() or not path.exists():
            raise HTTPException(404)
        return FileResponse(path)

    @app.get("/try", response_class=HTMLResponse)
    def try_page(request: Request):
        import os

        return render(request, "try.html", agent_id=os.environ.get("ELEVENLABS_INBOUND_AGENT_ID"))


def _dur(start, end) -> str:
    if not start or not end:
        return "—"
    s = int((end - start).total_seconds())
    return f"{s // 60}:{s % 60:02d}"


def _alerts(stats: dict, handoffs) -> list[tuple[str, str]]:
    out = []
    for name, s in stats.items():
        if s["calls"] >= 20 and s["errors"] / s["calls"] > 0.05:
            out.append(("err", f"Tool {name}: error rate above 5%"))
        if s["p95_ms"] > 300:
            out.append(("warn", f"Tool {name}: p95 {s['p95_ms']} ms is over the 300 ms budget"))
    if len(handoffs) >= 5:
        out.append(("warn", f"{len(handoffs)} recent handoffs to a human"))
    return out
