import {
  MailIcon,
  WarningIcon,
  FolderIcon,
  BellIcon,
  BlockIcon,
  TagIcon,
  CheckIcon,
  ClockIcon,
} from "./Icons.jsx";
import { formatClock, formatRelative } from "../lib/formatTime.js";

// Each ledger event type maps to an icon + a color. Unknown types fall back to a clock,
// so a new event_type from the backend (S6) never breaks the screen.
const EVENT_STYLES = {
  email_received: { Icon: MailIcon, ring: "bg-slate-100 text-slate-600" },
  scam_detected: { Icon: WarningIcon, ring: "bg-amber-100 text-amber-700" },
  email_quarantined: { Icon: FolderIcon, ring: "bg-blue-100 text-blue-700" },
  sender_blocked: { Icon: BlockIcon, ring: "bg-red-100 text-red-700" },
  transaction_flagged: { Icon: TagIcon, ring: "bg-purple-100 text-purple-700" },
  family_notified: { Icon: BellIcon, ring: "bg-indigo-100 text-indigo-700" },
  approval_requested: { Icon: WarningIcon, ring: "bg-amber-100 text-amber-700" },
  approved: { Icon: CheckIcon, ring: "bg-green-100 text-green-700" },
  denied: { Icon: BlockIcon, ring: "bg-red-100 text-red-700" },
};

const FALLBACK = { Icon: ClockIcon, ring: "bg-slate-100 text-slate-600" };

export default function Timeline({ events }) {
  if (!events?.length) {
    return (
      <p className="rounded-xl border border-slate-200 bg-white p-6 text-lg text-slate-500">
        Nothing yet. Lighthouse will record everything it does here.
      </p>
    );
  }

  return (
    <ol className="relative space-y-5 border-l-2 border-slate-200 pl-6">
      {events.map((event) => {
        const { Icon, ring } = EVENT_STYLES[event.type] ?? FALLBACK;
        return (
          <li key={event.id} className="relative">
            <span
              className={`absolute -left-[2.45rem] flex h-9 w-9 items-center justify-center rounded-full ring-4 ring-slate-50 ${ring}`}
            >
              <Icon className="h-5 w-5" />
            </span>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                <p className="text-lg font-semibold text-slate-900">
                  {event.title}
                </p>
                <time
                  className="text-base text-slate-500"
                  dateTime={event.at}
                  title={formatClock(event.at)}
                >
                  {formatRelative(event.at)}
                </time>
              </div>
              {event.detail && (
                <p className="mt-1 text-lg leading-relaxed text-slate-600">
                  {event.detail}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
