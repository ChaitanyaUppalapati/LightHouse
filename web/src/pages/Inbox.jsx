import { useState } from "react";
import { INBOX_EMAILS } from "../data/inboxData.js";

// S4 — a real-looking inbox. A browser agent (Browserbase + Stagehand) operates THIS page:
// it clicks the flagged scam email, then clicks the clearly-labeled "Move to Quarantine"
// button, and the email actually moves to the Quarantine folder. Buttons carry plain text,
// aria-labels, and data-testids so an automated agent can find them reliably.
export default function Inbox() {
  const [emails, setEmails] = useState(INBOX_EMAILS);
  const [folder, setFolder] = useState("inbox");
  const [openId, setOpenId] = useState(null);

  const inboxCount = emails.filter((e) => e.folder === "inbox").length;
  const quarantineCount = emails.filter((e) => e.folder === "quarantine").length;
  const visible = emails.filter((e) => e.folder === folder);

  function move(id, to) {
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, folder: to } : e)));
    setOpenId(null);
  }

  const folderBtn = (key, label, count) => {
    const active = folder === key;
    return (
      <button
        type="button"
        onClick={() => { setFolder(key); setOpenId(null); }}
        aria-label={`${label} folder`}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8,
          width: "100%", textAlign: "left", fontFamily: "inherit", fontSize: 15.5,
          fontWeight: 600, cursor: "pointer", padding: "11px 14px", borderRadius: 12,
          border: "none", marginBottom: 4,
          background: active ? "rgba(35,94,111,.12)" : "transparent",
          color: active ? "#1B2A41" : "#566570",
        }}
      >
        <span>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 700, color: active ? "#235E6F" : "#9a8f7c" }}>{count}</span>
      </button>
    );
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexWrap: "wrap" }}>
      {/* sidebar */}
      <aside
        style={{
          width: 240, flex: "1 1 220px", maxWidth: 280, boxSizing: "border-box",
          padding: "26px 18px", borderRight: "1px solid #E7DECF", background: "#FFFDF8",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 26, padding: "0 6px" }}>
          <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#E7A33E", boxShadow: "0 0 10px 2px rgba(231,163,62,.55)", flex: "none" }} />
          <div>
            <div className="lh-serif" style={{ fontWeight: 600, fontSize: 18, color: "#1B2A41", lineHeight: 1 }}>Mailbox</div>
            <div style={{ fontSize: 13, color: "#9a8f7c", marginTop: 3 }}>Margaret&apos;s inbox</div>
          </div>
        </div>
        {folderBtn("inbox", "Inbox", inboxCount)}
        {folderBtn("quarantine", "Quarantine", quarantineCount)}
      </aside>

      {/* message list */}
      <main style={{ flex: "999 1 420px", minWidth: 0, padding: "26px 22px 60px", maxWidth: 760, margin: "0 auto" }}>
        <h1 className="lh-serif" style={{ fontWeight: 600, fontSize: 26, margin: "0 0 4px", color: "#1B2A41" }}>
          {folder === "inbox" ? "Inbox" : "Quarantine"}
        </h1>
        <p style={{ fontSize: 14.5, color: "#8a7f6e", margin: "0 0 20px" }}>
          {folder === "inbox"
            ? `${inboxCount} ${inboxCount === 1 ? "message" : "messages"}`
            : "Suspicious messages Lighthouse moved out of the way."}
        </p>

        {visible.length === 0 ? (
          <p style={{ fontSize: 16.5, color: "#8a7f6e", padding: "24px 4px" }}>
            {folder === "inbox" ? "No messages." : "Nothing in Quarantine."}
          </p>
        ) : (
          <div
            style={{
              background: "#FFFDF8", border: "1px solid #E7DECF", borderRadius: 16,
              boxShadow: "0 6px 22px -16px rgba(27,42,65,.22)", overflow: "hidden",
            }}
          >
            {visible.map((mail, i) => {
              const open = openId === mail.id;
              return (
                <div key={mail.id} style={{ borderTop: i > 0 ? "1px solid #EFE7D8" : "none" }}>
                  <button
                    type="button"
                    onClick={() => setOpenId(open ? null : mail.id)}
                    aria-label={`Email from ${mail.sender}: ${mail.subject}`}
                    aria-expanded={open}
                    className="lh-row"
                    style={{
                      display: "flex", alignItems: "flex-start", gap: 14, width: "100%",
                      textAlign: "left", fontFamily: "inherit", cursor: "pointer",
                      border: "none", background: open ? "#FBF7EF" : "transparent",
                      padding: "16px 20px",
                    }}
                  >
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ display: "flex", alignItems: "center", gap: 9 }}>
                        <span style={{ fontSize: 15.5, fontWeight: 700, color: "#1B2A41" }}>{mail.sender}</span>
                        {mail.scam && (
                          <span style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: ".6px", color: "#C9603F", background: "rgba(201,96,63,.12)", padding: "2px 7px", borderRadius: 999 }}>
                            SUSPICIOUS
                          </span>
                        )}
                      </span>
                      <span style={{ display: "block", fontSize: 15, fontWeight: 600, color: "#384550", marginTop: 4 }}>{mail.subject}</span>
                      <span style={{ display: "block", fontSize: 14, color: "#8a7f6e", marginTop: 3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{mail.preview}</span>
                    </span>
                    <span style={{ fontSize: 13, color: "#9a8f7c", flex: "none", paddingTop: 2 }}>{mail.time}</span>
                  </button>

                  {open && (
                    <div style={{ padding: "0 20px 20px", borderTop: "1px solid #EFE7D8" }}>
                      <div style={{ fontSize: 13.5, color: "#9a8f7c", margin: "14px 0 12px" }}>
                        From {mail.sender} &lt;{mail.email}&gt;
                      </div>
                      <p style={{ fontSize: 16, lineHeight: 1.6, color: "#384550", margin: "0 0 18px", textWrap: "pretty" }}>{mail.body}</p>
                      {folder === "inbox" ? (
                        <button
                          type="button"
                          data-testid="move-to-quarantine"
                          aria-label={`Move email "${mail.subject}" to Quarantine`}
                          onClick={() => move(mail.id, "quarantine")}
                          className="lh-approve"
                          style={{
                            fontFamily: "inherit", fontSize: 15.5, fontWeight: 600,
                            padding: "12px 22px", borderRadius: 12, cursor: "pointer",
                            background: "#C9603F", color: "#fff", border: "1.5px solid #C9603F",
                            boxShadow: "0 6px 16px -8px rgba(201,96,63,.7)",
                          }}
                        >
                          Move to Quarantine
                        </button>
                      ) : (
                        <button
                          type="button"
                          data-testid="move-to-inbox"
                          aria-label={`Move email "${mail.subject}" back to Inbox`}
                          onClick={() => move(mail.id, "inbox")}
                          className="lh-deny"
                          style={{
                            fontFamily: "inherit", fontSize: 15.5, fontWeight: 600,
                            padding: "12px 22px", borderRadius: 12, cursor: "pointer",
                            background: "transparent", color: "#235E6F", border: "1.5px solid rgba(35,94,111,.5)",
                          }}
                        >
                          Move back to Inbox
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
