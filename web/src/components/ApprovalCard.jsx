import { CheckIcon, XIcon, WarningIcon } from "./Icons.jsx";
import { formatRelative } from "../lib/formatTime.js";

// One pending decision. The message is plain English; the two buttons are huge,
// color-coded, and carry BOTH an icon and a word (never rely on color alone).
export default function ApprovalCard({ approval, onDecide }) {
  return (
    <article className="rounded-2xl border-2 border-amber-300 bg-white p-6 shadow-sm">
      <div className="flex items-start gap-3">
        <WarningIcon className="mt-1 h-7 w-7 shrink-0 text-amber-500" title="Needs attention" />
        <div className="flex-1">
          <p className="text-xl font-semibold leading-snug text-slate-900">
            {approval.message}
          </p>
          {approval.detail && (
            <p className="mt-2 text-lg leading-relaxed text-slate-600">
              {approval.detail}
            </p>
          )}
          <p className="mt-2 text-base text-slate-500">
            Arrived {formatRelative(approval.receivedAt)}
            {approval.amount ? ` · Amount: ${approval.amount}` : ""}
          </p>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={() => onDecide(approval.id, "approved")}
          className="flex flex-1 items-center justify-center gap-3 rounded-xl bg-green-600 px-6 py-4 text-xl font-bold text-white transition hover:bg-green-700 active:bg-green-800"
        >
          <CheckIcon className="h-7 w-7" />
          Approve
        </button>
        <button
          type="button"
          onClick={() => onDecide(approval.id, "denied")}
          className="flex flex-1 items-center justify-center gap-3 rounded-xl bg-red-600 px-6 py-4 text-xl font-bold text-white transition hover:bg-red-700 active:bg-red-800"
        >
          <XIcon className="h-7 w-7" />
          Deny
        </button>
      </div>
    </article>
  );
}
