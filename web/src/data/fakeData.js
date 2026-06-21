// FAKE data for the family dashboard (S1) and history timeline (S2).
// No backend yet — in S6 these arrays get replaced by live calls to Keya's data service.
// Keep the SHAPES close to the real schemas so the swap is painless:
//   - approvals  ~ /approvals?status=pending  (proposal + plain message)
//   - handled    ~ ActionResults that were routed "autonomous"
//   - timeline   ~ /ledger?person_id=...      (ledger_events, newest first)

export const PERSON_NAME = "Margaret";

// "Needs your decision" — high-stakes things Lighthouse will NOT do without family approval.
export const pendingApprovals = [
  {
    id: "apr_1001",
    message:
      'A scam email asked Margaret to pay $200 to "unlock her bank account." Should I pay it?',
    detail:
      'The email claims to be from "SecureBank Support" but was sent from billing-alert@secure-bank-help.com. Real banks never ask for payment to unlock an account.',
    amount: "$200.00",
    receivedAt: "2026-06-20T09:14:00",
  },
  {
    id: "apr_1002",
    message:
      "An email is asking to reset the password on Margaret's email account. Should I allow it?",
    detail:
      "A password-reset request came from a device we've never seen before, in a different state. This could lock Margaret out of her own email.",
    amount: null,
    receivedAt: "2026-06-20T08:02:00",
  },
];

// "What I've handled" — safe, reversible actions Lighthouse did on its own.
export const handledActions = [
  {
    id: "act_2001",
    title: "Quarantined a scam email",
    summary:
      'Moved a fake "Your package is held" delivery scam out of Margaret\'s inbox.',
    handledAt: "2026-06-20T07:48:00",
    reversible: true,
  },
  {
    id: "act_2002",
    title: "Blocked a repeat scam sender",
    summary:
      "Blocked prizes@lucky-winner-rewards.net after it sent 3 lottery scams this week.",
    handledAt: "2026-06-19T18:30:00",
    reversible: true,
  },
  {
    id: "act_2003",
    title: "Flagged an unusual charge",
    summary:
      'Labeled a $4.99 "free trial" charge from an unknown service and notified you.',
    handledAt: "2026-06-19T13:05:00",
    reversible: true,
  },
];

// Protected-person screen (S3) — gentle, warm content for Margaret herself.
// Deliberately NO scam details and NO controls here; just reassurance.
// In S6 these could come from a "family messages" feed; the shapes stay simple.
export const familyNote = {
  from: "Priya",
  relation: "your daughter",
  message: "Thinking of you today. I'll call after lunch. Love you. 💙",
};

export const dayReminder = "A little walk this afternoon would be lovely.";

// History timeline (S2) — the full story Lighthouse can show a worried family member.
// Newest first. `type` drives the icon; keep types stable so the icon map stays in sync.
export const timelineEvents = [
  {
    id: "evt_3001",
    type: "approval_requested",
    title: "Asked family for a decision",
    detail: 'Pay $200 to "unlock bank account"? Waiting for your answer.',
    at: "2026-06-20T09:14:20",
  },
  {
    id: "evt_3002",
    type: "scam_detected",
    title: "Flagged an email as a scam",
    detail: 'Fake "SecureBank" payment demand. Sender address did not match.',
    at: "2026-06-20T09:14:05",
  },
  {
    id: "evt_3003",
    type: "email_received",
    title: "New email arrived",
    detail: 'Subject: "URGENT: Your account is locked"',
    at: "2026-06-20T09:14:00",
  },
  {
    id: "evt_3004",
    type: "family_notified",
    title: "Notified the family",
    detail: "Sent Priya a summary of this morning's quarantined scam.",
    at: "2026-06-20T07:48:30",
  },
  {
    id: "evt_3005",
    type: "email_quarantined",
    title: "Quarantined the email",
    detail: 'Moved "Your package is held" delivery scam to Quarantine.',
    at: "2026-06-20T07:48:10",
  },
  {
    id: "evt_3006",
    type: "scam_detected",
    title: "Flagged an email as a scam",
    detail: "Delivery scam with a fake tracking link.",
    at: "2026-06-20T07:48:05",
  },
  {
    id: "evt_3007",
    type: "email_received",
    title: "New email arrived",
    detail: 'Subject: "Your package #4471 is held. Pay redelivery fee."',
    at: "2026-06-20T07:48:00",
  },
];
