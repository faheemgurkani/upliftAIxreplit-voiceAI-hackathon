"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CorroborationMap } from "@/components/CorroborationMap";
import { FlagBadge } from "@/components/StatusBadge";
import { getCluster } from "@/lib/api";
import { formatDate, languageLabel } from "@/lib/format";
import type { ClusterDetail, StatementSummary } from "@/lib/types";

export default function ClusterDetailPage() {
  const params = useParams<{ clusterId: string }>();
  const clusterId = decodeURIComponent(params.clusterId || "");
  const [cluster, setCluster] = useState<ClusterDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!clusterId) return;
    let cancelled = false;
    getCluster(clusterId)
      .then((data) => {
        if (!cancelled) setCluster(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load cluster");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [clusterId]);

  const linked: StatementSummary[] =
    cluster?.linked_statements || cluster?.statements || [];

  return (
    <div className="mx-auto max-w-4xl px-5 py-10 md:px-8 md:py-14">
      <Link
        href="/clusters"
        className="text-sm text-mist-400 transition-colors duration-300 hover:text-brass-300"
      >
        ← Back to clusters
      </Link>

      {loading && <p className="mt-8 text-sm text-mist-400">Loading…</p>}
      {error && (
        <p className="mt-8 rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {cluster && (
        <div className="mt-6 space-y-6 animate-fade-up">
          <header>
            <h1 className="font-display text-3xl text-mist-50 md:text-4xl">
              {cluster.cluster_label || cluster.id}
            </h1>
            <p className="mt-3 text-sm text-mist-300">
              {cluster.statement_count ?? linked.length} witness statements
              {cluster.composite_score != null && (
                <>
                  {" "}
                  · Composite corroboration score:{" "}
                  <span className="text-brass-300">
                    {cluster.composite_score.toFixed(2)}
                  </span>
                </>
              )}
            </p>
            {cluster.collusion_warning && (
              <div className="mt-3">
                <FlagBadge tone="warn">Collusion warning</FlagBadge>
              </div>
            )}
          </header>

          <CorroborationMap
            fields={cluster.field_results}
            compositeScore={cluster.composite_score}
            consensus={cluster.consensus_recommendation}
            collusionWarning={cluster.collusion_warning}
          />

          <section className="glass-panel rounded-xl p-5 md:p-6">
            <h2 className="mb-4 font-display text-xl text-mist-50">
              Linked statements
            </h2>
            {linked.length === 0 ? (
              <p className="text-sm text-mist-400">No linked statements returned.</p>
            ) : (
              <ul className="space-y-3">
                {linked.map((s) => (
                  <li key={s.ref_code}>
                    <Link
                      href={`/dashboard/${encodeURIComponent(s.ref_code)}`}
                      className="interactive-row flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/10 bg-ink-950/40 px-3 py-3 text-sm"
                    >
                      <span className="font-medium tracking-wide text-mist-50">
                        {s.ref_code}
                      </span>
                      <span className="text-mist-400">
                        {languageLabel(s.language_of_call)}
                        {s.witness_type ? ` · ${s.witness_type}` : ""}
                        {s.created_at ? ` · ${formatDate(s.created_at)}` : ""}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
