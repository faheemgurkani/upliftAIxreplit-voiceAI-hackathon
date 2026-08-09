import { Link } from 'wouter';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  callRecordingUrl,
  fetchActivity,
  fetchCalls,
  refreshCallArtifacts,
  type TrackedCall,
} from '@/lib/api';
import { PageShell } from '@/components/layout/page-shell';

function statusBadge(status?: string) {
  const s = (status || 'unknown').toLowerCase();
  if (['dispatched', 'dialing', 'ringing', 'answered', 'in_progress', 'connected', 'processing'].includes(s)) {
    return 'badge-amber';
  }
  if (s === 'completed') return 'badge-teal';
  if (s === 'failed') return 'badge-red';
  return 'badge-gray';
}

function formatDuration(sec?: number) {
  if (sec == null || Number.isNaN(sec)) return '—';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function transcriptPreview(call: TrackedCall) {
  const t = call.transcript;
  if (!t) return null;
  if (typeof t === 'string') return t.slice(0, 160);
  try {
    return JSON.stringify(t).slice(0, 160);
  } catch {
    return null;
  }
}

export default function CallsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['calls'],
    queryFn: () => fetchCalls(40),
    refetchInterval: 3000,
  });

  const { data: activity } = useQuery({
    queryKey: ['activity'],
    queryFn: () => fetchActivity(30),
    refetchInterval: 2500,
  });

  const refreshArtifacts = useMutation({
    mutationFn: (callId: string) => refreshCallArtifacts(callId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['calls'] }),
  });

  const counts = data?.counts;

  return (
    <PageShell>
      <div className="page-content page-stack">
        <div className="page-header">
          <div className="page-header-row">
            <div>
              <div className="section-eyebrow">// LIVE TRACKING · WEB + PSTN</div>
              <h1 className="section-title">
                CALL.<span className="accent">PIPELINE</span>
              </h1>
              <p className="section-sub">
                Web demo calls and Uplift phone calls — status, recordings, and transcripts sync
                every few seconds so judges can see real pipeline activity.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button
                type="button"
                className="cta-btn cta-ghost"
                onClick={() => refetch()}
                disabled={isFetching}
              >
                <span className="cta-sq">↻</span>
                <span className="cta-lbl">{isFetching ? 'Syncing' : 'Refresh'}</span>
              </button>
              <Link href="/demo" className="cta-btn">
                <span className="cta-sq">☎</span>
                <span className="cta-lbl">New call</span>
              </Link>
            </div>
          </div>
        </div>

        <div className="kpi-grid">
          <div className="hud">
            <div className="hud-k">Total tracked</div>
            <div className="hud-v vt">{counts?.total ?? '—'}</div>
          </div>
          <div className="hud">
            <div className="hud-k">Active / processing</div>
            <div className="hud-v vt accent">{counts?.active ?? '—'}</div>
          </div>
          <div className="hud">
            <div className="hud-k">Completed</div>
            <div className="hud-v vt">{counts?.completed ?? '—'}</div>
          </div>
          <div className="hud">
            <div className="hud-k">Artifacts</div>
            <div className="hud-v vt">{counts?.with_artifacts ?? 0}</div>
          </div>
        </div>

        {/*
        <div className="insight">
          <span className="insight-lbl">CHANNELS</span>
          <code>web_browser</code> = in-site recorder → STT → statement.{' '}
          <code>phone_outbound</code> = Uplift PSTN. Both update this table live.
        </div>
        */}

        {data?.sync_error && (
          <div className="insight" style={{ borderColor: 'var(--e-warn)' }}>
            <span className="insight-lbl">SYNC WARNING</span>
            Could not refresh from Uplift: {data.sync_error}
          </div>
        )}

        <div className="find-panel">
          <div className="find-head">
            <span className="find-n">LIVE</span>
            ACTIVITY FEED
          </div>
          <div
            className="find-body"
            style={{ fontFamily: 'monospace', fontSize: 12, maxHeight: 160, overflow: 'auto' }}
          >
            {(activity?.items || []).slice(0, 12).map((ev, idx) => (
              <div key={idx} style={{ marginBottom: 6 }}>
                {ev.at ? new Date(String(ev.at)).toLocaleTimeString() : '—'} · [
                {ev.channel || '?'}] {ev.type} · {ev.status || '—'}
                {ev.detail ? ` — ${String(ev.detail).slice(0, 90)}` : ''}
                {ev.ref_code ? ` · ref ${ev.ref_code}` : ''}
              </div>
            ))}
            {!activity?.items?.length && 'No activity yet — start a web or phone demo.'}
          </div>
        </div>

        {isLoading ? (
          <div className="state-panel">
            <div className="spinner" />
            <div className="pager-meta">Loading calls</div>
          </div>
        ) : error ? (
          <div className="insight" style={{ borderColor: 'var(--e-warn)' }}>
            <span className="insight-lbl">ERROR</span>
            Failed to load calls.
          </div>
        ) : !data?.items?.length ? (
          <div className="insight">
            <span className="insight-lbl">EMPTY</span>
            No calls yet. Use Demo → Web call or Phone call.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="brutal">
              <thead>
                <tr>
                  <th>WHEN</th>
                  <th>CHANNEL</th>
                  <th>TO / ROOM</th>
                  <th>STATUS</th>
                  <th>DURATION</th>
                  <th>DETAIL</th>
                  <th>ARTIFACTS</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((call) => {
                  const id = String(call.call_id || call.callId || '');
                  const status = call.status || call.state || 'unknown';
                  const preview = transcriptPreview(call);
                  const hasRecording = Boolean(
                    call.local_recording_path || call.recording_url,
                  );
                  const channel = String(call.channel || '—');
                  const isWeb = channel.includes('web');
                  return (
                    <tr key={id || Math.random()}>
                      <td>
                        {call.created_at
                          ? new Date(String(call.created_at)).toLocaleString()
                          : '—'}
                      </td>
                      <td>
                        <span className={`badge-e ${isWeb ? 'badge-teal' : 'badge-amber'}`}>
                          {isWeb ? 'web' : 'phone'}
                        </span>
                      </td>
                      <td className="first">
                        {call.to || call.room_name || call.participant_name || '—'}
                      </td>
                      <td>
                        <span className={`badge-e ${statusBadge(status)}`}>
                          {status}
                        </span>
                      </td>
                      <td>{formatDuration(call.duration_sec)}</td>
                      <td>
                        {call.label || call.outcome || call.failure_reason || '—'}
                        {call.ref_code ? ` · ref ${call.ref_code}` : ''}
                        {call.ended_by ? ` · ended by ${call.ended_by}` : ''}
                        {preview ? (
                          <div style={{ fontSize: 12, opacity: 0.75, marginTop: 4 }}>
                            {preview}
                            {preview.length >= 160 ? '…' : ''}
                          </div>
                        ) : null}
                      </td>
                      <td style={{ fontSize: 12 }}>
                        {hasRecording ? (
                          <a href={callRecordingUrl(id)} target="_blank" rel="noreferrer">
                            Recording
                          </a>
                        ) : (
                          call.artifacts_status || 'pending'
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="cta-btn cta-ghost"
                          style={{ padding: '6px 10px', fontSize: 12 }}
                          disabled={refreshArtifacts.isPending || !id || isWeb}
                          onClick={() => refreshArtifacts.mutate(id)}
                          title={isWeb ? 'Web artifacts stored locally' : 'Pull from Uplift'}
                        >
                          Pull
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageShell>
  );
}
