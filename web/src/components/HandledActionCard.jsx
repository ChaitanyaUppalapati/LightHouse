import { formatRelative } from "../lib/formatTime.js";

// One safe, reversible action Lighthouse took on its own. Rendered as a row inside the
// shared "What I've handled" card. `first` controls the divider; `exiting` eases it out on Undo.
export default function HandledActionCard({ action, onUndo, first, exiting }) {
  const canUndo = action.reversible && typeof onUndo === "function";

  return (
    <div
      className="lh-row"
      style={{
        display: "flex",
        gap: 14,
        alignItems: "flex-start",
        padding: "17px 20px",
        borderTop: first ? "none" : "1px solid #EFE7D8",
        transition: "opacity .4s ease, transform .4s ease",
        opacity: exiting ? 0 : 1,
        transform: exiting ? "translateX(-16px)" : "none",
      }}
    >
      <span
        style={{
          width: 30,
          height: 30,
          flex: "none",
          borderRadius: "50%",
          background: "rgba(94,139,115,.16)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginTop: 2,
        }}
      >
        <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#5E8B73" }} />
      </span>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: "#1B2A41" }}>{action.title}</div>
        <div style={{ fontSize: 15, color: "#566570", lineHeight: 1.5, marginTop: 3, textWrap: "pretty" }}>
          {action.summary}
        </div>
        <div style={{ fontSize: 13.5, color: "#9a8f7c", marginTop: 6 }}>
          {formatRelative(action.handledAt)}
        </div>
      </div>

      {canUndo && (
        <button
          type="button"
          onClick={() => onUndo(action.id)}
          className="lh-undo"
          style={{
            fontFamily: "inherit",
            fontSize: 14.5,
            fontWeight: 600,
            color: "#235E6F",
            background: "transparent",
            border: "none",
            cursor: "pointer",
            padding: "6px 8px",
            flex: "none",
            alignSelf: "center",
          }}
        >
          Undo
        </button>
      )}
    </div>
  );
}
