-- Lighthouse ledger lockdown (task K3) — our TAMPER-EVIDENCE feature (arch §9).
--
-- ledger_events is APPEND-ONLY: once an event is written it can never be edited
-- or removed. An agent acting in someone's financial life must be fully
-- accountable, so the audit trail has to be provably un-rewritable.
--
-- We enforce this in two layers, because they cover different callers:
--
--   1) REVOKE UPDATE, DELETE — removes those privileges at the SQL permission
--      layer. This stops ordinary (non-owner) roles.
--
--   2) A trigger that RAISES on UPDATE / DELETE / TRUNCATE — this is the layer
--      that actually guarantees the property. The table owner and any superuser
--      BYPASS privilege checks (our local app role `lighthouse` is a superuser),
--      so REVOKE alone would not stop them. Triggers are not privilege checks —
--      they fire for everyone — so this makes "deleting a ledger row is refused"
--      true even for an admin connection.
--
-- Idempotent: safe to apply on every startup.

REVOKE UPDATE, DELETE ON ledger_events FROM PUBLIC;

CREATE OR REPLACE FUNCTION ledger_events_block_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'ledger_events is append-only (tamper-evidence): % is not allowed', TG_OP;
END;
$$ LANGUAGE plpgsql;

-- Row-level guard for UPDATE / DELETE.
DROP TRIGGER IF EXISTS ledger_events_no_mutate ON ledger_events;
CREATE TRIGGER ledger_events_no_mutate
    BEFORE UPDATE OR DELETE ON ledger_events
    FOR EACH ROW EXECUTE FUNCTION ledger_events_block_mutation();

-- Statement-level guard for TRUNCATE (which has no per-row firing).
DROP TRIGGER IF EXISTS ledger_events_no_truncate ON ledger_events;
CREATE TRIGGER ledger_events_no_truncate
    BEFORE TRUNCATE ON ledger_events
    FOR EACH STATEMENT EXECUTE FUNCTION ledger_events_block_mutation();
