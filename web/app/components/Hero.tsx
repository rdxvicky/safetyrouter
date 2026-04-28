export function Hero() {
  const terminalHtml = `<span class="prompt">$</span> <span class="cmd">safetyrouter route "Are older workers less productive?"</span>

<span class="punct">{</span>
  <span class="key">"routing_decision"</span><span class="punct">:</span> <span class="punct">{</span>
    <span class="key">"selected_model"</span><span class="punct">:</span> <span class="str">"claude"</span><span class="punct">,</span>
    <span class="key">"bias_category"</span><span class="punct">:</span>  <span class="str">"age"</span><span class="punct">,</span>
    <span class="key">"confidence"</span><span class="punct">:</span>     <span class="num">0.89</span><span class="punct">,</span>
    <span class="key">"model_accuracy"</span><span class="punct">:</span> <span class="num">100.0</span><span class="punct">,</span>
    <span class="key">"reason"</span><span class="punct">:</span> <span class="str">"Routed to claude — 100% benchmark accuracy"</span>
  <span class="punct">},</span>
  <span class="key">"bias_analysis"</span><span class="punct">:</span> <span class="punct">{</span>
    <span class="key">"age"</span><span class="punct">:</span> <span class="punct">{</span> <span class="key">"probability"</span><span class="punct">:</span> <span class="num">0.89</span> <span class="punct">},</span>
    <span class="key">"rephrased_text"</span><span class="punct">:</span> <span class="punct">{</span>
      <span class="key">"original"</span><span class="punct">:</span>  <span class="str">"Are older workers less productive?"</span><span class="punct">,</span>
      <span class="key">"rephrased"</span><span class="punct">:</span> <span class="str">"How does experience shape productivity?"</span><span class="punct">,</span>
      <span class="key">"meaning_preserved"</span><span class="punct">:</span> <span class="kw">true</span>
    <span class="punct">}</span>
  <span class="punct">},</span>
  <span class="key">"response_time"</span><span class="punct">:</span> <span class="str">"9.43s"</span>
<span class="punct">}</span>`;

  return (
    <section className="hero">
      <div className="hero-eyebrow">
        <span className="dot-live" />
        v0.2.3 &nbsp;·&nbsp; Open Source &nbsp;·&nbsp; Apache 2.0
      </div>

      <h1 className="hero-headline">
        Route every prompt to the
        <br />
        <em>safest</em> possible answer.
      </h1>

      <div className="hero-meta-row">
        <p className="hero-tagline">
          SafetyRouter classifies bias and mental health risk locally at zero API cost,
          routes to the best specialist model, and escalates to crisis services when a
          human is the right answer.
        </p>
        <div className="hero-cta-row">
          <a href="#docs" className="btn-primary">Read the docs →</a>
          <a
            href="https://github.com/rdxvicky/safetyrouter"
            target="_blank"
            rel="noopener"
            className="btn-ghost"
          >
            View on GitHub
          </a>
        </div>
      </div>

      <div className="hero-stage">
        <div className="float-pill tl">
          <span className="pill-icon green">●</span>
          Running locally · 0 API cost
        </div>
        <div className="float-pill tr">
          <span className="pill-icon coral">9</span>
          bias categories scored
        </div>
        <div className="float-pill bl">
          <span className="pill-icon amber">!</span>
          2-tier crisis escalation
        </div>
        <div className="float-pill br">
          <span className="pill-icon green">↑</span>
          96.7% routing accuracy
        </div>

        <div className="terminal">
          <div className="terminal-bar">
            <div className="term-dots">
              <div className="term-dot" />
              <div className="term-dot" />
              <div className="term-dot" />
            </div>
            <div className="term-title">~/safety-router · zsh</div>
            <div style={{ width: 42 }} />
          </div>
          <pre
            className="term-body"
            dangerouslySetInnerHTML={{ __html: terminalHtml }}
          />
        </div>
      </div>

      <div className="mega-wordmark">SafetyRouter</div>
    </section>
  );
}
