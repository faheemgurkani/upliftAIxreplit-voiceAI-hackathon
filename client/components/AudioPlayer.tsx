"use client";

export function AudioPlayer({ src, label }: { src?: string | null; label?: string }) {
  if (!src) {
    return (
      <section className="glass-panel rounded-xl p-5 md:p-6">
        <h2 className="mb-2 font-display text-xl text-mist-50">
          {label || "Readback audio"}
        </h2>
        <p className="text-sm text-mist-400">No readback audio available.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel rounded-xl p-5 md:p-6">
      <h2 className="mb-4 font-display text-xl text-mist-50">
        {label || "Readback audio"}
      </h2>
      <audio controls preload="metadata" className="w-full" src={src}>
        Your browser does not support audio playback.
      </audio>
    </section>
  );
}
