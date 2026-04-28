const rows: [string, string, string, number][] = [
  ["gender", "GPT-4", "gpt-4o", 96.7],
  ["disability", "GPT-4", "gpt-4o", 100],
  ["religion", "GPT-4", "gpt-4o", 96.7],
  ["race", "Claude", "claude-opus-4-5", 83.3],
  ["age", "Claude", "claude-opus-4-5", 100],
  ["sexual_orientation", "Claude", "claude-opus-4-5", 83.3],
  ["socioeconomic_status", "Claude", "claude-opus-4-5", 96.7],
  ["nationality", "Gemini", "gemini-2.0-flash", 96.7],
  ["physical_appearance", "Gemini", "gemini-2.0-flash", 100],
];

export function RoutingTable() {
  return (
    <section className="section section-tight">
      <div className="section-label">Routing table</div>
      <h2>
        Every bias type
        <br />
        has a <em>specialist</em>.
      </h2>
      <p className="section-intro">
        Routing decisions are backed by benchmark accuracy from the{" "}
        <a
          href="https://github.com/rdxvicky/llm-bias-evaluator"
          target="_blank"
          rel="noopener"
          style={{ color: "var(--coral)", textDecoration: "underline", textUnderlineOffset: 3 }}
        >
          LLM Bias Evaluator
        </a>{" "}
        — 270 samples across StereoSet, CrowS-Pairs, BBQ, HolisticBias, and BOLD.
      </p>

      <div className="data-card">
        <table>
          <thead>
            <tr>
              <th>Bias category</th>
              <th>Routed to</th>
              <th>Model ID</th>
              <th>Benchmark accuracy</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([cat, provider, model, acc]) => (
              <tr key={cat}>
                <td><span className="cat-tag">{cat}</span></td>
                <td>
                  <span className="provider-pill">
                    <span className="dot" />
                    {provider}
                  </span>
                </td>
                <td><code>{model}</code></td>
                <td>
                  <div className="acc-cell">
                    <div className="acc-bar">
                      <div className="acc-fill" style={{ width: `${acc}%` }} />
                    </div>
                    <span className="acc-num">{acc === 100 ? "100%" : `${acc}%`}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
