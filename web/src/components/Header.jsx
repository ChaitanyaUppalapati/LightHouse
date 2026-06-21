import { PERSON_NAME } from "../data/fakeData.js";

// A small CSS lighthouse: a teal tower with a glowing amber light and a slow sweeping beam.
function LighthouseMark() {
  return (
    <div
      style={{
        position: "relative",
        width: 56,
        height: 56,
        flex: "none",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* sweeping beam */}
      <div
        style={{
          position: "absolute",
          width: 130,
          height: 130,
          borderRadius: "50%",
          background:
            "conic-gradient(from 0deg, rgba(231,163,62,0) 0deg, rgba(231,163,62,0) 304deg, rgba(231,163,62,.5) 342deg, rgba(231,163,62,0) 360deg)",
          filter: "blur(3px)",
          animation: "lh-rotate 14s linear infinite",
        }}
      />
      {/* soft glow */}
      <div
        style={{
          position: "absolute",
          width: 64,
          height: 64,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(231,163,62,.55), rgba(231,163,62,0) 68%)",
          filter: "blur(2px)",
          animation: "lh-glow 5s ease-in-out infinite",
        }}
      />
      {/* tower + light */}
      <div
        style={{
          position: "relative",
          width: 12,
          height: 34,
          borderRadius: "6px 6px 3px 3px",
          background: "linear-gradient(180deg,#2C6E80,#235E6F)",
          marginTop: 14,
          boxShadow: "0 2px 6px rgba(27,42,65,.25)",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: -9,
            left: "50%",
            transform: "translateX(-50%)",
            width: 13,
            height: 13,
            borderRadius: "50%",
            background: "#E7A33E",
            boxShadow: "0 0 14px 3px rgba(231,163,62,.7)",
          }}
        />
      </div>
    </div>
  );
}

export default function Header() {
  return (
    <header
      className="lh-rise"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 16,
        marginBottom: 42,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <LighthouseMark />
        <div>
          <div
            className="lh-serif"
            style={{
              fontWeight: 600,
              fontSize: 27,
              letterSpacing: "-.4px",
              lineHeight: 1,
              color: "#1B2A41",
            }}
          >
            Lighthouse
          </div>
          <div style={{ fontSize: 15.5, color: "#5b6b73", marginTop: 5 }}>
            Watching out for {PERSON_NAME}
          </div>
        </div>
      </div>

      {/* Protected status — reassurance, not a control */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 9,
          padding: "9px 15px",
          borderRadius: 999,
          background: "rgba(94,139,115,.13)",
          border: "1px solid rgba(94,139,115,.28)",
        }}
      >
        <span style={{ position: "relative", width: 9, height: 9, display: "inline-block" }}>
          <span
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "50%",
              background: "#5E8B73",
              animation: "lh-pulse 3s ease-in-out infinite",
            }}
          />
          <span style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "#5E8B73" }} />
        </span>
        <span style={{ fontSize: 14.5, fontWeight: 600, color: "#3f6450" }}>Protected</span>
      </div>
    </header>
  );
}
