import { useState } from "react";
import Header from "../components/Header.jsx";
import ApprovalCard from "../components/ApprovalCard.jsx";
import HandledActionCard from "../components/HandledActionCard.jsx";
import Timeline from "../components/Timeline.jsx";
import {
  pendingApprovals,
  handledActions as initialHandled,
  timelineEvents,
} from "../data/fakeData.js";

// Small colored-dot section heading: terracotta = needs you, sage = handled, amber = history.
function SectionHead({ color, title, right }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 11, marginBottom: 18 }}>
      <span style={{ width: 9, height: 9, borderRadius: "50%", background: color, flex: "none", transform: "translateY(-2px)" }} />
      <h2 className="lh-serif" style={{ fontWeight: 600, fontSize: 24, margin: 0, letterSpacing: "-.3px" }}>
        {title}
      </h2>
      {right && <span style={{ fontSize: 14, color: "#8a7f6e", marginLeft: "auto" }}>{right}</span>}
    </div>
  );
}

let toastSeq = 0;

export default function Dashboard() {
  // Local state for now (fake data). In S6 this becomes live data from Keya's backend.
  const [approvals, setApprovals] = useState(pendingApprovals);
  const [handled, setHandled] = useState(initialHandled);
  const [exiting, setExiting] = useState({}); // approval id -> "approved" | "denied"
  const [exitingHandled, setExitingHandled] = useState({}); // handled id -> true
  const [toasts, setToasts] = useState([]);

  function addToast(text, kind) {
    const id = ++toastSeq;
    const bg =
      kind === "denied"
        ? "rgba(201,96,63,.95)"
        : kind === "undo"
        ? "rgba(35,94,111,.95)"
        : "rgba(94,139,115,.95)";
    setToasts((t) => [...t, { id, text, bg }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000);
  }

  function handleDecide(id, decision) {
    setExiting((e) => ({ ...e, [id]: decision }));
    addToast(
      decision === "approved" ? "Approved. I'll take care of it." : "Denied. I've blocked it.",
      decision
    );
    setTimeout(() => setApprovals((prev) => prev.filter((a) => a.id !== id)), 460);
  }

  function handleUndo(id) {
    setExitingHandled((e) => ({ ...e, [id]: true }));
    addToast("Undone. I restored it for you.", "undo");
    setTimeout(() => setHandled((prev) => prev.filter((a) => a.id !== id)), 420);
  }

  return (
    <div style={{ position: "relative", minHeight: "100vh", overflowX: "hidden" }}>
      {/* toasts — gentle confirmation that a tap registered */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 80,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
          paddingTop: 18,
          pointerEvents: "none",
        }}
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            style={{
              padding: "13px 22px",
              borderRadius: 14,
              background: t.bg,
              color: "#fff",
              fontSize: 15.5,
              fontWeight: 600,
              boxShadow: "0 14px 30px -14px rgba(27,42,65,.5)",
              animation: "lh-toast 3s ease both",
            }}
          >
            {t.text}
          </div>
        ))}
      </div>

      {/* dawn-gradient hero behind the header */}
      <div className="lh-fade" style={{ position: "relative" }}>
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 360,
            background: "linear-gradient(180deg,#FBE7C9 0%,#FBEFD9 38%,#FAF6EF 92%)",
            zIndex: 0,
          }}
        />
        <div
          style={{
            position: "absolute",
            top: -60,
            left: "50%",
            transform: "translateX(-50%)",
            width: 520,
            height: 360,
            background: "radial-gradient(ellipse at center top, rgba(231,163,62,.32), rgba(231,163,62,0) 64%)",
            zIndex: 0,
            animation: "lh-glow 7s ease-in-out infinite",
          }}
        />

        <div style={{ position: "relative", zIndex: 1, maxWidth: 780, margin: "0 auto", padding: "34px 22px 96px" }}>
          <Header />

          {/* Needs your decision */}
          <section className="lh-rise" style={{ marginBottom: 54, animationDelay: ".05s" }}>
            <SectionHead
              color="#C9603F"
              title="Needs your decision"
              right={approvals.length ? `${approvals.length} waiting` : null}
            />
            {approvals.length ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {approvals.map((a) => (
                  <ApprovalCard key={a.id} approval={a} onDecide={handleDecide} exitDir={exiting[a.id]} />
                ))}
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 13,
                  padding: "22px 24px",
                  borderRadius: 16,
                  background: "rgba(94,139,115,.08)",
                  border: "1px dashed rgba(94,139,115,.35)",
                }}
              >
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#5E8B73", flex: "none" }} />
                <p style={{ margin: 0, fontSize: 16.5, color: "#3f6450" }}>
                  All caught up. Nothing needs you right now.
                </p>
              </div>
            )}
          </section>

          {/* What I've handled */}
          <section className="lh-rise" style={{ marginBottom: 54, animationDelay: ".1s" }}>
            <SectionHead color="#5E8B73" title="What I've handled" right="on my own" />
            {handled.length ? (
              <div
                style={{
                  background: "#FFFDF8",
                  border: "1px solid #E7DECF",
                  borderRadius: 18,
                  boxShadow: "0 6px 22px -16px rgba(27,42,65,.22)",
                  overflow: "hidden",
                }}
              >
                {handled.map((h, i) => (
                  <HandledActionCard
                    key={h.id}
                    action={h}
                    onUndo={handleUndo}
                    first={i === 0}
                    exiting={exitingHandled[h.id]}
                  />
                ))}
              </div>
            ) : (
              <p style={{ fontSize: 16.5, color: "#8a7f6e", padding: "4px" }}>Nothing handled yet.</p>
            )}
          </section>

          {/* History */}
          <section className="lh-rise" style={{ animationDelay: ".15s" }}>
            <SectionHead color="#E7A33E" title="History" right="newest first" />
            <Timeline events={timelineEvents} />
          </section>

          <footer style={{ marginTop: 60, textAlign: "center", color: "#9a8f7c", fontSize: 14.5 }}>
            Smart enough to act, safe enough to ask.
          </footer>
        </div>
      </div>
    </div>
  );
}
