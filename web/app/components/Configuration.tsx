const env: { name: string; def: string; desc: React.ReactNode }[] = [
  { name: "SR_CLASSIFIER_MODEL",     def: "gemma3n:e2b", desc: "Ollama model for local bias + mental health classification" },
  { name: "SR_USER_NAME",            def: "—",           desc: "User's name — used in crisis transcript and age-aware prompts" },
  { name: "SR_USER_AGE_RANGE",       def: "—",           desc: "Age range (Under 18, 18–25, … 60+) — activates youth/elder-aware prompts" },
  { name: "SR_USER_COUNTRY",         def: "US",          desc: "ISO-2 code or full name — determines crisis helpline and emergency number" },
  { name: "SR_SELF_HARM_THRESHOLD",  def: "0.70",        desc: "self_harm score ≥ this triggers Tier 1 emergency (LLM skipped)" },
  { name: "SR_HELPLINE_THRESHOLD",   def: "0.60",        desc: "severe_distress / existential_crisis ≥ this triggers Tier 2 helpline" },
  { name: "SR_CUSTOM_ROUTING",       def: "{}",          desc: <>JSON map of bias category → provider override, e.g. <code>{`{"gender":"claude"}`}</code></> },
  { name: "OPENAI_API_KEY",          def: "—",           desc: "Required for GPT-4 routing (gender, disability, religion)" },
  { name: "ANTHROPIC_API_KEY",       def: "—",           desc: "Required for Claude routing (race, age, sexual_orientation, socioeconomic)" },
  { name: "GOOGLE_API_KEY",          def: "—",           desc: "Required for Gemini routing (nationality, physical_appearance)" },
  { name: "GROQ_API_KEY",            def: "—",           desc: "Optional — Groq/Mixtral as fallback or custom routing target" },
];

export function Configuration() {
  return (
    <section className="section section-tight" id="config">
      <div className="section-label">Configuration</div>
      <h2>
        All environment
        <br />
        <em>variables</em>.
      </h2>
      <p className="section-intro">
        Every option can be set via environment variable or passed directly to{" "}
        <code>SafetyRouterConfig</code>. <code>safetyrouter setup</code> writes a{" "}
        <code>.env</code> file automatically.
      </p>

      <div className="data-card">
        <table>
          <thead>
            <tr>
              <th>Variable</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {env.map((row) => (
              <tr key={row.name}>
                <td><span className="env">{row.name}</span></td>
                <td><span className="def">{row.def}</span></td>
                <td className="desc">{row.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
