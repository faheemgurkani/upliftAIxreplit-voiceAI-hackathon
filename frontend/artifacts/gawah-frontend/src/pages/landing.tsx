import { useEffect } from 'react';
import { Link } from 'wouter';
import { motion, useScroll, useSpring } from 'framer-motion';
import { PageShell } from '@/components/layout/page-shell';
import { Reveal } from '@/components/landing/reveal';
import { SectionRail } from '@/components/landing/section-rail';

export default function LandingPage() {
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 28, mass: 0.35 });

  useEffect(() => {
    const unsub = progress.on('change', (v) => {
      document.documentElement.style.setProperty('--land-progress', String(v));
    });
    return () => {
      unsub();
      document.documentElement.style.removeProperty('--land-progress');
    };
  }, [progress]);

  return (
    <PageShell>
      <div className="land dot-bg">
        <div className="land-progress" aria-hidden />
        <SectionRail />

        {/* ── Hero ── */}
        <section className="land-hero">
          <div className="land-hero-inner">
            <div>
              <div className="land-kicker">
                <span
                  className="accent-sq"
                  style={{ width: 12, height: 12, background: 'var(--e-accent)', display: 'inline-block' }}
                />
                // SECTION : LANDING
              </div>

              <motion.div
                className="land-urdu"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.05 }}
              >
                گواہ
              </motion.div>

              <motion.h1
                className="section-title glitch"
                style={{ fontSize: 'min(92px, 16vw)', marginTop: 8 }}
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.55, delay: 0.12 }}
              >
                GAWAH
              </motion.h1>

              <motion.p
                className="land-tagline"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                The Witness That Cannot Be Silenced
              </motion.p>

              <div className="land-rule-row">
                <div className="e-rule" style={{ width: 60 }} />
                <div
                  style={{
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                    fontWeight: 600,
                    fontSize: 13,
                  }}
                >
                  Phone-only CrPC §161 · Pakistan
                </div>
              </div>

              <div className="land-cta-row">
                <Link href="/demo" className="cta-btn">
                  <span className="cta-sq">●</span>
                  <span className="cta-lbl">Start Demo</span>
                </Link>
                <Link href="/dashboard" className="cta-btn cta-ghost">
                  <span className="cta-sq">→</span>
                  <span className="cta-lbl">Open Dashboard</span>
                </Link>
              </div>
            </div>

            <motion.div
              style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.22 }}
            >
              <div className="bento">
                <div className="bento-h">
                  <span className="dot dot-o" />
                  PRODUCT META
                </div>
                <div className="bento-body kv-grid">
                  <div className="kv-k">CHANNEL</div>
                  <div className="kv-v">PSTN PHONE · NO APP</div>
                  <div className="kv-k">DOMAIN</div>
                  <div className="kv-v">CRIMINAL JUSTICE</div>
                  <div className="kv-k">COMPLIANCE</div>
                  <div className="kv-v">CRPC §161 / PDPA 2023</div>
                  <div className="kv-k">STATUS</div>
                  <div className="kv-v text-e-accent" style={{ fontWeight: 'bold' }}>
                    LIVE PROTOTYPE
                  </div>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div className="hud">
                  <div className="hud-k">Conviction Rate</div>
                  <div className="hud-v accent">8.66%</div>
                </div>
                <div className="hud">
                  <div className="hud-k">Mission</div>
                  <div className="hud-v">TRUTH</div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <div className="land-band">
          <div className="marquee" style={{ border: 'none' }}>
            <div className="marquee-track">
              GO ON RECORD WITHOUT GOING ON RECORD <span className="marquee-star">▣</span> PHONE-ONLY
              · NO SMARTPHONE <span className="marquee-star">▣</span> CRPC §161 · PDPA 2023{' '}
              <span className="marquee-star">▣</span>
              GO ON RECORD WITHOUT GOING ON RECORD <span className="marquee-star">▣</span> PHONE-ONLY
              · NO SMARTPHONE <span className="marquee-star">▣</span> CRPC §161 · PDPA 2023{' '}
              <span className="marquee-star">▣</span>
            </div>
          </div>
        </div>

        {/* ── Problem ── */}
        <section id="problem" className="land-chapter">
          <Reveal>
            <header className="land-chapter-head">
              <h2 className="land-chapter-title">
                WHY WITNESSES.<span className="accent">WITHDRAW</span>
              </h2>
              <p className="land-chapter-sub">
                Two failures — silence, and lost paper. Gawah answers both without asking the
                witness to walk into a station.
              </p>
            </header>
          </Reveal>

          <div className="land-split">
            <Reveal delay={0.05}>
              <div className="bento" style={{ height: '100%' }}>
                <div className="bento-h">
                  <span className="dot dot-o" />
                  PROBLEM.A · SILENCE
                </div>
                <div className="bento-body page-stack" style={{ gap: 16 }}>
                  <p style={{ margin: 0, lineHeight: 1.65 }}>
                    Many witnesses never report at all. Fear of exposure is the barrier — not
                    ignorance of the crime.
                  </p>
                  <p className="text-e-muted" style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>
                    Answer: anonymity by design. Reference code + pseudonym. The dashboard shows the
                    statement — not the caller ID.
                  </p>
                </div>
              </div>
            </Reveal>
            <Reveal delay={0.12}>
              <div className="bento" style={{ height: '100%' }}>
                <div className="bento-h">
                  <span className="dot dot-k" />
                  PROBLEM.B · LOST REPORTS
                </div>
                <div className="bento-body page-stack" style={{ gap: 16 }}>
                  <p style={{ margin: 0, lineHeight: 1.65 }}>
                    Reports that are filed often disappear — written on paper, in a drawer, in a
                    station the witness is afraid to return to.
                  </p>
                  <p className="text-e-muted" style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>
                    Answer: immutable timestamped record. The reference code is proof the statement
                    was made — independent of police custody.
                  </p>
                </div>
              </div>
            </Reveal>
          </div>
        </section>

        {/* ── Anonymous ── */}
        <section id="anonymous" className="land-chapter">
          <Reveal>
            <header className="land-chapter-head">
              <h2 className="land-chapter-title">
                GO ON RECORD.<span className="accent">ANONYMOUSLY</span>
              </h2>
              <p className="land-chapter-sub">
                Privacy mode is the mechanism — not a cosmetic flag. Identity decoupled from
                statement by design.
              </p>
            </header>
          </Reveal>

          <div className="land-sticky-board">
            <Reveal>
              <div className="land-sticky-col">
                <div className="land-quote">
                  <p>For the first time, a witness can go on record without going on record.</p>
                  <div className="land-quote-meta">// Pitch line · Anonymous witness</div>
                </div>
              </div>
            </Reveal>
            <Reveal delay={0.1}>
              <div className="land-card-stack">
                <div className="bento">
                  <div className="bento-h">
                    <span className="dot dot-o" />
                    ANONYMITY.MECHANISM
                  </div>
                  <div className="bento-body">
                    <ul className="e-bullets">
                      <li>Caller ID masked from dashboard views</li>
                      <li>Pseudonym + 6-character reference code — the durable link</li>
                      <li>No PII without Phase 0 explicit consent</li>
                      <li>Witness may request full decoupling; statement remains</li>
                    </ul>
                  </div>
                </div>
                <div className="bento">
                  <div className="bento-h">
                    <span className="dot dot-k" />
                    WHAT THE DASHBOARD SHOWS
                  </div>
                  <div className="bento-body" style={{ fontSize: 14, lineHeight: 1.65 }}>
                    Statement fields, consistency flags, protection referral — not name, not phone
                    number. Dashboard is built for counsel, not caller identity.
                  </div>
                </div>
              </div>
            </Reveal>
          </div>
        </section>

        {/* ── Intelligence ── */}
        <section id="intelligence" className="land-chapter">
          <Reveal>
            <header className="land-chapter-head">
              <h2 className="land-chapter-title">
                INTELLIGENCE.<span className="accent">LAYER</span>
              </h2>
              <p className="land-chapter-sub">
                Consistency analysis on every call record — then multi-witness cluster depth when
                neighbours describe the same incident. For counsel preparation. Never lie detection.
                Never court corroboration.
              </p>
            </header>
          </Reveal>

          <div className="land-split">
            <Reveal delay={0.05}>
              <div className="bento" style={{ height: '100%' }}>
                <div className="bento-h">
                  <span className="dot dot-o" />
                  PER.CALL · CONSISTENCY
                </div>
                <div className="bento-body page-stack" style={{ gap: 16 }}>
                  <p style={{ margin: 0, lineHeight: 1.65 }}>
                    Intra-statement analysis on a single witness record. Surfaces internal
                    contradictions so counsel can resolve them before the contradiction surface
                    reaches trial under CrPC §162.
                  </p>
                  <ul className="e-bullets">
                    <li>
                      Real-time during the call — agent flags clear conflicts as the witness speaks
                    </li>
                    <li>
                      Post-call hybrid pass — deeper claim-pair analysis on the saved narrative
                    </li>
                    <li>
                      Typed flags: temporal · spatial · identity · sequence · sensory · numerical
                    </li>
                    <li>Side-by-side A/B quotes + score on the statement dashboard — not intent scoring</li>
                  </ul>
                </div>
              </div>
            </Reveal>
            <Reveal delay={0.12}>
              <div className="bento" style={{ height: '100%' }}>
                <div className="bento-h">
                  <span className="dot dot-k" />
                  CLUSTER · CORROBORATION
                </div>
                <div className="bento-body page-stack" style={{ gap: 16 }}>
                  <p style={{ margin: 0, lineHeight: 1.65 }}>
                    When multiple voices describe the same incident, Gawah groups them into an
                    incident cluster and maps field-level agreement — who, what, when, where, how —
                    so lawyers stop cross-referencing by hand.
                  </p>
                  <ul className="e-bullets">
                    <li>Automatic clustering by time, place, and overlapping narrative</li>
                    <li>
                      Field map: agreement · partial · conflict · collusion warning
                    </li>
                    <li>
                      Composite corroboration score as a preparedness instrument — not evidence
                    </li>
                    <li>
                      Near-identical phrasing triggers collusion caution, not a perfect score
                    </li>
                  </ul>
                </div>
              </div>
            </Reveal>
          </div>

          <Reveal delay={0.1}>
            <div className="land-feature-row" style={{ marginTop: 20 }}>
              <article className="land-feature">
                <span className="idx">LIVE</span>
                <h3>During the call</h3>
                <p>
                  Obvious contradictions are flagged in-session so the readback step can tighten the
                  record before confirmation.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">DEPTH</span>
                <h3>After the call</h3>
                <p>
                  Background consistency + corroboration jobs enrich the statement and any linked
                  cluster for the dashboard.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">MAP</span>
                <h3>Cluster detail</h3>
                <p>
                  Field-by-field conflict map shows exactly what counsel must brief or investigate
                  before court appearance.
                </p>
              </article>
            </div>
          </Reveal>

          <Reveal delay={0.14}>
            <div className="insight" style={{ marginTop: 24 }}>
              <span className="insight-lbl">§162 BOUNDARY</span>
              Pre-litigation intelligence only — not admissible corroboration under CrPC Section 162.
              Scores prepare lawyers and reviewers; they do not replace in-court testimony.
            </div>
          </Reveal>

          <Reveal delay={0.18}>
            <div className="land-cta-row" style={{ marginTop: 24 }}>
              <Link href="/clusters" className="cta-btn">
                <span className="cta-sq">▣</span>
                <span className="cta-lbl">View Clusters</span>
              </Link>
              <Link href="/dashboard" className="cta-btn cta-ghost">
                <span className="cta-sq">→</span>
                <span className="cta-lbl">Statement Flags</span>
              </Link>
            </div>
          </Reveal>
        </section>

        {/* ── Legal ── */}
        <section id="legal" className="land-chapter">
          <Reveal>
            <header className="land-chapter-head">
              <h2 className="land-chapter-title">
                WHY THIS.<span className="accent">IS LEGAL</span>
              </h2>
              <p className="land-chapter-sub">
                CrPC 1898 (Pakistan kept the numbering — not India’s BNSS). Gawah makes §161 better
                — it does not invent §164 standing.
              </p>
            </header>
          </Reveal>

          <Reveal delay={0.06}>
            <div className="land-horizon">
              <article className="land-feature">
                <span className="idx">§161</span>
                <h3>Examination</h3>
                <p>
                  Police-level oral exam. Must be as actually made — not a constable’s précis. That
                  gap is what collapses under cross-examination.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">§162</span>
                <h3>Not signed</h3>
                <p>
                  §161 statements must not be signed. Voice confirmation + stored audio is the
                  legally defensible mechanism.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">§164</span>
                <h3>Boundary</h3>
                <p>
                  Magistrate statements carry evidentiary weight. Gawah does not claim that. §161
                  refreshes memory and surfaces inconsistencies.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">PDPA</span>
                <h3>2023 data law</h3>
                <p>
                  Consent before facts. Sensitive category. Purpose-limited. No sale. EU/encrypted
                  demo store → Pakistan-hosted / ap-south-1 in production.
                </p>
              </article>
            </div>
          </Reveal>

          <Reveal delay={0.12}>
            <div className="insight" style={{ marginTop: 24 }}>
              <span className="insight-lbl">SCOPE</span>
              The agent captures facts. It does not give legal advice. Intra-statement consistency
              analysis — never “lie detection.” Punjab WPA 2018 grounds protection referral in
              Punjab; other provinces use their own frameworks.
            </div>
          </Reveal>

          <Reveal delay={0.16}>
            <div className="bento" style={{ marginTop: 20 }}>
              <div className="bento-h">
                <span className="dot dot-r" />
                TECH · COMPLIANCE
              </div>
              <div className="bento-body" style={{ padding: 0, overflowX: 'auto' }}>
                <table className="brutal" style={{ border: 'none' }}>
                  <thead>
                    <tr>
                      <th>Layer</th>
                      <th>Instrument</th>
                      <th>How Gawah meets it</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="first">Procedure</td>
                      <td>CrPC §§161–162</td>
                      <td>Verbatim §161; voice confirm (not signed)</td>
                    </tr>
                    <tr>
                      <td className="first">Data compliance</td>
                      <td>PDPA 2023</td>
                      <td>Consent in Phase 0; no PII without explicit consent</td>
                    </tr>
                    <tr>
                      <td className="first">Protection</td>
                      <td>Punjab WPA 2018+</td>
                      <td>Auto-referral; provincial routing</td>
                    </tr>
                    <tr>
                      <td className="first">Analysis</td>
                      <td>Consistency engine</td>
                      <td>Contradiction flags for counsel — not intent scoring</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </Reveal>
        </section>

        {/* ── Model ── */}
        <section id="model" className="land-chapter">
          <Reveal>
            <header className="land-chapter-head">
              <h2 className="land-chapter-title">
                SOLD.<span className="accent">TO INSTITUTIONS</span>
              </h2>
              <p className="land-chapter-sub">
                Witnesses never pay. Gawah is sold to the parties who run intake, counsel, and
                justice workflows — NGOs, law firms, government, and legal-aid networks.
              </p>
            </header>
          </Reveal>

          <Reveal delay={0.06}>
            <div className="land-feature-row">
              <article className="land-feature">
                <span className="idx">NGO</span>
                <h3>NGOs &amp; legal aid</h3>
                <p>
                  Dashboard seats for statement review, consistency flags, protection referrals, and
                  cluster maps — the launch buyer and grant-aligned path.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">FIRM</span>
                <h3>Law firms</h3>
                <p>
                  Case prep for counsel teams — structured §161 records, conflict surfaces, and
                  multi-witness intelligence without manual cross-referencing.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">GOV</span>
                <h3>Government</h3>
                <p>
                  Provincial and institutional buyers for scaled witness intake, FIR-pipeline
                  partnership, and justice-sector deployment — longer procurement, larger seat.
                </p>
              </article>
            </div>
          </Reveal>

          <Reveal delay={0.12}>
            <div className="land-split" style={{ marginTop: 20 }}>
              <div className="bento">
                <div className="bento-h">
                  <span className="dot dot-o" />
                  MONETIZATION
                </div>
                <div className="bento-body kv-grid">
                  <div className="kv-k">Buyers</div>
                  <div className="kv-v">NGOs · law firms · government · legal aid</div>
                  <div className="kv-k">Price</div>
                  <div className="kv-v">Org / seat licensing — ~$50–200 / month to start</div>
                  <div className="kv-k">Witness</div>
                  <div className="kv-v">Statement capture stays free</div>
                  <div className="kv-k">Scale</div>
                  <div className="kv-v">B2G &amp; firm contracts as the growth lane</div>
                </div>
              </div>
              <div className="bento">
                <div className="bento-h">
                  <span className="dot dot-k" />
                  FUNDING PATH
                </div>
                <div className="bento-body" style={{ fontSize: 14, lineHeight: 1.65 }}>
                  Grant-eligible with UN Women, USAID, and OSF-aligned legal aid for NGO launch.
                  Parallel sales to private law firms and government justice programs fund
                  sustainability — FIR pipeline partnership is the long-term institutional seat.
                </div>
              </div>
            </div>
          </Reveal>
        </section>

        {/* ── Future ── */}
        <section id="future" className="land-chapter">
          <Reveal>
            <header className="land-chapter-head">
              <h2 className="land-chapter-title">
                FUTURE.<span className="accent">WORK</span>
              </h2>
              <p className="land-chapter-sub">
                Roadmap beyond the PSTN MVP — deeper signal analysis, formal deposition workflow,
                and native mobile reach for counsel and witnesses.
              </p>
            </header>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="land-feature-row">
              <article className="land-feature">
                <span className="idx">SIGNAL</span>
                <h3>Lie detection</h3>
                <p>
                  Multi-modal analysis across text and voice — prosody, hesitation, and narrative
                  cues — as an assistive layer for counsel review. Explicitly out of today’s
                  consistency engine; never a credibility verdict.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">PROCESS</span>
                <h3>Deposition management</h3>
                <p>
                  End-to-end conduction and case management for depositions — scheduling, party
                  roles, transcript control, and handoff across lawyers, witnesses, and other
                  participants in the proceeding.
                </p>
              </article>
              <article className="land-feature">
                <span className="idx">MOBILE</span>
                <h3>Native phone apps</h3>
                <p>
                  Dedicated iPhone and Android applications for intake, status, and counsel
                  workflows — alongside the phone-first PSTN channel that remains the core moat.
                </p>
              </article>
            </div>
          </Reveal>

          <Reveal delay={0.14}>
            <div className="insight" style={{ marginTop: 24 }}>
              <span className="insight-lbl">SCOPE</span>
              Today’s product stays phone-only §161 capture with consistency flags and cluster
              intelligence. These items are post-MVP expansions — not shipped claims.
            </div>
          </Reveal>
        </section>

        {/* ── Close ── */}
        <section id="close" className="land-close">
          <div className="land-chapter">
            <Reveal>
              <header className="land-chapter-head">
                <h2 className="land-chapter-title">
                  THE ANONYMOUS.<span className="accent">WITNESS</span>
                </h2>
                <p className="land-chapter-sub">
                  Can go on record without going on record — for the first time. Built for NGOs, law
                  firms, legal aid, and government · Grant-eligible (UN Women, USAID).
                </p>
              </header>
            </Reveal>

            <Reveal delay={0.1}>
              <ul className="e-bullets" style={{ marginTop: 36, maxWidth: 920 }}>
                <li>Voice statement in Urdu / Punjabi — no literacy required</li>
                <li>Witness can remain anonymous — linked to a reference code, not a phone number</li>
                <li>
                  Reviewers see statement, consistency flags, and protection referral on the
                  dashboard
                </li>
                <li>Immutable timestamped record — the lost-report failure mode ends here</li>
              </ul>
            </Reveal>

            <Reveal delay={0.16}>
              <div className="land-cta-row" style={{ marginTop: 36 }}>
                <Link href="/demo" className="cta-btn">
                  <span className="cta-sq">●</span>
                  <span className="cta-lbl">Start Demo</span>
                </Link>
                <Link href="/dashboard" className="cta-btn cta-ghost">
                  <span className="cta-sq">→</span>
                  <span className="cta-lbl">Dashboard</span>
                </Link>
              </div>
            </Reveal>
          </div>
        </section>
      </div>
    </PageShell>
  );
}
