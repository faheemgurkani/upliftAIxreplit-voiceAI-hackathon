"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FlagBadge } from "@/components/StatusBadge";
import { listClusters, normalizeClusters } from "@/lib/api";
import { formatDate, scoreTone } from "@/lib/format";
import type { ClusterSummary } from "@/lib/types";

export default function ClustersPage() {
  const [items, setItems] = useState<ClusterSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    listClusters()
      .then((data) => {
        if (!cancelled) setItems(normalizeClusters(data));
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load clusters");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 md:px-8 md:py-14">
      <header className="mb-8 animate-fade-up">
        <p className="text-xs uppercase tracking-[0.2em] text-brass-300">
          Multi-witness layer
        </p>
        <h1 className="mt-2 font-display text-3xl text-mist-50 md:text-4xl">
          Incident clusters
        </h1>
        <p className="mt-3 max-w-xl text-sm text-mist-300">
          Linked statements grouped by time, place, and narrative overlap.
        </p>
      </header>

      {loading && <p className="text-sm text-mist-400">Loading clusters…</p>}
      {error && (
        <p className="rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-mist-400">No clusters yet.</p>
      )}

      <ul className="space-y-3 animate-fade-up-delay">
        {items.map((c) => {
          const tone = scoreTone(c.composite_score);
          return (
            <li key={c.id}>
              <Link
                href={`/clusters/${encodeURIComponent(c.id)}`}
                className="interactive-row glass-panel block rounded-xl px-4 py-4 md:px-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-display text-lg text-mist-50">
                      {c.cluster_label || c.id}
                    </p>
                    <p className="mt-1 text-sm text-mist-300">
                      {c.statement_count ?? "—"} statements
                      {c.created_at ? ` · ${formatDate(c.created_at)}` : ""}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {c.composite_score != null && (
                      <FlagBadge
                        tone={
                          tone === "good"
                            ? "good"
                            : tone === "warn"
                              ? "warn"
                              : "flagged"
                        }
                      >
                        Score {c.composite_score.toFixed(2)}
                      </FlagBadge>
                    )}
                    {c.collusion_warning && (
                      <FlagBadge tone="warn">Collusion</FlagBadge>
                    )}
                    {c.cluster_status && (
                      <FlagBadge tone="neutral">
                        {c.cluster_status.replace(/_/g, " ")}
                      </FlagBadge>
                    )}
                  </div>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
