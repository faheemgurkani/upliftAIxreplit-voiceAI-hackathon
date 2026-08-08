"use client";

import { useEffect, useMemo, useState } from "react";
import { StatementRow } from "@/components/StatementRow";
import { listStatements } from "@/lib/api";
import type { StatementSummary } from "@/lib/types";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending_review", label: "Pending review" },
  { value: "urgent_escalation", label: "Urgent escalation" },
  { value: "reviewed", label: "Reviewed" },
  { value: "submitted", label: "Submitted" },
  { value: "incomplete", label: "Incomplete" },
  { value: "archived", label: "Archived" },
];

const FLAG_OPTIONS = [
  { value: "", label: "All flags" },
  { value: "intimidation", label: "Intimidation / urgent" },
  { value: "inconsistency", label: "Inconsistency flagged" },
];

export default function DashboardPage() {
  const [status, setStatus] = useState("");
  const [flag, setFlag] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<StatementSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    listStatements({ status: status || undefined, page, flags: flag || undefined })
      .then((data) => {
        if (cancelled) return;
        setItems(data.items || []);
        setTotal(data.total ?? data.items?.length ?? 0);
      })
      .catch((err) => {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setError(err instanceof Error ? err.message : "Failed to load statements");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, page, flag]);

  const filtered = useMemo(() => {
    if (!flag) return items;
    return items.filter((s) => {
      if (flag === "intimidation") return !!s.intimidation_flag;
      if (flag === "inconsistency")
        return (s.inconsistency_flags?.length || 0) > 0;
      return true;
    });
  }, [items, flag]);

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 md:px-8 md:py-14">
      <header className="mb-8 animate-fade-up">
        <p className="text-xs uppercase tracking-[0.2em] text-brass-300">
          NGO / lawyer desk
        </p>
        <h1 className="mt-2 font-display text-3xl text-mist-50 md:text-4xl">
          Statements
        </h1>
        <p className="mt-3 text-sm text-mist-300">
          Filter by review status and risk flags. {total} total from API.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap gap-3 animate-fade-up-delay">
        <select
          value={status}
          onChange={(e) => {
            setPage(1);
            setStatus(e.target.value);
          }}
          className="rounded-md border border-white/10 bg-ink-900/80 px-3 py-2 text-sm text-mist-100 outline-none transition-colors duration-300 focus:border-brass-400/50"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value || "all"} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={flag}
          onChange={(e) => {
            setPage(1);
            setFlag(e.target.value);
          }}
          className="rounded-md border border-white/10 bg-ink-900/80 px-3 py-2 text-sm text-mist-100 outline-none transition-colors duration-300 focus:border-brass-400/50"
        >
          {FLAG_OPTIONS.map((o) => (
            <option key={o.value || "all-flags"} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <p className="text-sm text-mist-400">Loading statements…</p>
      )}
      {error && (
        <p className="mb-4 rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {!loading && !error && filtered.length === 0 && (
        <p className="text-sm text-mist-400">No statements match these filters.</p>
      )}

      <ul className="space-y-3 animate-fade-up-late">
        {filtered.map((s) => (
          <li key={s.ref_code}>
            <StatementRow statement={s} />
          </li>
        ))}
      </ul>

      <div className="mt-8 flex items-center gap-3">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="rounded-md border border-white/10 px-3 py-1.5 text-sm text-mist-200 transition-colors duration-300 hover:border-brass-400/40 disabled:opacity-40"
        >
          Previous
        </button>
        <span className="text-sm text-mist-400">Page {page}</span>
        <button
          type="button"
          disabled={items.length === 0}
          onClick={() => setPage((p) => p + 1)}
          className="rounded-md border border-white/10 px-3 py-1.5 text-sm text-mist-200 transition-colors duration-300 hover:border-brass-400/40 disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
