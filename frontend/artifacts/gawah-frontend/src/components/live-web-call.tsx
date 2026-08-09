import { useEffect, useMemo, useRef } from 'react';
import {
  AudioTrack,
  BarVisualizer,
  DisconnectButton,
  TrackToggle,
  UpliftAIRoom,
  useTracks,
  useUpliftAIRoom,
  useVoiceAssistant,
} from '@upliftai/assistants-react';
import { Track } from 'livekit-client';
import { buildGawahTools, type ToolEvent } from '@/lib/gawah-tools';
import { postWebEvent } from '@/lib/api';

/** Mirrors backend WEB_CALL_INSTRUCTIONS — injected on connect via updateInstruction. */
const WEB_CHANNEL_INSTRUCTIONS = [
  'Yeh browser / web call Gawah demo / live witness intake hai — phone call jaisi hi.',
  'Channel: web_browser (WebRTC). Witness ne khud demo se session shuru kiya hai.',
  'Phase 0 caution (voluntariness + PDPA consent) pehle complete karein,',
  'phir CrPC Section 161 ke mutabiq 5 fields collect karein.',
  'Hamesha Urdu ya Punjabi mein baat karein — witness ki zubaan follow karein.',
  'Tools available: save_witness_statement, flag_inconsistency, flag_intimidation,',
  'enable_privacy_mode, assess_protection_need, confirm_statement.',
  "Readback ke baad jab witness 'haan' kahe to confirm_statement call karein,",
  'phir reference code teen baar bolen.',
].join(' ');

interface Props {
  token: string;
  wsUrl: string;
  callId: string;
  onLog: (line: string) => void;
  onTool?: (ev: ToolEvent) => void;
  onEnded?: () => void;
}

function CallBody({
  callId,
  onLog,
  onEnded,
}: {
  callId: string;
  onLog: (line: string) => void;
  onEnded?: () => void;
}) {
  const { isConnected, agentParticipant, updateInstruction } = useUpliftAIRoom();
  const { state, audioTrack } = useVoiceAssistant();
  const tracks = useTracks([Track.Source.Microphone], { onlySubscribed: false });
  const localMic = tracks.find((t) => t.participant.isLocal);
  const connectedOnce = useRef(false);
  const instructedOnce = useRef(false);
  const lastState = useRef<string>('');

  useEffect(() => {
    if (isConnected && !connectedOnce.current) {
      connectedOnce.current = true;
      onLog(`[${ts()}] Live web call connected — same Gawah agent as phone`);
      void postWebEvent(callId, {
        type: 'webrtc_connected',
        detail: 'Uplift WebRTC room connected',
        status: 'connected',
      });
    }
  }, [isConnected, callId, onLog]);

  // Align web session behaviour with phone CALL_INSTRUCTIONS (Uplift updateInstruction)
  useEffect(() => {
    if (!isConnected || instructedOnce.current) return;
    if (typeof updateInstruction !== 'function') return;
    instructedOnce.current = true;
    void (async () => {
      try {
        await updateInstruction(WEB_CHANNEL_INSTRUCTIONS);
        onLog(`[${ts()}] Web channel instructions synced (Phase 0–4 + tools)`);
        void postWebEvent(callId, {
          type: 'web_instructions_synced',
          detail: 'updateInstruction applied for web channel parity',
          status: 'connected',
        });
      } catch (err) {
        onLog(
          `[${ts()}] Could not sync web instructions: ${
            err instanceof Error ? err.message : 'unknown'
          }`,
        );
      }
    })();
  }, [isConnected, updateInstruction, callId, onLog]);

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
          tools, readback, and confirmation. No record button.
        </p>
        <div className="live-pill" style={{ marginBottom: 16 }}>
          <span className="pulse-dot" />
          {isConnected ? agentLabel.toUpperCase() : 'CONNECTING…'}
        </div>
        {(audioTrack || localMic) && (
          <div
            style={{
              marginBottom: 16,
              padding: 16,
              border: '1px solid var(--e-line, #333)',
              minHeight: 72,
            }}
          >
            {audioTrack && (
              <>
                <AudioTrack trackRef={audioTrack} />
                <BarVisualizer state={state} trackRef={audioTrack} barCount={18} />
              </>
            )}
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
    >
      <CallBody callId={callId} onLog={onLog} onEnded={onEnded} />
    </UpliftAIRoom>
  );
}

function ts() {
  return new Date().toLocaleTimeString();
}
