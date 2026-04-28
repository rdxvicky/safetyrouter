type Feature = { n: string; titleHtml: string; desc: React.ReactNode };

const features: Feature[] = [
  {
    n: "01",
    titleHtml: "Bias <em>rephrasing</em>",
    desc: (
      <>
        Every response includes a <code>rephrased_text</code> object — original rewritten
        without bias, with a changelog and meaning-preservation flag. Runs locally at zero cost.
      </>
    ),
  },
  {
    n: "02",
    titleHtml: "Mental health<br/>detection",
    desc: (
      <>
        Four signals scored on every request: self_harm, severe_distress, existential_crisis,
        emotional_dependency. All local, configurable thresholds.
      </>
    ),
  },
  {
    n: "03",
    titleHtml: "Two-tier crisis<br/><em>escalation</em>",
    desc: (
      <>
        Emergency tier skips the LLM entirely — even mid-stream. Helpline tier appends
        support info. Safety checks fire before the first token.
      </>
    ),
  },
  {
    n: "04",
    titleHtml: "Zero-cost<br/>classification",
    desc: (
      <>
        All classification runs on your machine via Ollama (gemma3n:e2b). No API calls,
        no cost, no data leaving your environment until you choose to route.
      </>
    ),
  },
  {
    n: "05",
    titleHtml: "Benchmark-backed<br/>routing",
    desc: (
      <>
        Each bias category routes to the highest-accuracy model from a 270-sample
        benchmark. Override any mapping with <code>SR_CUSTOM_ROUTING</code>.
      </>
    ),
  },
  {
    n: "06",
    titleHtml: "Safe streaming",
    desc: (
      <>
        Token streaming with full escalation checks. Emergency and helpline logic runs
        before any tokens are yielded — no unsafe responses leak through.
      </>
    ),
  },
  {
    n: "07",
    titleHtml: "Pluggable<br/>providers",
    desc: (
      <>
        OpenAI, Anthropic, Google, Groq, and Ollama out of the box. Bring your own by
        subclassing <code>BaseProvider</code>. Lazy-loaded — only installed extras imported.
      </>
    ),
  },
  {
    n: "08",
    titleHtml: "Fully local<br/>mode",
    desc: (
      <>
        Route everything to local Ollama models. Zero external API dependency — perfect
        for air-gapped environments or privacy-sensitive workloads.
      </>
    ),
  },
  {
    n: "09",
    titleHtml: "Production<br/><em>hardened</em>",
    desc: (
      <>
        Rate limiting (60 req/min), input length validation, classifier fallback on
        malformed JSON, provider error isolation, thread-safe init, 26 unit tests.
      </>
    ),
  },
];

export function Features() {
  return (
    <section className="section section-tight" id="features">
      <div className="section-label">Features</div>
      <h2>
        Built for
        <br />
        <em>responsible</em> AI.
      </h2>
      <p className="section-intro">
        Every feature is designed around the principle that safety checks should never be
        an afterthought.
      </p>

      <div className="features-grid">
        {features.map((f) => (
          <div className="feature" key={f.n}>
            <div className="feature-num">— {f.n}</div>
            <h3 dangerouslySetInnerHTML={{ __html: f.titleHtml }} />
            <p>{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
