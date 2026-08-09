import { useEffect, useMemo, useRef, useState } from 'react';
import {
  RoomAudioRenderer,
  StartAudio,
  UpliftAIRoom,
  useLocalParticipant,
  useTranscriptions,
  useUpliftAIRoom,
  useVoiceAssistant,
} from '@upliftai/assistants-react';
import { buildGawahTools, type ToolEvent } from '@/lib/gawah-tools';
import {
  completeWebSession,
  postWebEvent,
  uploadWebRecording,
  type WebRecordingResponse,
} from '@/lib/api';
import {
  formatDialogueTranscript,
  type DialogueTurn,
} from '@/lib/dialogue';
import { TranscriptChat } from '@/components/transcript-chat';

interface Props {
  token: string;
  wsUrl: string;
  callId: string;
  onLog: (line: string) => void;
  onTool?: (ev: ToolEvent) => void;
  /** Called after hang-up + optional recording→statement pipeline */
  onEnded?: (result?: WebRecordingResponse | null) => void;
}

/**
 * Live WebRTC + continuous witness mic capture + live Agent/Witness dialogue.
 *
 * Do NOT call updateInstruction() with a short blurb — it replaces the full prompt.
 */
function CallBody({
  callId,
  onLog,
  onEnded,
  tools,
}: {
  callId: string;
  onLog: (line: string) => void;
  onEnded?: (result?: WebRecordingResponse | null) => void;
  tools: ReturnType<typeof buildGawahTools>;
}) {
  const { isConnected, agentParticipant, upsertTools } = useUpliftAIRoom();
  const { state, agentTranscriptions } = useVoiceAssistant();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const transcriptions = useTranscriptions();

  const [recSeconds, setRecSeconds] = useState(0);
  const [ending, setEnding] = useState(false);

  const connectedOnce = useRef(false);
  const toolsOnce = useRef(false);
  const recOnce = useRef(false);
  const lastState = useRef<string>('');
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const ownStreamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const mimeRef = useRef('audio/webm');
  const endingRef = useRef(false);
  const dialogueRef = useRef<DialogueTurn[]>([]);

  const localIdentity = localParticipant?.identity;
  const agentIdentity = agentParticipant?.identity;

  /** LiveKit text streams + agent track segments → labelled dialogue */
  const dialogue = useMemo((): DialogueTurn[] => {
    const byId = new Map<string, DialogueTurn>();

    for (const t of transcriptions) {
      const text = (t.text || '').trim();
      if (!text) continue;
      const identity = t.participantInfo?.identity || '';
      const role: DialogueTurn['role'] =
        localIdentity && identity === localIdentity ? 'witness' : 'agent';
      const id = String(t.streamInfo?.id || `${role}-${t.streamInfo?.timestamp}-${text.slice(0, 24)}`);
      byId.set(id, {
        role,
        text,
        id,
        at: Number(t.streamInfo?.timestamp) || Date.now(),
      });
    }

    // Backup: agent mic transcription segments from useVoiceAssistant
    for (const seg of agentTranscriptions || []) {
      const text = (seg.text || '').trim();
      if (!text) continue;
      const id = String(seg.id || `agent-seg-${seg.firstReceivedTime || text.slice(0, 24)}`);
      if (byId.has(id)) {
        byId.set(id, { ...byId.get(id)!, text, role: 'agent' });
      } else {
        byId.set(id, {
          role: 'agent',
          text,
          id,
          at: Number(seg.firstReceivedTime) || Date.now(),
        });
      }
    }

    return Array.from(byId.values()).sort((a, b) => (a.at || 0) - (b.at || 0));
  }, [transcriptions, agentTranscriptions, localIdentity, agentIdentity]);

  useEffect(() => {
    dialogueRef.current = dialogue;
  }, [dialogue]);

  // Dedicated continuous witness capture → STT → §161 fields on hang-up
  useEffect(() => {
    if (!isConnected || recOnce.current) return;
    recOnce.current = true;

    void (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        ownStreamRef.current = stream;
        const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm';
        mimeRef.current = mime;
        const recorder = new MediaRecorder(stream, { mimeType: mime });
        chunksRef.current = [];
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        mediaRef.current = recorder;
        recorder.start(1000);
        setRecSeconds(0);
        timerRef.current = window.setInterval(() => setRecSeconds((s) => s + 1), 1000);
        onLog(`[${ts()}] Witness mic recording — everything you say is captured`);
        void postWebEvent(callId, {
          type: 'witness_recording_started',
          detail: 'Continuous mic capture for statement structuring',
          status: 'connected',
        });
      } catch (err) {
        recOnce.current = false;
        onLog(
          `[${ts()}] Mic record warning: ${
            err instanceof Error ? err.message : 'permission denied'
          }`,
        );
      }
    })();

    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [isConnected, callId, onLog]);

  useEffect(() => {
    if (isConnected && !connectedOnce.current) {
      connectedOnce.current = true;
      onLog(`[${ts()}] Live web call connected — speak your statement; we record + structure it`);
      void postWebEvent(callId, {
        type: 'webrtc_connected',
        detail: 'Uplift WebRTC room connected',
        status: 'connected',
      });
    }
  }, [isConnected, callId, onLog]);

  useEffect(() => {
    if (!isConnected || toolsOnce.current) return;
    if (typeof upsertTools !== 'function') return;
    toolsOnce.current = true;
    void (async () => {
      try {
        await upsertTools(tools as never);
        onLog(`[${ts()}] Tool handlers registered (${tools.length})`);
      } catch (err) {
        onLog(
          `[${ts()}] Tool sync warning: ${
            err instanceof Error ? err.message : 'unknown'
          }`,
        );
      }
    })();
  }, [isConnected, upsertTools, tools, onLog]);

  const agentLogged = useRef<string | null>(null);
  useEffect(() => {
    const id = agentParticipant?.identity;
    if (!id || agentLogged.current === id) return;
    agentLogged.current = id;
    onLog(`[${ts()}] Agent joined: ${id}`);
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

  const stopAndUpload = async () => {
    if (endingRef.current) return;
    endingRef.current = true;
    setEnding(true);

    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }

    const turns = dialogueRef.current;
    onLog(
      `[${ts()}] Ending call — uploading recording + ${turns.length} dialogue turn(s)…`,
    );
    void postWebEvent(callId, {
      type: 'webrtc_disconnect',
      detail: `User ended call; dialogue turns=${turns.length}`,
      status: 'processing',
    });

    let result: WebRecordingResponse | null = null;
    const recorder = mediaRef.current;

    try {
      if (recorder && recorder.state !== 'inactive') {
        const blob = await new Promise<Blob>((resolve) => {
          recorder.onstop = () => {
            resolve(new Blob(chunksRef.current, { type: mimeRef.current }));
          };
          recorder.stop();
        });

        if (blob.size > 0) {
          result = await uploadWebRecording(callId, blob, {
            language: 'ur',
            participantName: 'Witness',
            filename: `witness-${callId}.webm`,
            dialogue: turns,
          });
          onLog(
            `[${ts()}] Statement structured · ref ${result.ref_code || '—'} · dialogue ${
              result.dialogue?.length || turns.length
            } turns`,
          );
        } else {
          onLog(`[${ts()}] Recording empty — completing session without upload`);
        }
      } else {
        onLog(`[${ts()}] No recorder — completing session`);
      }
    } catch (err) {
      onLog(
        `[${ts()}] Upload/structure error: ${
          err instanceof Error ? err.message : 'unknown'
        }`,
      );
    }

    // Ensure result carries dialogue for ended UI even if backend omitted it
    if (result && !result.dialogue?.length && turns.length) {
      result = {
        ...result,
        dialogue: turns,
        transcript: result.transcript || formatDialogueTranscript(turns),
      };
    } else if (!result && turns.length) {
      result = {
        ok: true,
        call_id: callId,
        dialogue: turns,
        transcript: formatDialogueTranscript(turns),
      };
    }

    try {
      await completeWebSession(callId);
    } catch {
      // non-fatal
    }

    ownStreamRef.current?.getTracks().forEach((t) => t.stop());
    ownStreamRef.current = null;

    onEnded?.(result);
  };

  const agentLabel =
    ending
      ? 'Saving your statement…'
      : state === 'speaking'
        ? 'Agent speaking…'
        : state === 'thinking'
          ? 'Agent thinking…'
          : state === 'listening'
            ? 'Listening — speak your statement'
            : 'Connecting…';

  const mm = String(Math.floor(recSeconds / 60)).padStart(2, '0');
  const ss = String(recSeconds % 60).padStart(2, '0');

  return (
    <div className="live-call-layout">
      <div className="bento live-call-panel">
        <div className="bento-h">
          <span className="dot dot-o" />
          LIVE.WEB.CALL · WITNESS RECORDING
        </div>
        <div className="bento-body">
          <p style={{ fontSize: 15, marginBottom: 16, lineHeight: 1.6 }}>
            You are the witness. Speak naturally — we capture the live dialogue (agent + you) and
            your mic for the §161 fields. Allow mic + agent audio if the browser asks.
          </p>

          <RoomAudioRenderer />

          <div className="call-status-row">
            <div className="live-pill">
              <span className="pulse-dot" />
              {isConnected ? agentLabel.toUpperCase() : 'CONNECTING…'}
            </div>
            {isConnected && !ending && (
              <div className="call-rec-meta">REC · {mm}:{ss}</div>
            )}
          </div>

          <StartAudio label="Tap to hear the agent" className="call-start-audio" />

          <div className="call-controls" role="group" aria-label="Call controls">
            <button
              type="button"
              className="cta-btn cta-ghost"
              disabled={!isConnected || ending}
              aria-pressed={isMicrophoneEnabled}
              onClick={() => {
                void localParticipant?.setMicrophoneEnabled(!isMicrophoneEnabled);
              }}
            >
              <span className="cta-sq">{isMicrophoneEnabled ? '●' : '○'}</span>
              <span className="cta-lbl">{isMicrophoneEnabled ? 'Mic on' : 'Mic off'}</span>
            </button>
            <button
              type="button"
              className="cta-btn"
              disabled={ending || !isConnected}
              onClick={() => void stopAndUpload()}
            >
              <span className="cta-sq">■</span>
              <span className="cta-lbl">{ending ? 'Saving…' : 'End call'}</span>
            </button>
          </div>
        </div>
      </div>

      <aside className="live-call-transcript">
        <TranscriptChat
          turns={dialogue}
          live
          title="لائیو بات چیت"
          emptyHint="گفتگو یہاں ظاہر ہوگی — ایجنٹ اور گواہ کی سطریں اردو میں…"
        />
      </aside>
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
