import { ShieldIcon } from "./Icons.jsx";
import { formatRelative } from "../lib/formatTime.js";

// A safe, reversible action Lighthouse already took on its own. Reassuring, low-key.
// If the action is reversible and an onUndo handler is given, show a quiet Undo button.
export default function HandledActionCard({ action, onUndo }) {
  const canUndo = action.reversible && typeof onUndo === "function";

  return (
    <article className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-green-100">
        <ShieldIcon className="h-6 w-6 text-green-700" title="Handled safely" />
      </div>
      <div className="flex-1">
        <p className="text-lg font-semibold text-slate-900">{action.title}</p>
        <p className="mt-1 text-lg leading-relaxed text-slate-600">
          {action.summary}
        </p>
        <p className="mt-1 text-base text-slate-500">
          {formatRelative(action.handledAt)}
          {action.reversible ? " · Can be undone" : ""}
        </p>
      </div>
      {canUndo && (
        <button
          type="button"
          onClick={() => onUndo(action.id)}
          className="shrink-0 self-center rounded-lg border border-slate-300 px-4 py-2 text-base font-semibold text-slate-700 transition hover:bg-slate-100 active:bg-slate-200"
        >
          Undo
        </button>
      )}
    </article>
  );
}
