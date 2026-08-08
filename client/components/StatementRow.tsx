import Link from "next/link";
import { FlagBadge, StatusBadge } from "@/components/StatusBadge";
import { formatDate, languageLabel, scoreTone } from "@/lib/format";
import type { StatementSummary } from "@/lib/types";

export function StatementRow({ statement }: { statement: StatementSummary }) {
  const score = statement.corroboration_score;
  const tone = scoreTone(score);
  const flagCount = statement.inconsistency_flags?.length || 0;

  return (
    <Link
      href={`/dashboard/${encodeURIComponent(statement.ref_code)}`}
      className="interactive-row glass-panel block rounded-xl px-4 py-4 md:px-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-display text-lg tracking-wide text-mist-50">
            {statement.ref_code}
          </p>
          <p className="mt-1 text-sm text-mist-300">
            {statement.location || "Location unknown"}
          </p>
          <p className="mt-1 text-xs text-mist-400">
            {formatDate(statement.created_at)} · {languageLabel(statement.language_of_call)}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={statement.status} />
          {statement.intimidation_flag && <FlagBadge tone="urgent">Urgent</FlagBadge>}
          {flagCount > 0 && (
            <FlagBadge tone="flagged">Flagged · {flagCount}</FlagBadge>
          )}
          {score != null && (
            <FlagBadge tone={tone === "good" ? "good" : tone === "warn" ? "warn" : "flagged"}>
              {tone === "good" ? "Corroborated" : tone === "warn" ? "Partial" : "Conflicting"}{" "}
              {score.toFixed(2)}
            </FlagBadge>
          )}
        </div>
      </div>
    </Link>
  );
}
