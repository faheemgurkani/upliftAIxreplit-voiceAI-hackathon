import { DemoSession } from "@/components/DemoSession";

export default function DemoPage() {
  return (
    <div className="mx-auto max-w-3xl px-5 py-10 md:px-8 md:py-14">
      <header className="mb-8 animate-fade-up">
        <p className="text-xs uppercase tracking-[0.2em] text-brass-300">
          Browser voice demo
        </p>
        <h1 className="mt-2 font-display text-3xl text-mist-50 md:text-4xl">
          Talk to Gawah
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-mist-300 md:text-base">
          Start a realtime session against the FastAPI backend. Credentials and
          tool-call activity appear below for hackathon debugging.
        </p>
      </header>
      <div className="animate-fade-up-delay">
        <DemoSession />
      </div>
    </div>
  );
}
