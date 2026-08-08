"use client";

import { useState } from "react";
import { reviewStatement } from "@/lib/api";

export function ReviewForm({ refCode }: { refCode: string }) {
  const [notes, setNotes] = useState("");
  const [reviewedBy, setReviewedBy] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "ok" | "error">("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("saving");
    setMessage("");
    try {
      await reviewStatement(refCode, {
        reviewer_notes: notes,
        reviewed_by: reviewedBy,
      });
      setStatus("ok");
      setMessage("Review saved.");
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Failed to save review");
    }
  }

  return (
    <section className="glass-panel rounded-xl p-5 md:p-6">
      <h2 className="mb-4 font-display text-xl text-mist-50">Review</h2>
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block text-sm">
          <span className="mb-1.5 block text-mist-400">Reviewed by</span>
          <input
            required
            value={reviewedBy}
            onChange={(e) => setReviewedBy(e.target.value)}
            className="w-full rounded-md border border-white/10 bg-ink-950/60 px-3 py-2 text-mist-50 outline-none transition-colors duration-300 focus:border-brass-400/50"
            placeholder="Lawyer / NGO officer name"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1.5 block text-mist-400">Reviewer notes</span>
          <textarea
            required
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full resize-y rounded-md border border-white/10 bg-ink-950/60 px-3 py-2 text-mist-50 outline-none transition-colors duration-300 focus:border-brass-400/50"
            placeholder="Notes for counsel, follow-ups, resolution of flags…"
          />
        </label>
        <button
          type="submit"
          disabled={status === "saving"}
          className="rounded-md bg-brass-400 px-4 py-2.5 text-sm font-medium text-ink-950 transition-all duration-300 hover:bg-brass-300 disabled:opacity-60"
        >
          {status === "saving" ? "Saving…" : "Mark reviewed"}
        </button>
        {message && (
          <p
            className={`text-sm ${
              status === "error" ? "text-red-300" : "text-moss-400"
            }`}
          >
            {message}
          </p>
        )}
      </form>
    </section>
  );
}
