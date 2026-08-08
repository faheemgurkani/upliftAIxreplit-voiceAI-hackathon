import Link from "next/link";

export default function LandingPage() {
  return (
    <section className="relative flex min-h-screen flex-col justify-center px-5 pb-16 pt-28 md:px-8">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -left-24 top-24 h-72 w-72 animate-pulse-soft rounded-full bg-moss-500/20 blur-3xl" />
        <div className="absolute bottom-16 right-0 h-80 w-80 rounded-full bg-brass-400/10 blur-3xl" />
        <div
          className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-brass-400/40 to-transparent"
          style={{
            backgroundSize: "200% 100%",
          }}
        />
      </div>

      <div className="relative mx-auto w-full max-w-4xl">
        <p className="animate-fade-up font-display text-6xl tracking-tight text-mist-50 sm:text-7xl md:text-8xl lg:text-9xl">
          Gawah
        </p>
        <h1 className="animate-fade-up-delay mt-6 max-w-2xl font-display text-2xl leading-snug text-mist-100 sm:text-3xl md:text-4xl text-balance">
          Voice witness statements, structured for counsel.
        </h1>
        <p className="animate-fade-up-late mt-5 max-w-xl text-base leading-relaxed text-mist-300 sm:text-lg">
          Record CrPC Section 161 examinations in Urdu, Punjabi, and Pashto —
          then review consistency and multi-witness intelligence before court.
        </p>
        <div className="animate-fade-up-late mt-10 flex flex-wrap gap-3">
          <Link
            href="/demo"
            className="rounded-md bg-brass-400 px-5 py-3 text-sm font-medium text-ink-950 transition-all duration-300 hover:bg-brass-300 hover:shadow-[0_0_24px_rgba(212,168,75,0.25)]"
          >
            Try the demo
          </Link>
          <Link
            href="/dashboard"
            className="rounded-md border border-white/20 bg-white/5 px-5 py-3 text-sm font-medium text-mist-50 transition-all duration-300 hover:border-brass-400/40 hover:bg-white/10"
          >
            Open dashboard
          </Link>
        </div>
      </div>
    </section>
  );
}
