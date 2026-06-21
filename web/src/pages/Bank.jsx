import { useState } from "react";
import { ACCOUNT, TRANSACTIONS, usd } from "../data/bankData.js";

// S5 — a believable online-banking page. Overview (balance + recent activity) ->
// "Make a payment" -> a real payment form -> confirmation. In the demo the family DENIES,
// so the payment is stopped upstream; this page just has to exist and look real. C5's pay
// action opens MOCK_BANK_URL and would fill the form, so inputs and the submit button carry
// labels, aria-labels, and data-testids an automated agent can find.
export default function Bank() {
  const [view, setView] = useState("overview"); // overview | pay | done
  const [form, setForm] = useState({ recipient: "", amount: "", memo: "" });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const submit = (e) => {
    e.preventDefault();
    setView("done");
  };

  const label = { display: "block", fontSize: 13.5, fontWeight: 600, color: "#566570", marginBottom: 7 };
  const input = {
    width: "100%", boxSizing: "border-box", fontFamily: "inherit", fontSize: 16,
    padding: "12px 14px", borderRadius: 12, border: "1px solid #E7DECF",
    background: "#FFFDF8", color: "#1B2A41", outline: "none",
  };

  return (
    <div style={{ minHeight: "100vh", background: "#FAF6EF" }}>
      {/* bank chrome */}
      <header style={{ background: "linear-gradient(180deg,#235E6F,#1d4f5e)", color: "#fff" }}>
        <div style={{ maxWidth: 720, margin: "0 auto", padding: "20px 22px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
            <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#E7A33E", boxShadow: "0 0 10px 2px rgba(231,163,62,.55)", flex: "none" }} />
            <span className="lh-serif" style={{ fontSize: 20, fontWeight: 600, letterSpacing: "-.2px" }}>{ACCOUNT.bankName}</span>
          </div>
          <span style={{ fontSize: 14, color: "rgba(255,255,255,.82)" }}>{ACCOUNT.holder}</span>
        </div>
      </header>

      <main style={{ maxWidth: 720, margin: "0 auto", padding: "28px 22px 64px" }}>
        {view === "overview" && (
          <div className="lh-fade">
            {/* balance card */}
            <div style={{ background: "#FFFDF8", border: "1px solid #E7DECF", borderRadius: 18, padding: "26px 28px", boxShadow: "0 6px 22px -16px rgba(27,42,65,.22)", marginBottom: 24 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600, letterSpacing: ".4px", textTransform: "uppercase", color: "#9a8f7c" }}>
                {ACCOUNT.type} · {ACCOUNT.number}
              </div>
              <div className="lh-serif" style={{ fontSize: 44, fontWeight: 600, color: "#1B2A41", margin: "8px 0 4px", letterSpacing: "-.5px" }}>
                {usd(ACCOUNT.balance)}
              </div>
              <div style={{ fontSize: 14.5, color: "#8a7f6e", marginBottom: 22 }}>Available balance</div>
              <button
                type="button"
                data-testid="make-payment"
                aria-label="Make a payment"
                onClick={() => setView("pay")}
                className="lh-approve"
                style={{ fontFamily: "inherit", fontSize: 16, fontWeight: 600, padding: "13px 26px", borderRadius: 12, cursor: "pointer", background: "#235E6F", color: "#fff", border: "1.5px solid #235E6F", boxShadow: "0 6px 16px -8px rgba(35,94,111,.7)" }}
              >
                Make a payment
              </button>
            </div>

            {/* recent activity */}
            <h2 className="lh-serif" style={{ fontSize: 19, fontWeight: 600, color: "#1B2A41", margin: "0 0 14px" }}>Recent activity</h2>
            <div style={{ background: "#FFFDF8", border: "1px solid #E7DECF", borderRadius: 16, overflow: "hidden" }}>
              {TRANSACTIONS.map((t, i) => (
                <div key={t.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, padding: "15px 20px", borderTop: i > 0 ? "1px solid #EFE7D8" : "none" }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 15.5, fontWeight: 600, color: "#1B2A41" }}>{t.name}</div>
                    <div style={{ fontSize: 13.5, color: "#9a8f7c", marginTop: 2 }}>{t.memo} · {t.date}</div>
                  </div>
                  <div style={{ fontSize: 15.5, fontWeight: 700, flex: "none", color: t.amount < 0 ? "#1B2A41" : "#3f6450" }}>
                    {t.amount < 0 ? "-" : "+"}{usd(Math.abs(t.amount)).replace("$", "$")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {view === "pay" && (
          <form className="lh-fade" onSubmit={submit} style={{ background: "#FFFDF8", border: "1px solid #E7DECF", borderRadius: 18, padding: "26px 28px", boxShadow: "0 6px 22px -16px rgba(27,42,65,.22)", maxWidth: 460 }}>
            <h1 className="lh-serif" style={{ fontSize: 24, fontWeight: 600, color: "#1B2A41", margin: "0 0 6px" }}>Make a payment</h1>
            <p style={{ fontSize: 14.5, color: "#8a7f6e", margin: "0 0 22px" }}>From {ACCOUNT.type} ({ACCOUNT.number})</p>

            <div style={{ marginBottom: 16 }}>
              <label htmlFor="bank-recipient" style={label}>Recipient</label>
              <input id="bank-recipient" data-testid="pay-recipient" aria-label="Recipient" type="text" placeholder="Name or account" value={form.recipient} onChange={set("recipient")} required style={input} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label htmlFor="bank-amount" style={label}>Amount</label>
              <div style={{ position: "relative" }}>
                <span style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "#8a7f6e", fontSize: 16 }}>$</span>
                <input id="bank-amount" data-testid="pay-amount" aria-label="Amount" type="number" min="0" step="0.01" placeholder="0.00" value={form.amount} onChange={set("amount")} required style={{ ...input, paddingLeft: 28 }} />
              </div>
            </div>
            <div style={{ marginBottom: 24 }}>
              <label htmlFor="bank-memo" style={label}>Memo (optional)</label>
              <input id="bank-memo" data-testid="pay-memo" aria-label="Memo" type="text" placeholder="What's this for?" value={form.memo} onChange={set("memo")} style={input} />
            </div>

            <div style={{ display: "flex", gap: 10 }}>
              <button type="button" onClick={() => setView("overview")} className="lh-deny" style={{ fontFamily: "inherit", fontSize: 15.5, fontWeight: 600, padding: "12px 20px", borderRadius: 12, cursor: "pointer", background: "transparent", color: "#566570", border: "1.5px solid #E7DECF" }}>Cancel</button>
              <button type="submit" data-testid="send-payment" aria-label="Send payment" className="lh-approve" style={{ fontFamily: "inherit", fontSize: 15.5, fontWeight: 600, padding: "12px 24px", borderRadius: 12, cursor: "pointer", background: "#235E6F", color: "#fff", border: "1.5px solid #235E6F", boxShadow: "0 6px 16px -8px rgba(35,94,111,.7)" }}>Send payment</button>
            </div>
          </form>
        )}

        {view === "done" && (
          <div className="lh-fade" style={{ background: "#FFFDF8", border: "1px solid #E7DECF", borderRadius: 18, padding: "34px 30px", boxShadow: "0 6px 22px -16px rgba(27,42,65,.22)", maxWidth: 460, textAlign: "center" }}>
            <div style={{ width: 52, height: 52, borderRadius: "50%", background: "rgba(94,139,115,.16)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
              <span style={{ width: 16, height: 16, borderRadius: "50%", background: "#5E8B73" }} />
            </div>
            <h1 className="lh-serif" style={{ fontSize: 23, fontWeight: 600, color: "#1B2A41", margin: "0 0 8px" }}>Payment sent</h1>
            <p style={{ fontSize: 16, color: "#566570", margin: "0 0 22px" }}>
              {form.amount ? usd(Number(form.amount)) : ""} to {form.recipient || "recipient"}.
            </p>
            <button type="button" onClick={() => { setForm({ recipient: "", amount: "", memo: "" }); setView("overview"); }} className="lh-deny" style={{ fontFamily: "inherit", fontSize: 15.5, fontWeight: 600, padding: "11px 22px", borderRadius: 12, cursor: "pointer", background: "transparent", color: "#235E6F", border: "1.5px solid rgba(35,94,111,.5)" }}>Back to account</button>
          </div>
        )}
      </main>
    </div>
  );
}
