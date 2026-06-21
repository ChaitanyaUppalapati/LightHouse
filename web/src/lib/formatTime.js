// Friendly, human time formatting. Family members are not reading ISO timestamps.

export function formatRelative(iso, now = new Date()) {
  const then = new Date(iso);
  const diffMs = now - then;
  const diffMin = Math.round(diffMs / 60000);

  if (Number.isNaN(diffMin)) return "";
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? "" : "s"} ago`;

  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr} hour${diffHr === 1 ? "" : "s"} ago`;

  const diffDay = Math.round(diffHr / 24);
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`;

  return then.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function formatClock(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// Time-of-day greeting for the protected-person screen (S3). Warm, never clinical.
export function greeting(now = new Date()) {
  const hour = now.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

// A big, friendly date Margaret can read at a glance — e.g. "Saturday, June 20".
export function formatFriendlyDate(now = new Date()) {
  return now.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}
