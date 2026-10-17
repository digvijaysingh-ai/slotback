"""HTTP layer: ElevenLabs webhook tools, signed post-call webhook, timer sweep, verify upload.

    ElevenLabs agent ──POST /tools/<name>──▶ check X-Tool-Secret ─▶ resolve X-Call-Token
                                             ─▶ services.scheduling ─▶ Postgres + ledger
    ElevenLabs ──POST /hooks/post-call (ElevenLabs-Signature HMAC)──▶ record_call_outcome
    GitHub Actions cron ──POST /hooks/sweep──▶ expire holds, apply cut-offs
    Browser ──POST /api/sessions (access code)──▶ unbound token for a widget session

Logs are JSON with only pid / call_id / tool / outcome / latency (D24): no names,
dates of birth, ID digits or specialty ever reach a log line.
"""

import json
import logging
import os
import secrets
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from voiceledger import BundleInvalid, read_bundle
from voiceops.guard import RateLimiter, SafeLog, secret_matches, verify_webhook
from voiceops.guard.fastapi import ToolGuard, rate_limited, signed_webhook

from slotback.api.models import TOOLS
from slotback.dashboard.routes import mount_dashboard
from slotback.db import apply_schema
from slotback.ledger import verify as verify_ledger
from slotback.services import scheduling as svc

log = logging.getLogger("slotback")
MADRID = ZoneInfo("Europe/Madrid")


def madrid_now() -> datetime:
    return datetime.now(MADRID).replace(tzinfo=None)


@dataclass
class Settings:
    database_url: str
    tool_secret: str
    webhook_secret: str = ""
    access_code: str = ""
    live_hospital: str = "live"
    clock: Callable[[], datetime] = madrid_now

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            tool_secret=os.environ["TOOL_SECRET"],
            webhook_secret=os.environ.get("ELEVENLABS_WEBHOOK_SECRET", ""),
            access_code=os.environ.get("DEMO_ACCESS_CODE", ""),
            live_hospital=os.environ.get("LIVE_HOSPITAL", "live"),
        )


@dataclass
class Stats:
    """In-process latency samples per tool, shown as p50/p95 on the console (D23)."""

    samples: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=500))
    )
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    calls: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add(self, name: str, ms: float, ok: bool) -> None:
        self.samples[name].append(ms)
        self.calls[name] += 1
        if not ok:
            self.errors[name] += 1

    def summary(self) -> dict:
        out = {}
        for name, s in self.samples.items():
            ordered = sorted(s)
            out[name] = {
                "calls": self.calls[name],
                "errors": self.errors[name],
                "p50_ms": round(ordered[len(ordered) // 2], 1),
                "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 1),
            }
        return out


_jlog = SafeLog(log, extra_fields={"pid"})
verify_signature = verify_webhook


def _call_tool(name: str, conn, token: str, body: BaseModel, now: datetime) -> dict:
    data = body.model_dump()
    fn = {
        "record_disclosure": lambda: (
            svc.record_disclosure(conn, token, now) or {"status": "recorded"}
        ),
        "verify_identity": lambda: svc.verify_identity(conn, token, **data, now=now),
        "get_appointment": lambda: svc.get_appointment(conn, token, now),
        "confirm_appointment": lambda: svc.confirm_appointment(conn, token, now),
        "cancel_appointment": lambda: svc.cancel_appointment(
            conn, token, data["patient_confirmed"], now
        ),
        "list_alternative_slots": lambda: svc.list_alternative_slots(conn, token, now),
        "reschedule": lambda: svc.reschedule(conn, token, data["slot_id"], now),
        "offer_backfill": lambda: svc.offer_backfill(conn, token, now),
        "accept_backfill": lambda: svc.accept_backfill(conn, token, now),
        "decline_backfill": lambda: svc.decline_backfill(conn, token, now),
        "transfer_to_human": lambda: svc.transfer_to_human(conn, token, data["reason"], now),
        "opt_out": lambda: svc.opt_out(conn, token, now),
        "log_outcome": lambda: svc.log_outcome(conn, token, data["outcome"], now),
    }[name]
    return fn()


class SessionRequest(BaseModel):
    access_code: str
    purpose: str = "inbound"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    stats = Stats()
    guard = ToolGuard(settings.tool_secret, _jlog, limiter=RateLimiter(per_minute=120))
    upload_limited = Depends(rate_limited(RateLimiter(per_minute=10)))
    session_limited = Depends(rate_limited(RateLimiter(per_minute=5)))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pool = ConnectionPool(
            settings.database_url, kwargs={"autocommit": True}, min_size=1, max_size=8, open=True
        )
        with pool.connection() as conn:
            apply_schema(conn)
        app.state.pool = pool
        yield
        pool.close()

    app = FastAPI(title="Slotback", lifespan=lifespan)
    app.state.settings = settings
    app.state.stats = stats

    for tool_name, (model, _desc) in TOOLS.items():

        def make(name=tool_name, Model=model):
            async def endpoint(
                body: Model,  # type: ignore[valid-type]
                x_call_token: str = Depends(guard.tool_call),
            ):
                started = time.perf_counter()
                ok, call_id = True, None
                try:
                    with app.state.pool.connection() as conn:
                        result = _call_tool(name, conn, x_call_token, body, settings.clock())
                        call_id = (
                            svc.resolve(conn, x_call_token).call_id
                            if name != ("log_outcome")
                            else None
                        )
                    payload = {"ok": True, **result}
                except svc.ServiceError as e:
                    ok = False
                    payload = {"ok": False, "error": e.code, "message": str(e)}
                ms = (time.perf_counter() - started) * 1000
                stats.add(name, ms, ok)
                _jlog(
                    event="tool",
                    tool=name,
                    call_id=call_id,
                    latency_ms=round(ms, 1),
                    status="ok" if ok else payload["error"],
                )
                return payload

            endpoint.__name__ = f"tool_{name}"
            app.post(f"/tools/{name}", tags=["tools"])(endpoint)

        make()

    @app.get("/health")
    def health():
        with app.state.pool.connection() as conn:
            n = conn.execute("SELECT count(*) FROM hospitals").fetchone()[0]
        return {"ok": True, "hospitals": n}

    @app.post("/hooks/post-call")
    async def post_call(raw: bytes = Depends(signed_webhook(settings.webhook_secret, _jlog))):
        event = json.loads(raw)
        data = event.get("data", {})
        dyn = (data.get("conversation_initiation_client_data") or {}).get("dynamic_variables", {})
        call_id = dyn.get("call_id")
        if not call_id:
            return {"ok": True, "ignored": "no call_id"}
        if event.get("type") == "call_initiation_failure":
            reason = (data.get("failure_reason") or "").replace("-", "_")
            outcome = reason if reason in ("no_answer", "busy") else "failed"
        else:
            with app.state.pool.connection() as conn:
                row = conn.execute(
                    "SELECT outcome FROM calls WHERE call_id = %s", (call_id,)
                ).fetchone()
            outcome = "voicemail" if row and row[0] == "voicemail" else "completed"
        transcript = data.get("transcript")
        if transcript:
            turns = [
                {"role": t.get("role"), "message": t.get("message")}
                for t in transcript
                if t.get("message")
            ]
            with app.state.pool.connection() as conn:
                conn.execute(
                    "UPDATE calls SET transcript = %s WHERE call_id = %s",
                    (json.dumps(turns), call_id),
                )
        try:
            with app.state.pool.connection() as conn:
                res = svc.record_call_outcome(
                    conn, call_id, outcome, settings.clock(), data.get("conversation_id")
                )
        except svc.NotFound:
            return {"ok": True, "ignored": "unknown call"}
        _jlog(event="post_call", call_id=call_id, outcome=outcome)
        return {"ok": True, **res}

    @app.post("/hooks/sweep", dependencies=[Depends(guard.require_secret)])
    def sweep():
        with app.state.pool.connection() as conn:
            return {"ok": True, **svc.sweep(conn, settings.live_hospital, settings.clock())}

    def check_access(code: str) -> None:
        if not secret_matches(code, settings.access_code):
            raise HTTPException(403, "wrong access code")

    @app.post("/api/sessions", dependencies=[session_limited])
    def new_session(req: SessionRequest):
        check_access(req.access_code)
        if req.purpose not in ("inbound", "confirm"):
            raise HTTPException(400, "sessions are inbound (widget) or confirm (demo phone call)")
        with app.state.pool.connection() as conn:
            pid = None
            if req.purpose == "confirm":
                # Demo outbound call: bound to the first synthetic appointment of the live
                # day, so the patient still has to pass verify_identity as that patient.
                pid = conn.execute(
                    "SELECT pid FROM appointments WHERE hospital_id = %s"
                    " ORDER BY appointment_id LIMIT 1",
                    (settings.live_hospital,),
                ).fetchone()[0]
            call_id, token = svc.start_call(
                conn, settings.live_hospital, req.purpose, settings.clock(), pid=pid
            )
        return {"call_id": call_id, "call_token": token}

    @app.post("/api/verify", dependencies=[upload_limited])
    async def verify_upload(file: UploadFile, trusted_key: str | None = None):
        data = await file.read(5 * 1024 * 1024 + 1)
        try:
            events, snapshots, head = read_bundle(data)
        except BundleInvalid as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return verify_ledger(events, snapshots, head, trusted_key).to_dict()

    @app.get("/api/stats")
    def tool_stats():
        return stats.summary()

    @app.post("/api/kill-switch")
    def kill_switch(access_code: str, paused: bool):
        check_access(access_code)
        with app.state.pool.connection() as conn:
            conn.execute(
                "INSERT INTO settings (hospital_id, calling_paused) VALUES (%s, %s)"
                " ON CONFLICT (hospital_id) DO UPDATE SET calling_paused = EXCLUDED.calling_paused",
                (settings.live_hospital, paused),
            )
            conn.execute(
                "INSERT INTO staff_actions (hospital_id, action, detail, at)"
                " VALUES (%s, %s, %s, %s)",
                (
                    settings.live_hospital,
                    "kill_switch",
                    json.dumps({"paused": paused}),
                    settings.clock(),
                ),
            )
        return {"ok": True, "calling_paused": paused}

    mount_dashboard(app)
    return app


def new_secret() -> str:
    return secrets.token_urlsafe(32)
