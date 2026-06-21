import { useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header.jsx";
import StatusStrip from "../components/StatusStrip.jsx";
import ApprovalCard from "../components/ApprovalCard.jsx";
import HandledActionCard from "../components/HandledActionCard.jsx";
import Timeline from "../components/Timeline.jsx";
import { CheckIcon, XIcon } from "../components/Icons.jsx";
import {
  pendingApprovals,
  handledActions as initialHandled,
  timelineEvents,
  PERSON_NAME,
} from "../data/fakeData.js";

function SectionHeading({ children, count }) {
  return (
    <div className="mb-4 flex items-baseline gap-3">
      <h2 className="text-2xl font-bold text-slate-900">{children}</h2>
      {typeof count === "number" && (
        <span className="rounded-full bg-slate-200 px-3 py-0.5 text-base font-semibold text-slate-700">
          {count}
        </span>
      )}
    </div>
  );
}

export default function Dashboard() {
  // Local state for now (fake data). In S6 this becomes live data from Keya's backend.
  const [approvals, setApprovals] = useState(pendingApprovals);
  const [handled, setHandled] = useState(initialHandled);
  // A single confirmation banner. tone drives the color; text is plain English.
  const [notice, setNotice] = useState(null);

  function handleDecide(id, decision) {
    const approval = approvals.find((a) => a.id === id);
    setApprovals((prev) => prev.filter((a) => a.id !== id));
    setNotice({
      tone: decision, // "approved" | "denied"
      text: `${decision === "approved" ? "Approved" : "Denied"}. Thanks — Lighthouse has noted your decision.`,
    });
  }

  function handleUndo(id) {
    const action = handled.find((a) => a.id === id);
    setHandled((prev) => prev.filter((a) => a.id !== id));
    setNotice({
      tone: "undo",
      text: `Undone${action ? `: ${action.title.toLowerCase()}` : ""}. Lighthouse has reversed it.`,
    });
  }

  const noticeStyles = {
    approved: { className: "bg-green-100 text-green-900", Icon: CheckIcon },
    denied: { className: "bg-red-100 text-red-900", Icon: XIcon },
    undo: { className: "bg-blue-100 text-blue-900", Icon: CheckIcon },
  };
  const activeNotice = notice ? noticeStyles[notice.tone] : null;

  return (
    <div className="min-h-screen bg-slate-100">
      <Header />

      <main className="mx-auto max-w-4xl px-6 py-8">
        <StatusStrip needsYou={approvals.length} handledCount={handled.length} />

        {/* Confirmation banner after a decision — reassures the family the tap registered. */}
        {activeNotice && (
          <div
            role="status"
            className={`mb-6 flex items-start gap-3 rounded-xl p-4 text-lg ${activeNotice.className}`}
          >
            <activeNotice.Icon className="mt-0.5 h-6 w-6 shrink-0" />
            <span>{notice.text}</span>
          </div>
        )}

        {/* Needs your decision */}
        <section className="mb-10">
          <SectionHeading count={approvals.length}>
            Needs your decision
          </SectionHeading>
          {approvals.length === 0 ? (
            <p className="rounded-xl border border-slate-200 bg-white p-6 text-lg text-slate-600">
              All caught up. Nothing needs your attention right now. 💙
            </p>
          ) : (
            <div className="space-y-4">
              {approvals.map((approval, i) => (
                <div
                  key={approval.id}
                  className="animate-fade-up"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <ApprovalCard approval={approval} onDecide={handleDecide} />
                </div>
              ))}
            </div>
          )}
        </section>

        {/* What I've handled */}
        <section className="mb-10">
          <SectionHeading>What I&apos;ve handled</SectionHeading>
          <p className="-mt-2 mb-4 text-lg text-slate-600">
            Safe things Lighthouse took care of for {PERSON_NAME} on its own.
          </p>
          {handled.length === 0 ? (
            <p className="rounded-xl border border-slate-200 bg-white p-6 text-lg text-slate-600">
              Nothing handled yet.
            </p>
          ) : (
            <div className="space-y-3">
              {handled.map((action, i) => (
                <div
                  key={action.id}
                  className="animate-fade-up"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <HandledActionCard action={action} onUndo={handleUndo} />
                </div>
              ))}
            </div>
          )}
        </section>

        {/* History (S2) */}
        <section>
          <SectionHeading>History</SectionHeading>
          <p className="-mt-2 mb-5 text-lg text-slate-600">
            Everything Lighthouse has done, newest first.
          </p>
          <Timeline events={timelineEvents} />
        </section>
      </main>

      <footer className="mx-auto flex max-w-4xl flex-col items-center gap-3 px-6 py-8 text-center text-base text-slate-500">
        <Link
          to="/me"
          className="font-semibold text-blue-700 underline-offset-2 hover:underline"
        >
          View {PERSON_NAME}&apos;s screen →
        </Link>
        <span>Smart enough to act, safe enough to ask.</span>
      </footer>
    </div>
  );
}
