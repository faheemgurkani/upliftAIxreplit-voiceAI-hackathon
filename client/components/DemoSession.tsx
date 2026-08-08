"use client";

import dynamic from "next/dynamic";
import { Component, useCallback, useState, type ReactNode } from "react";
import { createSession, getApiUrl } from "@/lib/api";
import type { SessionCreateResponse } from "@/lib/types";

const VoiceRoom = dynamic(() => import("@/components/VoiceRoom"), {
  ssr: false,
  loading: () => (
    <p className="text-sm text-mist-400">Loading voice room…</p>
  ),
});

type ConnState = "idle" | "creating" | "ready" | "connected" | "error";

export function DemoSession() {
  const [conn, setConn] = useState<ConnState>("idle");
  const [session, setSession] = useState<SessionCreateResponse | null>(null);
  const [error, setError] = useState("");
  const [toolLog, setToolLog] = useState<string[]>([]);
  const [useLive, setUseLive] = useState(true);
  const [liveFailed, setLiveFailed] = useState(false);

  const token = session?.token ? String(session.token) : "";
  const wsUrl = String(session?.wsUrl || session?.ws_url || "");

  const startSession = useCallback(async () => {
    setConn("creating");
    setError("");
    setLiveFailed(false);
    setToolLog((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] POST ${getApiUrl()}/api/sessions/create`,
    ]);
    try {
      const data = await createSession({ participantName: "Witness" });
      setSession(data);
      setConn("ready");
      setToolLog((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] Session created · room ${
          data.roomName || data.room_name || "—"
        }`,
      ]);
    } catch (err) {
      setConn("error");
      setError(err instanceof Error ? err.message : "Session create failed");
      setToolLog((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] Error: ${
          err instanceof Error ? err.message : "unknown"
        }`,
      ]);
    }
  }, []);

  const markConnected = () => {
    setConn("connected");
    setUseLive(false);
    setToolLog((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] Mock WebRTC connected`,
    ]);
  };

  return (
    <div className="space-y-6">
      <section className="glass-panel rounded-xl p-5 md:p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-xl text-mist-50">Voice session</h2>
            <p className="mt-1 text-sm text-mist-400">
              Creates an Uplift AI session via the FastAPI backend, then connects
              in-browser.
            </p>
          </div>
          <button
            type="button"
            onClick={startSession}
            disabled={conn === "creating"}
            className="rounded-md bg-brass-400 px-4 py-2.5 text-sm font-medium text-ink-950 transition-all duration-300 hover:bg-brass-300 disabled:opacity-60"
          >
            {conn === "creating" ? "Creating…" : "Start session"}
          </button>
        </div>

        {error && (
          <p className="mb-4 rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        {session && (
          <dl className="mb-5 grid gap-3 text-sm sm:grid-cols-2">
            <div className="rounded-lg border border-white/10 bg-ink-950/40 p-3">
              <dt className="text-[11px] uppercase tracking-wide text-mist-400">
                Token
              </dt>
              <dd className="mt-1 break-all font-mono text-xs text-mist-200">
                {token ? `${token.slice(0, 48)}…` : "—"}
              </dd>
            </div>
            <div className="rounded-lg border border-white/10 bg-ink-950/40 p-3">
              <dt className="text-[11px] uppercase tracking-wide text-mist-400">
                WebSocket URL
              </dt>
              <dd className="mt-1 break-all font-mono text-xs text-mist-200">
                {wsUrl || "—"}
              </dd>
            </div>
            <div className="rounded-lg border border-white/10 bg-ink-950/40 p-3 sm:col-span-2">
              <dt className="text-[11px] uppercase tracking-wide text-mist-400">
                Room
              </dt>
              <dd className="mt-1 font-mono text-xs text-mist-200">
                {String(session.roomName || session.room_name || "—")}
              </dd>
            </div>
          </dl>
        )}

        {session && token && wsUrl && useLive && !liveFailed ? (
          <div className="rounded-lg border border-moss-400/20 bg-moss-500/5 p-4">
            <ErrorBoundary
              onError={() => {
                setLiveFailed(true);
                setToolLog((prev) => [
                  ...prev,
                  `[${new Date().toLocaleTimeString()}] Live SDK failed — falling back to mock UI`,
                ]);
              }}
            >
              <VoiceRoom
                token={token}
                wsUrl={wsUrl}
                onToolEvent={(msg) => setToolLog((prev) => [...prev, msg])}
              />
            </ErrorBoundary>
          </div>
        ) : session ? (
          <div className="rounded-lg border border-white/10 bg-ink-950/40 p-4">
            <p className="mb-3 text-sm text-mist-300">
              {liveFailed
                ? "Mock connection UI — live SDK failed to mount. Backend session call still succeeded."
                : token && wsUrl
                  ? "Credentials ready. Use live room above or simulate connect."
                  : "Session response missing token/wsUrl — showing credentials only."}
            </p>
            <div className="mb-4 flex items-center gap-3">
              <span
                className={`inline-flex h-3 w-3 rounded-full ${
                  conn === "connected"
                    ? "bg-moss-400 animate-pulse-soft"
                    : "bg-brass-400"
                }`}
              />
              <span className="text-sm text-mist-200">
                Status: {conn === "connected" ? "Mock connected" : "Ready"}
              </span>
            </div>
            <button
              type="button"
              onClick={markConnected}
              className="rounded-md border border-brass-400/40 bg-brass-400/10 px-3 py-2 text-sm text-brass-300 transition-colors duration-300 hover:bg-brass-400/20"
            >
              Simulate connect
            </button>
          </div>
        ) : (
          <p className="text-sm text-mist-400">
            Press Start session to call{" "}
            <code className="text-brass-300">POST /api/sessions/create</code>.
          </p>
        )}
      </section>

      <section className="glass-panel rounded-xl p-5 md:p-6">
        <h2 className="mb-3 font-display text-xl text-mist-50">Tool call status</h2>
        <div className="max-h-56 overflow-y-auto rounded-lg border border-white/10 bg-ink-950/50 p-3 font-mono text-xs leading-relaxed text-mist-300">
          {toolLog.length === 0 ? (
            <p className="text-mist-400">No events yet.</p>
          ) : (
            toolLog.map((line, i) => <p key={`${i}-${line}`}>{line}</p>)
          )}
        </div>
      </section>
    </div>
  );
}

class ErrorBoundary extends Component<
  { children: ReactNode; onError: () => void },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch() {
    this.props.onError();
  }

  render() {
    if (this.state.hasError) return null;
    return this.props.children;
  }
}
