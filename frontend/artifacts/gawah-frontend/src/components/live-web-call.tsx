import { useEffect, useMemo, useRef } from 'react';
import {
  AudioTrack,
  BarVisualizer,
  DisconnectButton,
  RoomAudioRenderer,
  StartAudio,
  TrackToggle,
  UpliftAIRoom,
  useTracks,
  useUpliftAIRoom,
  useVoiceAssistant,
} from '@upliftai/assistants-react';
import { Track } from 'livekit-client';
import { buildGawahTools, type ToolEvent } from '@/lib/gawah-tools';
import { postWebEvent } from '@/lib/api';

interface Props {
  token: string;
  wsUrl: string;
  callId: string;
  onLog: (line: string) => void;
  onTool?: (ev: ToolEvent) => void;
  onEnded?: () => void;
}

/**
 * Live WebRTC body.
 *
 * Important (Uplift docs):
 * - updateInstruction() REPLACES the entire system prompt. Never use it to
 *   inject a short "web channel" blurb — that wiped Phase 0–4 + greeting and
 *   made the agent go silent vs phone (phone uses additive additionalInstructions).
 * - Web channel notes are baked into adhoc createSession config on the backend.
 * - Browser autoplay often blocks agent TTS until a user gesture → StartAudio.
 */
function CallBody({
  callId,
  onLog,
  onEnded,
  tools,
}: {
  callId: string;
  onLog: (line: string) => void;
  onEnded?: () => void;
  tools: ReturnType<typeof buildGawahTools>;
}) {
  const { isConnected, agentParticipant, upsertTools } = useUpliftAIRoom();
  const { state, audioTrack } = useVoiceAssistant();
  const tracks = useTracks([Track.Source.Microphone], { onlySubscribed: true });
  const agentMicTrack = tracks.find((t) => !t.participant.isLocal);
  const playTrack = audioTrack || agentMicTrack;
  const connectedOnce = useRef(false);
  const toolsOnce = useRef(false);
  const lastState = useRef<string>('');

  useEffect(() => {
    if (isConnected && !connectedOnce.current) {
      connectedOnce.current = true;
      onLog(`[${ts()}] Live web call connected — full Gawah agent (same as phone)`);
      void postWebEvent(callId, {
        type: 'webrtc_connected',
        detail: 'Uplift WebRTC room connected',
        status: 'connected',
      });
    }
  }, [isConnected, callId, onLog]);

  // Ensure client tool handlers are registered (RPC runs in the browser).
  useEffect(() => {
    if (!isConnected || toolsOnce.current) return;
    if (typeof upsertTools !== 'function') return;
    toolsOnce.current = true;
    void (async () => {
      try {
        await upsertTools(tools as never);
        onLog(`[${ts()}] Tool handlers registered (${tools.length})`);
        void postWebEvent(callId, {
          type: 'web_tools_synced',
          detail: `upsertTools: ${tools.map((t) => t.name).join(', ')}`,
          status: 'connected',
        });
      } catch (err) {
        onLog(
          `[${ts()}] Tool sync warning: ${
            err instanceof Error ? err.message : 'unknown'
          }`,
        );
      }
    })();
  }, [isConnected, upsertTools, tools, callId, onLog]);

  useEffect(() => {
    if (agentParticipant) {
      onLog(`[${ts()}] Agent joined: ${agentParticipant.identity}`);
    }
  }, [agentParticipant, onLog]);

  useEffect(() => {
    if (!state || state === lastState.current) return;
    lastState.current = state;
    onLog(`[${ts()}] Agent ${state}`);
    void postWebEvent(callId, {
      type: `agent_${state}`,
      detail: `Voice assistant state: ${state}`,
      status: state === 'listening' || state === 'speaking' ? 'connected' : undefined,
    });
  }, [state, callId, onLog]);

  const agentLabel =
    state === 'speaking'
      ? 'Agent speaking…'
      : state === 'thinking'
        ? 'Agent thinking…'
        : state === 'listening'
          ? 'Listening — speak your statement'
          : 'Connecting…';

  return (
    <div className="bento">
      <div className="bento-h">
        <span className="dot dot-o" />
        LIVE.WEB.CALL · UPLIFT WEBRTC
      </div>
      <div className="bento-body">
        <p style={{ fontSize: 15, marginBottom: 16, lineHeight: 1.6 }}>
          Same Gawah agent as phone — talk continuously. Phase 0 caution, §161 fields, live
          tools, readback, and confirmation. Allow microphone + unmute browser audio if prompted.
        </p>

        {/* Plays all remote audio (agent TTS). Critical for browser autoplay policies. */}
        <RoomAudioRenderer />
        <StartAudio label="Click to enable agent audio" className="cta-btn cta-ghost" />

        <div className="live-pill" style={{ marginBottom: 16, marginTop: 12 }}>
          <span className="pulse-dot" />
          {isConnected ? agentLabel.toUpperCase() : 'CONNECTING…'}
        </div>

        {playTrack && (
          <div
            style={{
              marginBottom: 16,
              padding: 16,
              border: '1px solid var(--e-line, #333)',
              minHeight: 72,
            }}
          >
            {/* Explicit agent track + RoomAudioRenderer (belt and suspenders) */}
            <AudioTrack trackRef={playTrack} />
            <BarVisualizer state={state} trackRef={playTrack} barCount={18} />
          </div>
        )}

        {agentParticipant && (
          <div className="pager-meta" style={{ marginBottom: 12 }}>
            Agent: {agentParticipant.identity}
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <TrackToggle source={Track.Source.Microphone} className="cta-btn cta-ghost">
            Mic
          </TrackToggle>
          <DisconnectButton
            className="cta-btn"
            onClick={() => {
              onLog(`[${ts()}] Ended live web call`);
              void postWebEvent(callId, {
                type: 'webrtc_disconnect',
                detail: 'User ended call',
                status: 'completed',
              });
              onEnded?.();
            }}
          >
            End call
          </DisconnectButton>
        </div>
      </div>
    </div>
  );
}

export function LiveWebCall({
  token,
  wsUrl,
  callId,
  onLog,
  onTool,
  onEnded,
}: Props) {
  const tools = useMemo(
    () =>
      buildGawahTools(callId, (ev) => {
        onLog(
          `[${ts()}] Tool ${ev.name}${ev.refCode ? ` · ref ${ev.refCode}` : ''} · ${ev.detail || ''}`,
        );
        onTool?.(ev);
        void postWebEvent(callId, {
          type: `tool_${ev.name}`,
          detail: ev.detail || ev.name,
          status: ev.name === 'save_witness_statement' ? 'processing' : 'connected',
        });
      }),
    [callId, onLog, onTool],
  );

  return (
    <UpliftAIRoom
      token={token}
      serverUrl={wsUrl}
      connect
      audio
      video={false}
      tools={tools as never}
      onConnectionChange={(connected, agentIdentity) => {
        onLog(
          `[${ts()}] Connection ${connected ? 'up' : 'down'}${
            agentIdentity ? ` · ${agentIdentity}` : ''
          }`,
        );
      }}
    >
      <CallBody callId={callId} onLog={onLog} onEnded={onEnded} tools={tools} />
    </UpliftAIRoom>
  );
}

function ts() {
  return new Date().toLocaleTimeString();
}
