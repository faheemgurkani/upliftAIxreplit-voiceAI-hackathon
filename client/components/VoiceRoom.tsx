"use client";

import {
  AudioTrack,
  BarVisualizer,
  DisconnectButton,
  TrackToggle,
  UpliftAIRoom,
  useUpliftAIRoom,
  useVoiceAssistant,
} from "@upliftai/assistants-react";
import { Track } from "livekit-client";

function RoomBody({ onToolEvent }: { onToolEvent: (msg: string) => void }) {
  const { isConnected, agentParticipant } = useUpliftAIRoom();
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span
          className={`inline-flex h-2.5 w-2.5 rounded-full ${
            isConnected ? "bg-moss-400 animate-pulse-soft" : "bg-mist-400"
          }`}
        />
        <span className="text-mist-200">
          {isConnected ? "Connected to Gawah agent" : "Connecting…"}
        </span>
        <span className="text-mist-400">Agent state: {state}</span>
        {agentParticipant && (
          <span className="text-mist-400">{agentParticipant.identity}</span>
        )}
      </div>
      {audioTrack && (
        <div className="rounded-lg border border-white/10 bg-ink-950/50 p-4">
          <BarVisualizer state={state} trackRef={audioTrack} className="h-16" />
          <AudioTrack trackRef={audioTrack} />
        </div>
      )}
      <div className="flex flex-wrap gap-3">
        <TrackToggle
          source={Track.Source.Microphone}
          className="rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm text-mist-100 transition-colors duration-300 hover:border-brass-400/40"
        />
        <DisconnectButton className="rounded-md border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300 transition-colors duration-300 hover:bg-red-500/20">
          Disconnect
        </DisconnectButton>
      </div>
      <button
        type="button"
        onClick={() =>
          onToolEvent(
            `[${new Date().toLocaleTimeString()}] Listening for tool calls (save_witness_statement, assess_protection_need, …)`
          )
        }
        className="text-xs text-mist-400 underline-offset-2 hover:text-brass-300 hover:underline"
      >
        Ping tool-status listener
      </button>
    </div>
  );
}

export default function VoiceRoom({
  token,
  wsUrl,
  onToolEvent,
}: {
  token: string;
  wsUrl: string;
  onToolEvent: (msg: string) => void;
}) {
  return (
    <UpliftAIRoom token={token} serverUrl={wsUrl} connect audio video={false}>
      <RoomBody onToolEvent={onToolEvent} />
    </UpliftAIRoom>
  );
}
