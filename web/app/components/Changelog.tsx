type Tag = "new" | "fix" | "improve";
type Importance = "" | "crit" | "high";

type Entry = {
  version: string;
  date: string;
  title: string;
  tags: Tag[];
  items: { imp: Importance; impLabel: string; body: React.ReactNode }[];
};

const entries: Entry[] = [
  {
    version: "v0.2.3",
    date: "April 2026",
    title: "Production hardening",
    tags: ["fix", "improve"],
    items: [
      { imp: "crit", impLabel: "Critical", body: <><strong>Stream escalation gap closed</strong> — stream() now checks self_harm and crisis scores before yielding any tokens; emergency stops the stream entirely.</> },
      { imp: "high", impLabel: "High",     body: <><strong>Async classifier</strong> — wrapped in asyncio.to_thread(); no longer blocks the event loop on Ollama calls.</> },
      { imp: "high", impLabel: "High",     body: <><strong>Safe fallback on malformed JSON</strong> — classifier degrades gracefully instead of crashing the request.</> },
      { imp: "",     impLabel: "Medium",   body: <><strong>SR_CUSTOM_ROUTING env var</strong> — JSON-encoded per-category routing overrides without code changes.</> },
      { imp: "",     impLabel: "Medium",   body: <><strong>Rate limiting + input length</strong> — 60 req/min per IP; 10,000-char input cap enforced at router and server.</> },
      { imp: "",     impLabel: "Low",      body: <><strong>Demographic skip + 0o600 transcripts</strong> — catch-all category no longer wins routing; transcripts owner-only.</> },
    ],
  },
  {
    version: "v0.2.2",
    date: "April 2026",
    title: "Bias rephrasing + structured CLI output",
    tags: ["new", "improve"],
    items: [
      { imp: "", impLabel: "New",     body: <><strong>Bias rephrasing</strong> — classifier returns rephrased_text with original, rephrased, changes_made, meaning_preserved, and meaning_change_risk.</> },
      { imp: "", impLabel: "New",     body: <><strong>JSON CLI output</strong> — safetyrouter route returns structured JSON by default. The --json-output flag is removed.</> },
      { imp: "", impLabel: "Improve", body: <><strong>Server hardening</strong> — thread-safe double-checked locking for router init and streaming escalation in HTTP /route.</> },
    ],
  },
  {
    version: "v0.2.0",
    date: "March 2026",
    title: "Mental health risk + crisis escalation",
    tags: ["new"],
    items: [
      { imp: "", impLabel: "New", body: <><strong>4 mental health signals</strong> — self_harm, severe_distress, existential_crisis, emotional_dependency, all scored locally.</> },
      { imp: "", impLabel: "New", body: <><strong>Two-tier escalation</strong> — EMERGENCY skips LLM entirely; HELPLINE appends crisis line to LLM response.</> },
      { imp: "", impLabel: "New", body: <><strong>15-country crisis database</strong> — emergency numbers, helplines, and webchat links. Session transcripts saved to ~/.safetyrouter/sessions/.</> },
      { imp: "", impLabel: "New", body: <><strong>FastAPI server</strong> — /route, /classify, /health, /routing-table endpoints.</> },
    ],
  },
  {
    version: "v0.1.0",
    date: "February 2026",
    title: "Initial release",
    tags: ["new"],
    items: [
      { imp: "", impLabel: "New", body: <><strong>9 bias categories</strong> classified locally with gemma3n:e2b via Ollama.</> },
      { imp: "", impLabel: "New", body: <><strong>Routing table</strong> backed by LLM Bias Evaluator benchmark (270 samples).</> },
      { imp: "", impLabel: "New", body: <><strong>5 providers</strong> — OpenAI, Anthropic, Google, Groq, Ollama. Python SDK + CLI + pip package.</> },
    ],
  },
];

export function Changelog() {
  return (
    <section className="section" id="changelog" style={{ paddingTop: "5rem" }}>
      <div className="section-label">Changelog</div>
      <h2>
        What&apos;s <em>new</em>.
      </h2>
      <p className="section-intro">
        SafetyRouter follows semantic versioning. All changes are backwards-compatible
        within a minor version.
      </p>

      <div className="changelog-list">
        {entries.map((e) => (
          <div className="changelog-row" key={e.version}>
            <div className="cl-meta">
              <div className="cl-version">{e.version}</div>
              <div className="cl-date">{e.date}</div>
            </div>
            <div className="cl-body">
              <h3>{e.title}</h3>
              <div className="cl-tags">
                {e.tags.map((t) => (
                  <span className={`cl-tag ${t}`} key={t}>{t}</span>
                ))}
              </div>
              <ul className="cl-items">
                {e.items.map((it, i) => (
                  <li key={i}>
                    <span className={`imp ${it.imp}`}>{it.impLabel}</span>
                    <span>{it.body}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
