const STATUS_STYLES: Record<string, string> = {
  pending_review: "bg-brass-400/15 text-brass-300 border-brass-400/30",
  urgent_escalation: "bg-red-500/15 text-red-300 border-red-400/35",
  reviewed: "bg-moss-500/20 text-moss-400 border-moss-400/30",
  submitted: "bg-sky-500/15 text-sky-300 border-sky-400/30",
  incomplete: "bg-white/5 text-mist-400 border-white/10",
  archived: "bg-white/5 text-mist-400 border-white/10",
};

export function StatusBadge({ status }: { status?: string }) {
  if (!status) return null;
  const style = STATUS_STYLES[status] || "bg-white/5 text-mist-200 border-white/10";
  const label = status.replace(/_/g, " ");
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${style}`}
    >
      {label}
    </span>
  );
}

export function FlagBadge({
  tone,
  children,
}: {
  tone: "urgent" | "flagged" | "good" | "warn" | "neutral";
  children: React.ReactNode;
}) {
  const styles = {
    urgent: "bg-red-500/15 text-red-300 border-red-400/35",
    flagged: "bg-orange-500/15 text-orange-300 border-orange-400/30",
    good: "bg-moss-500/20 text-moss-400 border-moss-400/30",
    warn: "bg-brass-400/15 text-brass-300 border-brass-400/30",
    neutral: "bg-white/5 text-mist-300 border-white/10",
  };
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${styles[tone]}`}
    >
      {children}
    </span>
  );
}
