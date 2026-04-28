const countries = [
  ["🇺🇸", "United States", "988"],
  ["🇬🇧", "United Kingdom", "116 123"],
  ["🇨🇦", "Canada", "1-833-456"],
  ["🇦🇺", "Australia", "13 11 14"],
  ["🇮🇳", "India", "9152987821"],
  ["🇳🇿", "New Zealand", "1737"],
  ["🇩🇪", "Germany", "0800 111"],
  ["🇫🇷", "France", "3114"],
  ["🇯🇵", "Japan", "0120-783"],
  ["🇧🇷", "Brazil", "188"],
  ["🇲🇽", "Mexico", "800 290"],
  ["🇿🇦", "South Africa", "0800 567"],
  ["🇸🇬", "Singapore", "1800 221"],
  ["🇮🇪", "Ireland", "116 123"],
  ["🇲🇾", "Malaysia", "015-4882"],
];

export function CrisisSafety() {
  return (
    <section className="section section-tight" id="crisis">
      <div className="section-label">Crisis safety</div>
      <h2>
        When a human is
        <br />
        the <em>right</em> answer.
      </h2>
      <p className="section-intro">
        When the mental health classifier detects risk, SafetyRouter steps aside.
        All classification runs locally — no risk signals leave your machine.
      </p>

      <div className="crisis-grid">
        <div className="crisis-card tier-1">
          <div className="crisis-tier-label">Tier 1 — Emergency</div>
          <div className="crisis-card-title">
            LLM is skipped
            <br />
            entirely.
          </div>
          <div className="crisis-trigger">self_harm ≥ 0.70</div>
          <p className="crisis-desc">
            <strong>No model is called.</strong> A crisis block is returned with the local
            emergency number and helpline for the user&apos;s country. Session transcript is
            saved to <code>~/.safetyrouter/sessions/</code> with <code>0o600</code> permissions.
          </p>
        </div>

        <div className="crisis-card tier-2">
          <div className="crisis-tier-label">Tier 2 — Helpline</div>
          <div className="crisis-card-title">
            LLM responds
            <br />
            + helpline.
          </div>
          <div className="crisis-trigger">severe_distress ≥ 0.60</div>
          <p className="crisis-desc">
            <strong>Normal routing proceeds.</strong> The LLM response is returned with
            the crisis helpline number and webchat link appended below — the user gets
            both a helpful answer and a clear path to human support.
          </p>
        </div>
      </div>

      <div className="country-strip">
        <div className="docs-side-label" style={{ marginBottom: "1.25rem" }}>
          15 countries supported out of the box
        </div>
        <div className="country-grid">
          {countries.map(([flag, name, num]) => (
            <div className="country-cell" key={name}>
              <span className="flag">{flag}</span>
              <span className="name">{name}</span>
              <span className="num">{num}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
