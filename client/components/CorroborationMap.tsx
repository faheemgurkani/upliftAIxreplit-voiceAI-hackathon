import { fieldLabel } from "@/lib/format";
import type { FieldCorroboration } from "@/lib/types";

function barWidth(score: number | null): string {
  if (score == null) return "0%";
  return `${Math.round(Math.min(1, Math.max(0, score)) * 100)}%`;
}

function statusMeta(status: string) {
  if (status === "agreement")
    return { label: "Agreement", tone: "text-moss-400" };
  if (status === "partial" || status === "partial_agreement")
    return { label: "Partial agreement", tone: "text-brass-300" };
  if (status === "conflict")
    return { label: "Conflict", tone: "text-orange-300" };
  if (status === "collusion_warning")
    return { label: "Collusion warning", tone: "text-yellow-300" };
  return { label: status.replace(/_/g, " "), tone: "text-mist-300" };
}

function valueText(v: string | { ref_code?: string; value?: string }): string {
  if (typeof v === "string") return v;
  if (v.ref_code && v.value) return `${v.ref_code}: "${v.value}"`;
  return v.value || v.ref_code || "—";
}

export function CorroborationMap({
  fields,
  compositeScore,
  consensus,
  collusionWarning,
}: {
  fields?: FieldCorroboration[];
  compositeScore?: number | null;
  consensus?: string;
  collusionWarning?: boolean;
}) {
  const list = fields || [];

  return (
    <section className="glass-panel rounded-xl p-5 md:p-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <h2 className="font-display text-xl text-mist-50">
          Field-level corroboration map
        </h2>
        {compositeScore != null && (
          <p className="text-sm text-mist-300">
            Composite score:{" "}
            <span className="font-medium text-brass-300">
              {compositeScore.toFixed(2)}
            </span>
          </p>
        )}
      </div>

      {list.length === 0 ? (
        <p className="text-sm text-mist-200/80">No field-level results yet.</p>
      ) : (
        <ul className="space-y-4">
          {list.map((f) => {
            const meta = statusMeta(f.status);
            return (
              <li key={f.field}>
                <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="text-mist-100">{fieldLabel(f.field)}</span>
                  <span className={meta.tone}>
                    {f.agreement_score != null
                      ? f.agreement_score.toFixed(2)
                      : "—"}{" "}
                    · {meta.label}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-ink-950/80">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-moss-600 to-brass-400 transition-all duration-700"
                    style={{ width: barWidth(f.agreement_score) }}
                  />
                </div>
                {f.values && f.values.length > 0 && (
                  <p className="mt-2 text-xs leading-relaxed text-mist-400">
                    {f.values.map(valueText).join(" · ")}
                  </p>
                )}
                {(f.conflict_detail || f.note) && (
                  <p className="mt-1 text-xs text-mist-300">
                    {f.conflict_detail || f.note}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {consensus && (
        <div className="mt-6 rounded-lg border border-white/10 bg-ink-950/40 p-4 text-sm text-mist-200">
          <p className="mb-1 text-[11px] uppercase tracking-wide text-mist-400">
            Consensus recommendation
          </p>
          {consensus}
        </div>
      )}

      <p
        className={`mt-4 text-sm ${
          collusionWarning ? "text-yellow-300" : "text-mist-400"
        }`}
      >
        Collusion warning: {collusionWarning ? "Triggered — investigate before submission" : "None"}
      </p>

      <p className="mt-4 border-t border-white/10 pt-4 text-xs leading-relaxed text-mist-400">
        Pre-litigation intelligence only — not admissible corroboration under CrPC
        Section 162.
      </p>
    </section>
  );
}
