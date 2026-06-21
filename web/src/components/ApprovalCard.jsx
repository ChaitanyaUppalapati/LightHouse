import { formatRelative, formatClock } from "../lib/formatTime.js";

const cardBase = {
  background: "#FFFDF8",
  border: "1px solid #E7DECF",
  borderRadius: 16,
  padding: "22px 22px 20px",
  boxShadow: "0 6px 22px -14px rgba(27,42,65,.28)",
  transition: "opacity .45s ease, transform .45s ease",
};

// One pending decision. Plain question in warm serif, a short why, and two calm
// actions: Approve (sage, filled) and Deny (terracotta, outline). `exitDir` eases
// the card out after a decision so the change feels gentle, not abrupt.
export default function ApprovalCard({ approval, onDecide, exitDir }) {
  const time = new Date(approval.receivedAt).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  const style = exitDir
    ? {
        ...cardBase,
        opacity: 0,
        transform:
          exitDir === "approved"
            ? "translateX(22px) scale(.99)"
            : "translateX(-22px) scale(.99)",
      }
    : cardBase;

  return (
    <article className={exitDir ? "" : "lh-card"} style={style}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 12,
        }}
      >
        <span style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: "1.4px", color: "#C9603F" }}>
          NEEDS YOU
        </span>
        {approval.amount && (
          <span
            className="lh-serif"
            style={{
              fontWeight: 600,
              fontSize: 17,
              color: "#1B2A41",
              padding: "4px 12px",
              borderRadius: 8,
              background: "rgba(231,163,62,.16)",
            }}
          >
            {approval.amount}
          </span>
        )}
      </div>

      <p
        className="lh-serif"
        style={{
          fontWeight: 500,
          fontSize: 21,
          lineHeight: 1.34,
          margin: "0 0 10px",
          color: "#1B2A41",
          textWrap: "pretty",
        }}
      >
        {approval.message}
      </p>
      {approval.detail && (
        <p style={{ fontSize: 16.5, lineHeight: 1.55, margin: "0 0 18px", color: "#566570", textWrap: "pretty" }}>
          {approval.detail}
        </p>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 14,
        }}
      >
        <span style={{ fontSize: 14, color: "#8a7f6e" }} title={formatClock(approval.receivedAt)}>
          {time} · {formatRelative(approval.receivedAt)}
        </span>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            onClick={() => onDecide(approval.id, "denied")}
            className="lh-deny"
            style={{
              fontFamily: "inherit",
              fontSize: 16,
              fontWeight: 600,
              padding: "12px 22px",
              borderRadius: 12,
              cursor: "pointer",
              background: "transparent",
              color: "#C9603F",
              border: "1.5px solid rgba(201,96,63,.55)",
            }}
          >
            Deny
          </button>
          <button
            type="button"
            onClick={() => onDecide(approval.id, "approved")}
            className="lh-approve"
            style={{
              fontFamily: "inherit",
              fontSize: 16,
              fontWeight: 600,
              padding: "12px 26px",
              borderRadius: 12,
              cursor: "pointer",
              background: "#5E8B73",
              color: "#fff",
              border: "1.5px solid #5E8B73",
              boxShadow: "0 6px 16px -8px rgba(94,139,115,.7)",
            }}
          >
            Approve
          </button>
        </div>
      </div>
    </article>
  );
}
