import { LighthouseIcon, ShieldIcon } from "../components/Icons.jsx";
import { greeting, formatFriendlyDate } from "../lib/formatTime.js";
import { PERSON_NAME, familyNote, dayReminder } from "../data/fakeData.js";

// S3 — the protected-person screen, for Margaret herself.
// Calm and reassuring on purpose: huge text, lots of space, soft colors.
// HARD RULES: no scam details, no settings, NO off-switch. Only family can change
// protection (on the dashboard). Nothing here is a control — it only reassures.
export default function Me() {
  const now = new Date();

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-b from-sky-50 to-blue-100 px-6 py-16 text-center">
      <div className="w-full max-w-2xl animate-fade-up">
        {/* Soft lighthouse mark — friendly, not an alarm */}
        <div className="mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-white text-blue-700 shadow-sm ring-4 ring-white/60">
          <LighthouseIcon className="h-14 w-14" title="Lighthouse" />
        </div>

        {/* Greeting — the largest thing on the page */}
        <h1 className="text-5xl font-bold leading-tight text-slate-900 sm:text-6xl">
          {greeting(now)}, {PERSON_NAME}.
        </h1>

        <p className="mt-4 text-2xl font-medium text-slate-600">
          {formatFriendlyDate(now)}
        </p>

        {/* Reassurance */}
        <p className="mx-auto mt-8 max-w-xl text-3xl leading-relaxed text-slate-800">
          Everything&apos;s okay. Lighthouse is looking out for you.
        </p>

        {/* Calm "protected" pill — reassuring status, NOT a toggle */}
        <div className="mt-8 inline-flex items-center gap-3 rounded-full bg-green-100 px-6 py-3 text-2xl font-semibold text-green-800">
          <ShieldIcon className="h-7 w-7" />
          You&apos;re protected
        </div>

        {/* Gentle reminders — a warm family note and one small nudge */}
        <div className="mt-12 space-y-5 text-left">
          <article className="rounded-3xl bg-white/80 p-8 shadow-sm">
            <p className="text-xl font-semibold text-blue-700">
              A note from {familyNote.from}, {familyNote.relation}
            </p>
            <p className="mt-3 text-2xl leading-relaxed text-slate-800">
              {familyNote.message}
            </p>
          </article>

          <article className="rounded-3xl bg-white/80 p-8 shadow-sm">
            <p className="text-xl font-semibold text-blue-700">
              A gentle reminder
            </p>
            <p className="mt-3 text-2xl leading-relaxed text-slate-800">
              {dayReminder}
            </p>
          </article>
        </div>
      </div>
    </main>
  );
}
