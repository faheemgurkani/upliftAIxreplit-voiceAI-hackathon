import type { ProtectionReferral } from "@/lib/types";

export function WitnessProtection({
  protection,
}: {
  protection?: ProtectionReferral | null;
}) {
  const status = protection?.status || "none";
  const isActive = status !== "none" && !!protection;

  return (
    <section className="glass-panel rounded-xl p-5 md:p-6">
      <h2 className="mb-4 font-display text-xl text-mist-50">Witness protection</h2>
      {!isActive ? (
        <p className="text-sm text-mist-200/80">
          No protection referral generated for this statement.
        </p>
      ) : (
        <div className="space-y-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-mist-400">Status:</span>
            <span className="rounded border border-red-400/35 bg-red-500/15 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-red-300">
              {status.replace(/_/g, " ")}
            </span>
          </div>
          {protection?.applicable_act && (
            <p>
              <span className="text-mist-400">Applicable act: </span>
              <span className="text-mist-100">{protection.applicable_act}</span>
            </p>
          )}
          {protection?.grounds && protection.grounds.length > 0 && (
            <p>
              <span className="text-mist-400">Grounds: </span>
              <span className="text-mist-100">{protection.grounds.join("; ")}</span>
            </p>
          )}
          <div className="flex flex-wrap gap-3 pt-2">
            {protection?.referral_pdf_url ? (
              <a
                href={protection.referral_pdf_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-brass-400/40 bg-brass-400/10 px-3 py-2 text-sm text-brass-300 transition-colors duration-300 hover:bg-brass-400/20"
              >
                Download referral PDF
              </a>
            ) : (
              <span className="rounded-md border border-white/10 px-3 py-2 text-sm text-mist-400">
                Referral PDF pending
              </span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
