// S6 — talk to Keya's data service (K4 approval bridge + K3 ledger).
// Base URL from VITE_DATA_URL, default http://localhost:8001. Each call throws on
// failure so the dashboard can fall back to sample data and stay demo-safe.
const DATA_URL = (import.meta.env.VITE_DATA_URL || "http://localhost:8001").replace(/\/+$/, "");

// Friendly titles for ledger events that don't carry their own (e.g. approval_requested).
const EVENT_TITLES = {
  email_received: "New email arrived",
  scam_detected: "Flagged an email as a scam",
  email_quarantined: "Quarantined the email",
  approval_requested: "Asked family for a decision",
  family_notified: "Notified the family",
  sender_blocked: "Blocked a sender",
  approved: "You approved an action",
  denied: "You denied an action",
};

async function getJSON(path) {
  const res = await fetch(`${DATA_URL}${path}`, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

// Pending approvals -> the shape ApprovalCard expects.
export async function fetchApprovals() {
  const rows = await getJSON("/approvals?status=pending");
  return rows.map((a) => ({
    id: a.approval_id || a.id,
    message: a.message,
    detail: a.detail || "",
    amount: a.proposal?.amount || null,
    receivedAt: a.created_at,
  }));
}

// Ledger (already newest-first) -> the shape Timeline expects.
export async function fetchLedger() {
  const rows = await getJSON("/ledger");
  return rows.map((e) => ({
    id: String(e.id),
    type: e.event_type,
    title: e.details?.title || EVENT_TITLES[e.event_type] || e.event_type,
    detail: e.details?.detail || e.details?.message || "",
    at: e.ts || e.created_at,
  }));
}

// Record the family's decision. Backend expects "approved" | "denied".
export async function decideApproval(id, decision) {
  const res = await fetch(`${DATA_URL}/approvals/${id}/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!res.ok) throw new Error(`decide ${id} -> ${res.status}`);
  return res.json();
}

export { DATA_URL };
