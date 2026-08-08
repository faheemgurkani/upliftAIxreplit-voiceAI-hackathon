import type { InconsistencyFlag } from "@/lib/types";

export function InconsistencyPanel({ flags }: { flags?: InconsistencyFlag[] }) {
  const list = flags || [];

  return (
    <section className="glass-panel rounded-xl p-5 md:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-xl text-mist-50">
          Statement consistency analysis
        </h2>
        <span
          className={`rounded border px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${
            list.length
              ? "border-orange-400/30 bg-orange-500/15 text-orange-300"
              : "border-moss-400/30 bg-moss-500/15 text-moss-400"
          }`}
        >
          {list.length} flag{list.length === 1 ? "" : "s"}
        </span>
      </div>
      <p className="mb-5 text-sm text-mist-400">
        Source: Real-time (during call) + post-call NLP analysis
      </p>

      {list.length === 0 ? (
        <p className="text-sm text-mist-200/80">No inconsistency flags on this statement.</p>
      ) : (
        <ul className="space-y-5">
          {list.map((flag, i) => (
            <li
              key={`${flag.category}-${i}`}
              className="border-t border-white/10 pt-5 first:border-0 first:pt-0"
            >
              <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium text-mist-50">Flag {i + 1}</span>
                <span className="rounded border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] uppercase tracking-wide text-mist-300">
                  {flag.category}
                </span>
                <span className="text-brass-300">
                  Score: {typeof flag.score === "number" ? flag.score.toFixed(2) : "—"}
                </span>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <blockquote className="rounded-lg border border-white/10 bg-ink-950/50 p-3 text-sm text-mist-200">
                  <span className="mb-1 block text-[11px] uppercase tracking-wide text-mist-400">
                    Segment A
                  </span>
                  “{flag.segment_a}”
                </blockquote>
                <blockquote className="rounded-lg border border-white/10 bg-ink-950/50 p-3 text-sm text-mist-200">
                  <span className="mb-1 block text-[11px] uppercase tracking-wide text-mist-400">
                    Segment B
                  </span>
                  “{flag.segment_b}”
                </blockquote>
              </div>
              {flag.analysis && (
                <p className="mt-3 text-sm text-mist-200/90">
                  <span className="text-mist-400">Analysis: </span>
                  {flag.analysis}
                </p>
              )}
              {flag.legal_risk && (
                <p className="mt-1 text-sm text-orange-300/90">
                  <span className="text-mist-400">Legal risk: </span>
                  {flag.legal_risk}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
