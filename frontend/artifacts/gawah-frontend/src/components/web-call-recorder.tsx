import { useEffect, useRef, useState } from 'react';
import {
  completeWebSession,
  postWebEvent,
  uploadWebRecording,
  type WebRecordingResponse,
} from '@/lib/api';

type RecState = 'idle' | 'starting' | 'live' | 'ending' | 'done' | 'error';

interface Props {
  callId: string;
  onLog: (line: string) => void;
  onProcessed?: (result: WebRecordingResponse) => void;
  onStatus?: (status: string) => void;
  /** Fired immediately when End call is pressed (show processing UI) */
  onProcessing?: () => void;
  /** Auto-open mic when mounted (call-like). Default true. */
  autoStart?: boolean;
}

/**
 * Offline / fallback "web call": mic opens immediately (like answering a call).
 * Continuous capture until End call — no separate Record button.
 * Not the interactive Gawah agent — use only when WebRTC live room is unavailable.
 */
export function WebCallRecorder({
  callId,
  onLog,
  onProcessed,
  onStatus,
  onProcessing,
  autoStart = true,
}: Props) {
  const [recState, setRecState] = useState<RecState>(autoStart ? 'starting' : 'idle');
  const [error, setError] = useState<string | null>(null);
  const [seconds, setSeconds] = useState(0);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const mimeRef = useRef('audio/webm');
  const startedRef = useRef(false);

  useEffect(() => {
    if (!autoStart || startedRef.current) return;
    startedRef.current = true;
    void start();
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount once
  }, [autoStart]);

  const start = async () => {
    setError(null);
    setRecState('starting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
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
      setRecState('live');
      setSeconds(0);
      timerRef.current = window.setInterval(() => setSeconds((s) => s + 1), 1000);
      onStatus?.('connected');
      onLog(`[${ts()}] Mic live — speak naturally (fallback web call)`);
      await postWebEvent(callId, {
        type: 'call_answered',
        detail: 'Continuous mic capture started (offline fallback)',
        status: 'connected',
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Microphone permission denied';
      setError(msg);
      setRecState('error');
      onLog(`[${ts()}] Mic error: ${msg}`);
      await postWebEvent(callId, {
        type: 'mic_error',
        detail: msg,
        status: 'failed',
      }).catch(() => undefined);
    }
  };

  const endCall = () => {
    if (recState !== 'live') return;
    setRecState('ending');
    onStatus?.('processing');
    onProcessing?.();
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    const recorder = mediaRef.current;
    if (recorder && recorder.state === 'recording') {
      recorder.onstop = () => {
        void finishUpload();
      };
      recorder.stop();
    } else {
      void finishUpload();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  const finishUpload = async () => {
    onLog(`[${ts()}] Call ended — processing audio…`);
    await postWebEvent(callId, {
      type: 'call_hangup',
      detail: `Duration ~${seconds}s`,
      status: 'processing',
    }).catch(() => undefined);

    try {
      const blob = new Blob(chunksRef.current, {
        type: mimeRef.current.split(';')[0],
      });
      if (blob.size < 200) {
        throw new Error('No audio captured — stay on the call a few seconds and speak.');
      }
      const result = await uploadWebRecording(callId, blob, {
        language: 'ur',
        participantName: 'Witness',
        filename: `web-call-${callId}.webm`,
      });
      setRecState('done');
      onStatus?.('completed');
      onLog(
        `[${ts()}] Processed · ref ${result.ref_code || '—'} · STT ${
          result.stt_ok ? 'ok' : 'fallback'
        }`,
      );
      onProcessed?.(result);
      await completeWebSession(callId).catch(() => undefined);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Processing failed';
      setError(msg);
      setRecState('error');
      onStatus?.('failed');
      onLog(`[${ts()}] Error: ${msg}`);
      await postWebEvent(callId, {
        type: 'processing_failed',
        detail: msg,
        status: 'failed',
      }).catch(() => undefined);
    }
  };

  return (
    <div className="bento">
      <div className="bento-h">
        <span className="dot dot-o" />
        WEB.CALL · CONTINUOUS MIC
      </div>
      <div className="bento-body">
        <p style={{ fontSize: 15, marginBottom: 16, lineHeight: 1.6 }}>
          Mic opens like answering a call — speak your testimony, then hang up. Audio is
          processed when the call ends (Uplift live room unavailable).
        </p>
        <div className="live-pill" style={{ marginBottom: 16 }}>
          <span className="pulse-dot" />
          {recState === 'live'
            ? `ON CALL ${seconds}s`
            : recState === 'ending'
              ? 'HANGING UP…'
              : recState === 'done'
                ? 'CALL ENDED'
                : recState === 'starting'
                  ? 'ANSWERING…'
                  : recState === 'idle'
                    ? 'READY — START WHEN NEEDED'
                    : 'ERROR'}
        </div>
        {error && (
          <div className="insight" style={{ borderColor: 'var(--e-warn)', marginBottom: 16 }}>
            <span className="insight-lbl">ERROR</span>
            {error}
          </div>
        )}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {recState === 'idle' && (
            <button
              type="button"
              className="cta-btn cta-ghost"
              onClick={() => {
                startedRef.current = true;
                void start();
              }}
            >
              <span className="cta-sq">●</span>
              <span className="cta-lbl">Start mic upload</span>
            </button>
          )}
          {recState === 'live' && (
            <button type="button" className="cta-btn" onClick={endCall}>
              <span className="cta-sq" style={{ background: 'var(--e-warn)' }}>
                ■
              </span>
              <span className="cta-lbl">End call</span>
            </button>
          )}
          {recState === 'error' && (
            <button type="button" className="cta-btn" onClick={() => void start()}>
              <span className="cta-sq">●</span>
              <span className="cta-lbl">Retry call</span>
            </button>
          )}
          {recState === 'ending' && (
            <div className="state-panel" style={{ borderStyle: 'solid', padding: 12 }}>
              <div className="spinner" />
              <div className="pager-meta">Processing testimony</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ts() {
  return new Date().toLocaleTimeString();
}
