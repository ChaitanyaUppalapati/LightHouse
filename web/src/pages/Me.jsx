import { useState, useRef } from "react";
import { greeting, formatFriendlyDate } from "../lib/formatTime.js";
import { PERSON_NAME, familyNote, dayReminder } from "../data/fakeData.js";
import { answerFor, speak, startListening, logVoiceQuestion, speechSupported } from "../lib/voice.js";

// S8 — a calm voice helper for Margaret. Tap the mic (or type), ask a question, and
// Lighthouse answers out loud with reassurance. A HELP feature only — it can never
// change or disable protection.
function AskLighthouse() {
  const [status, setStatus] = useState("idle"); // idle | listening | answer
  const [asked, setAsked] = useState("");
  const [answer, setAnswer] = useState("");
  const [typing, setTyping] = useState(!speechSupported); // no mic -> typed question
  const [draft, setDraft] = useState("");
  const stopRef = useRef(null);

  function respond(question) {
    const q = (question || "").trim();
    if (!q) return;
    const a = answerFor(q);
    setAsked(q);
    setAnswer(a);
    setStatus("answer");
    setDraft("");
    speak(a);
    logVoiceQuestion(q);
  }

  function onMic() {
    if (status === "listening") {
      stopRef.current && stopRef.current();
      setStatus("idle");
      return;
    }
    setStatus("listening");
    stopRef.current = startListening({
      onResult: (t) => respond(t),
      onError: () => {
        setStatus("idle");
        setTyping(true); // gracefully offer the typed path
      },
      onEnd: () => setStatus((s) => (s === "listening" ? "idle" : s)),
    });
  }

  const card = {
    background: "#FFFDF8",
    border: "1px solid #E7DECF",
    borderRadius: 20,
    padding: "28px 30px",
    boxShadow: "0 12px 34px -22px rgba(27,42,65,.4)",
    marginTop: 28,
    textAlign: "center",
  };

  return (
    <div className="lh-rise" style={{ ...card, animationDelay: ".36s" }}>
      <div style={{ fontSize: 15, fontWeight: 600, letterSpacing: ".4px", textTransform: "uppercase", color: "#9a8f7c", marginBottom: 18 }}>
        Ask Lighthouse
      </div>

      {speechSupported && (
        <>
          <button
            type="button"
            onClick={onMic}
            aria-label={status === "listening" ? "Stop listening" : "Ask Lighthouse a question"}
            className="lh-approve"
            style={{
              width: 96,
              height: 96,
              borderRadius: "50%",
              cursor: "pointer",
              border: "none",
              background: status === "listening" ? "#C9603F" : "#235E6F",
              color: "#fff",
              boxShadow: "0 10px 26px -12px rgba(35,94,111,.8)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {/* simple mic glyph */}
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="9" y="2" width="6" height="12" rx="3" />
              <path d="M5 11a7 7 0 0 0 14 0" />
              <line x1="12" y1="18" x2="12" y2="22" />
            </svg>
          </button>
          <p style={{ fontSize: 17, color: "#566570", margin: "16px 0 0" }}>
            {status === "listening" ? "Listening… tap when you're done." : "Tap and ask me anything."}
          </p>
          {!typing && (
            <button type="button" onClick={() => setTyping(true)} className="lh-undo" style={{ marginTop: 12, fontFamily: "inherit", fontSize: 14.5, fontWeight: 600, color: "#235E6F", background: "transparent", border: "none", cursor: "pointer" }}>
              or type a question
            </button>
          )}
        </>
      )}

      {typing && (
        <form
          onSubmit={(e) => { e.preventDefault(); respond(draft); }}
          style={{ display: "flex", gap: 10, marginTop: speechSupported ? 16 : 0, maxWidth: 440, marginInline: "auto" }}
        >
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            data-testid="voice-question-input"
            aria-label="Type a question for Lighthouse"
            placeholder="Type a question…"
            style={{ flex: 1, boxSizing: "border-box", fontFamily: "inherit", fontSize: 16, padding: "12px 14px", borderRadius: 12, border: "1px solid #E7DECF", background: "#fff", color: "#1B2A41", outline: "none" }}
          />
          <button type="submit" data-testid="voice-ask" className="lh-approve" style={{ fontFamily: "inherit", fontSize: 15.5, fontWeight: 600, padding: "12px 20px", borderRadius: 12, cursor: "pointer", background: "#235E6F", color: "#fff", border: "1.5px solid #235E6F" }}>
            Ask
          </button>
        </form>
      )}

      {status === "answer" && (
        <div className="lh-fade" style={{ marginTop: 22, textAlign: "left" }}>
          <p style={{ fontSize: 15, color: "#9a8f7c", margin: "0 0 6px" }}>You asked: “{asked}”</p>
          <p className="lh-serif" data-testid="voice-answer" style={{ fontSize: 21, lineHeight: 1.5, color: "#1B2A41", margin: 0, textWrap: "pretty" }}>
            {answer}
          </p>
        </div>
      )}
    </div>
  );
}

// S3 — Margaret's own screen. Calm and reassuring: dawn sky, huge serif greeting, a
// soft "You're protected" status, a family note, one gentle reminder, and (S8) a voice
// helper. HARD RULE: no scam details, no settings, NO off-switch. Only family can change
// protection, and only from the dashboard. Nothing here is a control.
export default function Me() {
  const now = new Date();

  return (
    <div className="lh-fade" style={{ position: "relative", minHeight: "100vh" }}>
      {/* dawn sky */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "60vh", background: "linear-gradient(180deg,#FBE3C0 0%,#FBEEDA 46%,#FAF6EF 96%)", zIndex: 0 }} />
      <div style={{ position: "absolute", top: -40, left: "50%", transform: "translateX(-50%)", width: 640, height: 420, background: "radial-gradient(ellipse at center top, rgba(231,163,62,.4), rgba(231,163,62,0) 62%)", zIndex: 0, animation: "lh-glow 8s ease-in-out infinite" }} />

      <div style={{ position: "relative", zIndex: 1, maxWidth: 620, margin: "0 auto", padding: "84px 26px 80px" }}>
        {/* date */}
        <div className="lh-rise" style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 36 }}>
          <span style={{ position: "relative", width: 11, height: 11, display: "inline-block" }}>
            <span style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "#E7A33E", animation: "lh-pulse 4s ease-in-out infinite" }} />
            <span style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "#E7A33E" }} />
          </span>
          <span style={{ fontSize: 16, fontWeight: 600, color: "#9a7b3e", letterSpacing: ".3px" }}>{formatFriendlyDate(now)}</span>
        </div>

        <h1 className="lh-serif lh-rise" style={{ fontWeight: 500, fontSize: 46, lineHeight: 1.12, letterSpacing: "-.6px", margin: "0 0 24px", color: "#1B2A41", textWrap: "balance", animationDelay: ".05s" }}>
          {greeting(now)}, {PERSON_NAME}.
        </h1>

        <p className="lh-serif lh-rise" style={{ fontWeight: 400, fontSize: 25, lineHeight: 1.5, margin: "0 0 40px", color: "#3a4a55", textWrap: "pretty", animationDelay: ".12s" }}>
          Everything&apos;s okay. Lighthouse is looking out for you.
        </p>

        {/* protected — reassurance, never a toggle */}
        <div className="lh-rise" style={{ display: "inline-flex", alignItems: "center", gap: 12, padding: "14px 22px", borderRadius: 999, background: "rgba(94,139,115,.14)", border: "1px solid rgba(94,139,115,.3)", marginBottom: 44, animationDelay: ".18s" }}>
          <span style={{ position: "relative", width: 12, height: 12, display: "inline-block" }}>
            <span style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "#5E8B73", animation: "lh-pulse 3.4s ease-in-out infinite" }} />
            <span style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "#5E8B73" }} />
          </span>
          <span style={{ fontSize: 19, fontWeight: 600, color: "#3f6450" }}>You&apos;re protected</span>
          <span style={{ fontSize: 16, color: "#6f8a7b" }}>always</span>
        </div>

        {/* a note from family */}
        <div className="lh-rise" style={{ background: "#FFFDF8", border: "1px solid #E7DECF", borderRadius: 20, padding: "28px 30px", boxShadow: "0 12px 34px -22px rgba(27,42,65,.4)", marginBottom: 28, animationDelay: ".24s" }}>
          <div style={{ fontSize: 15, fontWeight: 600, letterSpacing: ".4px", textTransform: "uppercase", color: "#9a8f7c", marginBottom: 14 }}>
            A note from {familyNote.from}, {familyNote.relation}
          </div>
          <p className="lh-serif" style={{ fontWeight: 400, fontSize: 23, lineHeight: 1.5, margin: 0, color: "#1B2A41", textWrap: "pretty" }}>
            {familyNote.message}
          </p>
        </div>

        {/* gentle reminder */}
        <div className="lh-rise" style={{ display: "flex", alignItems: "center", gap: 16, padding: "22px 26px", borderRadius: 18, background: "rgba(231,163,62,.1)", border: "1px solid rgba(231,163,62,.28)", animationDelay: ".3s" }}>
          <span style={{ width: 14, height: 14, borderRadius: "50%", flex: "none", background: "#E7A33E", boxShadow: "0 0 14px 2px rgba(231,163,62,.55)" }} />
          <p style={{ margin: 0, fontSize: 19, lineHeight: 1.5, color: "#5a4a2e" }}>{dayReminder}</p>
        </div>

        {/* S8 — voice helper */}
        <AskLighthouse />
      </div>
    </div>
  );
}
