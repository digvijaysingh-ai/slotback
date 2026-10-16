-- Slotback schema (Postgres 16). Synthetic data only.
-- Every row is scoped by hospital_id so eval runs get their own isolated hospital (EOV5)
-- and the showcase day stays read-only.
--
--   hospitals ─┬─ patients
--              ├─ slots ──── appointments
--              └─ waitlist_entries (rank = the hospital's order; the agent never changes it)
-- Ledger tables (list_snapshots, ledger_events, ledger_heads) are added on day 2.

CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id   text PRIMARY KEY,
    name          text NOT NULL,
    clinic_date   date NOT NULL,
    seed          bigint NOT NULL,
    read_only     boolean NOT NULL DEFAULT false,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS patients (
    hospital_id             text NOT NULL REFERENCES hospitals ON DELETE CASCADE,
    pid                     text NOT NULL,
    given_name              text NOT NULL,
    surname                 text NOT NULL,
    date_of_birth           date NOT NULL,
    id_number               text NOT NULL,
    phone                   text NOT NULL,
    language                text NOT NULL CHECK (language IN ('es', 'en', 'ro', 'ar')),
    hearing_difficulty      boolean NOT NULL,
    prior_visits_last_year  integer NOT NULL,
    opted_out               boolean NOT NULL DEFAULT false,
    PRIMARY KEY (hospital_id, pid)
);

CREATE TABLE IF NOT EXISTS slots (
    hospital_id  text NOT NULL REFERENCES hospitals ON DELETE CASCADE,
    slot_id      text NOT NULL,
    specialty    text NOT NULL,
    room         integer NOT NULL,
    starts_at    timestamp NOT NULL,
    minutes      integer NOT NULL,
    status       text NOT NULL DEFAULT 'booked'
                 CHECK (status IN ('booked', 'freed', 'offering', 'filled', 'unfilled')),
    version      integer NOT NULL DEFAULT 0,  -- compare-and-swap guard for claims
    PRIMARY KEY (hospital_id, slot_id)
);

CREATE TABLE IF NOT EXISTS appointments (
    hospital_id         text NOT NULL REFERENCES hospitals ON DELETE CASCADE,
    appointment_id      text NOT NULL,
    slot_id             text NOT NULL,
    pid                 text NOT NULL,
    specialty           text NOT NULL,
    booked_on           date NOT NULL,
    booking_delay_days  integer NOT NULL,
    no_show_propensity  double precision NOT NULL,  -- ILLUSTRATIVE analytics only
    will_no_show        boolean NOT NULL,            -- simulation input only
    status              text NOT NULL DEFAULT 'scheduled'
                        CHECK (status IN ('scheduled', 'confirmed', 'cancelled', 'rescheduled',
                                          'attended', 'no_show')),
    PRIMARY KEY (hospital_id, appointment_id),
    FOREIGN KEY (hospital_id, slot_id) REFERENCES slots,
    FOREIGN KEY (hospital_id, pid) REFERENCES patients
);

CREATE TABLE IF NOT EXISTS waitlist_entries (
    hospital_id  text NOT NULL REFERENCES hospitals ON DELETE CASCADE,
    specialty    text NOT NULL,
    rank         integer NOT NULL CHECK (rank >= 1),
    pid          text NOT NULL,
    priority     text NOT NULL CHECK (priority IN ('preferente', 'ordinaria')),
    referred_on  date NOT NULL,
    PRIMARY KEY (hospital_id, specialty, rank),
    UNIQUE (hospital_id, specialty, pid),
    FOREIGN KEY (hospital_id, pid) REFERENCES patients
);

CREATE INDEX IF NOT EXISTS appointments_slot ON appointments (hospital_id, slot_id);
CREATE INDEX IF NOT EXISTS slots_day ON slots (hospital_id, starts_at);

-- Calls and their per-call tokens (D15 / 1C / EOV2). Tools resolve the patient
-- from the token, never from an id the LLM sends. Unbound tokens (widget, inbound)
-- bind to one patient on a successful verify_identity.
CREATE TABLE IF NOT EXISTS calls (
    call_id          text PRIMARY KEY,
    token            text NOT NULL UNIQUE,
    hospital_id      text NOT NULL REFERENCES hospitals ON DELETE CASCADE,
    pid              text,               -- NULL until bound (widget / inbound)
    purpose          text NOT NULL CHECK (purpose IN ('confirm', 'backfill', 'inbound')),
    slot_id          text,               -- backfill: the freed slot being offered
    rank             integer,            -- backfill: rank being offered
    verified         boolean NOT NULL DEFAULT false,
    identity_failures integer NOT NULL DEFAULT 0,
    conversation_id  text,               -- ElevenLabs trace id (D24)
    started_at       timestamp NOT NULL,
    ended_at         timestamp,
    outcome          text,
    transcript       jsonb,              -- from the post-call webhook (demo calls only)
    campaign_key     text,               -- one call per appointment per campaign day (D18)
    UNIQUE (hospital_id, campaign_key)  -- per hospital, so eval runs never collide (EOV5)
);
CREATE INDEX IF NOT EXISTS calls_pid ON calls (hospital_id, pid, started_at);

-- One row per freed slot being backfilled.
CREATE TABLE IF NOT EXISTS backfills (
    hospital_id  text NOT NULL REFERENCES hospitals ON DELETE CASCADE,
    slot_id      text NOT NULL,
    status       text NOT NULL,
    snapshot_id  text NOT NULL,
    ranked_pids  jsonb NOT NULL,
    rank         integer NOT NULL,
    hold_until   timestamp,
    filled_by    text,
    PRIMARY KEY (hospital_id, slot_id)
);

-- Actions taken from the dashboard (D17): who, what, when.
CREATE TABLE IF NOT EXISTS staff_actions (
    id           bigserial PRIMARY KEY,
    hospital_id  text NOT NULL,
    action       text NOT NULL,
    detail       jsonb NOT NULL DEFAULT '{}',
    at           timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    hospital_id  text PRIMARY KEY REFERENCES hospitals ON DELETE CASCADE,
    calling_paused boolean NOT NULL DEFAULT false
);
