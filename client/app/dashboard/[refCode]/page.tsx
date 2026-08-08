"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AudioPlayer } from "@/components/AudioPlayer";
import { InconsistencyPanel } from "@/components/InconsistencyPanel";
import { ReviewForm } from "@/components/ReviewForm";
import { FlagBadge, StatusBadge } from "@/components/StatusBadge";
import { WitnessProtection } from "@/components/WitnessProtection";
import { getStatement, getStatementAudioUrl } from "@/lib/api";
import { asList, formatDate, getCoreFields, languageLabel } from "@/lib/format";
import type { StatementDetail } from "@/lib/types";

function CoreFieldsBlock({ statement }: { statement: StatementDetail }) {
  const core = getCoreFields(statement);
  const persons = asList(core.persons_present);
  const sequence = asList(core.sequence_of_events);

  const rows: { label: string; value: React.ReactNode }[] = [
    { label: "Time of incident", value: core.time_of_incident || "—" },
    { label: "Location", value: core.location || "—" },
    {
      label: "Persons present",
      value:
        persons.length > 0 ? (
          <ul className="list-disc space-y-1 pl-4">
            {persons.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        ) : (
          "—"
        ),
    },
    {
      label: "Sequence of events",
      value:
        sequence.length > 0 ? (
          <ol className="list-decimal space-y-1 pl-4">
            {sequence.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ol>
        ) : (
          "—"
        ),
    },
    {
      label: "Relationship to parties",
      value: core.relationship_to_parties || "—",
    },
  ];

  return (
    <section className="glass-panel rounded-xl p-5 md:p-6">
      <h2 className="mb-4 font-display text-xl text-mist-50">Core fields</h2>
      <dl className="space-y-4">
        {rows.map((row) => (
          <div key={row.label}>
            <dt className="text-[11px] uppercase tracking-wide text-mist-400">
              {row.label}
            </dt>
            <dd className="mt-1 text-sm leading-relaxed text-mist-100">
              {row.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default function StatementDetailPage() {
  const params = useParams<{ refCode: string }>();
  const refCode = decodeURIComponent(params.refCode || "");
  const [statement, setStatement] = useState<StatementDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!refCode) return;
    let cancelled = false;
    setLoading(true);
    getStatement(refCode)
      .then((data) => {
        if (!cancelled) setStatement(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refCode]);

  const audioSrc =
    statement?.readback_audio_url ||
    (statement ? getStatementAudioUrl(refCode) : null);

  return (
    <div className="mx-auto max-w-4xl px-5 py-10 md:px-8 md:py-14">
      <Link
        href="/dashboard"
        className="text-sm text-mist-400 transition-colors duration-300 hover:text-brass-300"
      >
        ← Back to statements
      </Link>

      {loading && <p className="mt-8 text-sm text-mist-400">Loading…</p>}
      {error && (
        <p className="mt-8 rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {statement && (
        <div className="mt-6 space-y-6 animate-fade-up">
          <header>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="font-display text-3xl tracking-wide text-mist-50 md:text-4xl">
                  {statement.ref_code}
                </h1>
                <p className="mt-2 text-sm text-mist-300">
                  {formatDate(statement.created_at)} ·{" "}
                  {languageLabel(statement.language_of_call)}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={statement.status} />
                {statement.intimidation_flag && (
                  <FlagBadge tone="urgent">Urgent</FlagBadge>
                )}
                {statement.incident_cluster_id && (
                  <Link
                    href={`/clusters/${statement.incident_cluster_id}`}
                    className="rounded border border-moss-400/30 bg-moss-500/15 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-moss-400 transition-colors duration-300 hover:bg-moss-500/25"
                  >
                    View cluster
                  </Link>
                )}
              </div>
            </div>
            {statement.corroboration_score != null && (
              <p className="mt-4 text-sm text-mist-300">
                Corroboration score:{" "}
                <span className="text-brass-300">
                  {statement.corroboration_score.toFixed(2)}
                </span>
              </p>
            )}
            <p className="mt-3 max-w-2xl text-xs leading-relaxed text-mist-400">
              Pre-litigation intelligence only — not admissible corroboration
              under CrPC Section 162.
            </p>
          </header>

          <CoreFieldsBlock statement={statement} />
          <InconsistencyPanel flags={statement.inconsistency_flags} />
          <WitnessProtection
            protection={statement.protection || statement.protection_referral}
          />
          <AudioPlayer src={audioSrc} />
          <ReviewForm refCode={refCode} />
        </div>
      )}
    </div>
  );
}
