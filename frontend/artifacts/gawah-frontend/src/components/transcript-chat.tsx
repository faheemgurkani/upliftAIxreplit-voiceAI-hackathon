import { useEffect, useRef } from 'react';
import type { DialogueTurn } from '@/lib/dialogue';

interface Props {
  turns: DialogueTurn[];
  /** Plain STT fallback when no labelled dialogue */
  fallbackText?: string;
  title?: string;
  live?: boolean;
  emptyHint?: string;
}

/**
 * Agent ↔ Witness dialogue as a chat transcript (full text, no truncation).
 * Live mode keeps a fixed-height scrollable box and follows the latest turn.
 */
export function TranscriptChat({
  turns,
  fallbackText,
  title = 'Dialogue',
  live = false,
  emptyHint = 'Dialogue will appear here as you and the agent speak…',
}: Props) {
  const hasTurns = turns.length > 0;
  const hasFallback = Boolean(fallbackText?.trim());
  const scrollerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!live) return;
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [live, turns, fallbackText]);

  if (!hasTurns && !hasFallback) {
    return (
      <div className={`find-panel transcript-preview${live ? ' transcript-preview--live' : ''}`}>
        <div className="find-head">
          <span className="find-n">{live ? 'LIVE' : 'CHAT'}</span>
          <span className="find-title">{title}</span>
        </div>
        <div
          ref={scrollerRef}
          className="find-body activity-log-empty transcript-chat"
        >
          {emptyHint}
        </div>
      </div>
    );
  }

  return (
    <div className={`find-panel transcript-preview${live ? ' transcript-preview--live' : ''}`}>
      <div className="find-head">
        <span className="find-n">{live ? 'LIVE' : 'CHAT'}</span>
        <span className="find-title">{title}</span>
      </div>
      <div
        ref={scrollerRef}
        className="transcript-chat"
        role="log"
        aria-live={live ? 'polite' : undefined}
      >
        {hasTurns
          ? turns.map((turn) => (
              <div
                key={turn.id}
                className={`transcript-bubble transcript-bubble--${turn.role}`}
              >
                <div className="transcript-bubble-role">
                  {turn.role === 'agent' ? 'ایجنٹ' : 'گواہ'}
                </div>
                <div className="transcript-bubble-text" dir="auto" lang="ur">
                  {turn.text}
                </div>
              </div>
            ))
          : (
              <div className="transcript-bubble transcript-bubble--witness">
                <div className="transcript-bubble-role">گواہ</div>
                <div className="transcript-bubble-text" dir="auto" lang="ur">
                  {fallbackText}
                </div>
              </div>
            )}
      </div>
    </div>
  );
}
