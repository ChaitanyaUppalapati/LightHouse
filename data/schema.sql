-- Lighthouse database schema (data/ track, task K1).
--
-- Columns mirror the FROZEN shared state model in lighthouse_common/schemas.py
-- (architecture reference §2). The five object tables hold the full chain that
-- flows through the system: Signal -> ThreatAssessment -> ActionProposal ->
-- RoutingDecision -> ActionResult. people/guardians/trust_grants model the
-- two-role permission design (§8). ledger_events is the audit trail (§9); its
-- append-only lockdown (REVOKE UPDATE/DELETE) is applied later in task K3.
--
-- Everything here is idempotent (CREATE ... IF NOT EXISTS) so it is safe to
-- apply repeatedly. Free-form / list fields from the schema are stored as JSONB.

-- ---------------------------------------------------------------------------
-- Identities & the consent relationship (§8: asymmetric two-role model)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS people (
    person_id   UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS guardians (
    guardian_id UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- A guardian's authority over a person. This is the "prior consent" the
-- architecture leans on (§8/§13): protection can only be granted/removed via a
-- trust grant, never by the protected person acting alone.
CREATE TABLE IF NOT EXISTS trust_grants (
    id          BIGSERIAL PRIMARY KEY,
    person_id   UUID NOT NULL REFERENCES people(person_id),
    guardian_id UUID NOT NULL REFERENCES guardians(guardian_id),
    granted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (person_id, guardian_id)
);

-- ---------------------------------------------------------------------------
-- The five shared objects (lighthouse_common/schemas.py)
-- ---------------------------------------------------------------------------

-- Signal: a raw thing observed in the world. Read-only, never trusted. We do
-- NOT foreign-key person_id here on purpose: a malformed/unknown signal must
-- still be recorded for the Watcher to flag, never silently dropped (§3).
CREATE TABLE IF NOT EXISTS signals (
    signal_id   TEXT PRIMARY KEY,
    person_id   UUID NOT NULL,
    source      TEXT NOT NULL
                CHECK (source IN ('email', 'transaction', 'account_event', 'voice')),
    payload     JSONB NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ThreatAssessment: the Watcher's LLM judgment about a Signal.
CREATE TABLE IF NOT EXISTS threat_assessments (
    assessment_id TEXT PRIMARY KEY,
    signal_id     TEXT NOT NULL REFERENCES signals(signal_id),
    category      TEXT NOT NULL
                  CHECK (category IN ('scam_phishing', 'financial_anomaly',
                                      'missed_obligation', 'account_risk', 'benign')),
    severity      TEXT NOT NULL CHECK (severity IN ('none', 'low', 'moderate', 'high')),
    confidence    DOUBLE PRECISION NOT NULL,
    rationale     TEXT NOT NULL,
    evidence      JSONB NOT NULL DEFAULT '[]'::jsonb,   -- list[str]
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ActionProposal: the Guardian's chosen response. action_type must be a key in
-- lighthouse_common/action_registry.yaml (enforced by the pipeline, not the DB).
CREATE TABLE IF NOT EXISTS action_proposals (
    proposal_id     TEXT PRIMARY KEY,
    assessment_id   TEXT NOT NULL REFERENCES threat_assessments(assessment_id),
    action_type     TEXT NOT NULL,
    target          JSONB NOT NULL DEFAULT '{}'::jsonb,
    rationale       TEXT NOT NULL,
    expected_effect TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RoutingDecision: the deterministic gate's verdict (one per proposal).
CREATE TABLE IF NOT EXISTS routing_decisions (
    proposal_id TEXT PRIMARY KEY REFERENCES action_proposals(proposal_id),
    route       TEXT NOT NULL CHECK (route IN ('autonomous', 'human_gate', 'watch_only')),
    reason      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ActionResult: what actually happened. Surrogate id (not proposal_id PK) so a
-- failed-then-retried action can keep its full history.
CREATE TABLE IF NOT EXISTS action_results (
    id           BIGSERIAL PRIMARY KEY,
    proposal_id  TEXT NOT NULL REFERENCES action_proposals(proposal_id),
    status       TEXT NOT NULL
                 CHECK (status IN ('executed', 'approved_executed', 'denied',
                                   'failed', 'watching')),
    evidence     JSONB NOT NULL DEFAULT '{}'::jsonb,
    undo_token   TEXT,
    completed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_action_results_proposal ON action_results(proposal_id);

-- ---------------------------------------------------------------------------
-- Ledger (§9: the immutable audit trail / tamper-evidence story)
-- Created here in K1; locked append-only (REVOKE UPDATE, DELETE) in K3.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ledger_events (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    person_id   UUID,
    event_type  TEXT NOT NULL,
    details     JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ledger_events_person ON ledger_events(person_id);
CREATE INDEX IF NOT EXISTS idx_ledger_events_ts ON ledger_events(ts DESC);

-- ---------------------------------------------------------------------------
-- Approvals (K4: the approval bridge §4.4)
-- The link between the Escalation agent (C4) and the family dashboard (S6).
-- Escalation creates a pending approval with a plain message; the dashboard
-- lists pending ones and records the family's decision; the agent polls for it.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    person_id   UUID,
    proposal    JSONB NOT NULL DEFAULT '{}'::jsonb,   -- the ActionProposal being gated
    message     TEXT NOT NULL,                         -- plain 6th-grade ask for the family
    detail      TEXT,                                  -- optional longer explanation
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'approved', 'denied')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
