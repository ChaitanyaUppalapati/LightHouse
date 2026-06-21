import { formatRelative, formatClock } from "../lib/formatTime.js";

// Dot color per ledger event type. Unknown types fall back to a calm slate-blue,
// so a new event_type from the backend (S6) never breaks the screen.
const DOT_COLORS = {
  approval_requested: "#E7A33E",
  scam_detected: "#C9603F",
  email_received: "#235E6F",
  family_notified: "#5E8B73",
  email_quarantined: "#6E8694",
};

export default function Timeline({ events }) {
  if (!events?.length) {
    return (
      <p style={{ fontSize: 16.5, color: "#8a7f6e", padding: "20px 4px" }}>
        Nothing yet. Lighthouse will record everything it does here.
      </p>
    );
  }

  return (
    <div>
      {events.map((event, i) => {
        const color = DOT_COLORS[event.type] || "#6E8694";
        const first = i === 0;
        const last = i === events.length - 1;
        return (
          <div key={event.id} style={{ display: "flex", gap: 16, position: "relative", paddingBottom: 24 }}>
            {/* rail + dot */}
            <div style={{ position: "relative", width: 22, flex: "none" }}>
              {!last && (
                <div
                  style={{
                    position: "absolute",
                    left: 9,
                    top: first ? 14 : 0,
                    bottom: -24,
                    width: 2,
                    background: "#E7DECF",
                  }}
                />
              )}
              <div
                style={{
                  position: "absolute",
                  left: 1,
                  top: 4,
                  width: 18,
                  height: 18,
                  borderRadius: "50%",
                  background: color,
                  border: "3px solid #FAF6EF",
                  boxShadow: first ? "0 0 0 4px rgba(231,163,62,.22)" : "none",
                }}
              />
            </div>

            {/* content — the newest event is gently highlighted */}
            <div
              style={
                first
                  ? {
                      flex: 1,
                      minWidth: 0,
                      background: "rgba(231,163,62,.09)",
                      border: "1px solid rgba(231,163,62,.22)",
                      borderRadius: 12,
                      padding: "12px 16px",
                      marginTop: -4,
                    }
                  : { flex: 1, minWidth: 0, paddingTop: 1 }
              }
            >
              <div style={{ fontSize: 15.5, fontWeight: 600, color: "#1B2A41" }}>{event.title}</div>
              {event.detail && (
                <div style={{ fontSize: 15, color: "#566570", lineHeight: 1.5, marginTop: 2, textWrap: "pretty" }}>
                  {event.detail}
                </div>
              )}
              <time
                dateTime={event.at}
                title={formatClock(event.at)}
                style={{ display: "block", fontSize: 13, color: "#9a8f7c", marginTop: 6 }}
              >
                {formatRelative(event.at)}
              </time>
            </div>
          </div>
        );
      })}
    </div>
  );
}
