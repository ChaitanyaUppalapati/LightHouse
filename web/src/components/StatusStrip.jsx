import { ShieldIcon, WarningIcon, CheckIcon } from "./Icons.jsx";

// At-a-glance reassurance for the family — one calm row, readable in a single look.
// Each pill carries an icon AND a word, so meaning never rests on color alone.
function Pill({ Icon, className, label }) {
  return (
    <div
      className={`flex items-center gap-2 rounded-full px-4 py-2 text-lg font-semibold ${className}`}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {label}
    </div>
  );
}

export default function StatusStrip({ needsYou, handledCount }) {
  return (
    <div className="mb-8 flex flex-wrap items-center gap-3">
      <Pill
        Icon={ShieldIcon}
        className="bg-green-100 text-green-800"
        label="Protected"
      />
      <Pill
        Icon={WarningIcon}
        className={
          needsYou > 0
            ? "bg-amber-100 text-amber-800"
            : "bg-slate-100 text-slate-600"
        }
        label={
          needsYou > 0
            ? `${needsYou} need${needsYou === 1 ? "s" : ""} you`
            : "Nothing needs you"
        }
      />
      <Pill
        Icon={CheckIcon}
        className="bg-blue-100 text-blue-800"
        label={`${handledCount} handled this week`}
      />
    </div>
  );
}
