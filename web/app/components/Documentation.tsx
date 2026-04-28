"use client";

import { useState } from "react";

type TabKey = "sdk" | "cli" | "http" | "stream" | "local";

const TABS: { key: TabKey; label: string; title: string }[] = [
  { key: "sdk",    label: "Python SDK",    title: "main.py" },
  { key: "cli",    label: "CLI",           title: "terminal · zsh" },
  { key: "http",   label: "HTTP Server",   title: "terminal · zsh" },
  { key: "stream", label: "Streaming",     title: "stream.py" },
  { key: "local",  label: "Fully local",   title: "config.py" },
];

const SAMPLES: Record<TabKey, string> = {
  sdk: `<span class="kw">import</span> asyncio
<span class="kw">from</span> safetyrouter <span class="kw">import</span> <span class="nm">SafetyRouter</span>

<span class="cm"># Reads API keys from environment</span>
<span class="nm">router</span> <span class="op">=</span> <span class="fn">SafetyRouter</span>()

<span class="kw">async def</span> <span class="fn">main</span>():
    <span class="nm">r</span> <span class="op">=</span> <span class="kw">await</span> <span class="nm">router</span>.<span class="fn">route</span>(<span class="st">"Should women be paid less?"</span>)

    <span class="fn">print</span>(<span class="nm">r</span>.bias_category)   <span class="cm"># "gender"</span>
    <span class="fn">print</span>(<span class="nm">r</span>.selected_model)  <span class="cm"># "gpt4"</span>
    <span class="fn">print</span>(<span class="nm">r</span>.model_accuracy)   <span class="cm"># 96.7</span>
    <span class="fn">print</span>(<span class="nm">r</span>.content)         <span class="cm"># LLM answer</span>

    <span class="cm"># Bias rephrasing — always present</span>
    <span class="nm">rp</span> <span class="op">=</span> <span class="nm">r</span>.bias_analysis[<span class="st">"rephrased_text"</span>]
    <span class="fn">print</span>(<span class="nm">rp</span>[<span class="st">"rephrased"</span>])
    <span class="fn">print</span>(<span class="nm">rp</span>[<span class="st">"meaning_preserved"</span>])

    <span class="cm"># Crisis escalation</span>
    <span class="kw">if</span> <span class="nm">r</span>.escalation_type <span class="op">==</span> <span class="st">"emergency"</span>:
        <span class="fn">print</span>(<span class="nm">r</span>.escalation_number)  <span class="cm"># "988"</span>
        <span class="fn">print</span>(<span class="nm">r</span>.escalation_service)
        <span class="fn">print</span>(<span class="nm">r</span>.session_transcript_path)

    <span class="cm"># Classify only — zero API cost</span>
    <span class="nm">dry</span> <span class="op">=</span> <span class="kw">await</span> <span class="nm">router</span>.<span class="fn">route</span>(<span class="st">"text"</span>, execute<span class="op">=</span><span class="kw">False</span>)
    <span class="fn">print</span>(<span class="nm">dry</span>.mental_health_scores)

asyncio.<span class="fn">run</span>(<span class="fn">main</span>())`,

  cli: `<span class="cm"># First-time setup — Ollama, classifier, profile, API keys</span>
<span class="kw">$</span> safetyrouter setup

<span class="cm"># Route — outputs structured JSON</span>
<span class="kw">$</span> safetyrouter route <span class="st">"Should people be judged by their race?"</span>

{
  <span class="st">"routing_decision"</span>: {
    <span class="st">"selected_model"</span>: <span class="st">"claude"</span>,
    <span class="st">"bias_category"</span>: <span class="st">"race"</span>,
    <span class="st">"confidence"</span>:     <span class="nu">0.85</span>,
    <span class="st">"model_accuracy"</span>: <span class="nu">83.3</span>,
    <span class="st">"reason"</span>: <span class="st">"Routed to claude — 83.3% accuracy"</span>,
    <span class="st">"message_content"</span>: <span class="st">"No, people should not be..."</span>
  },
  <span class="st">"bias_analysis"</span>: {
    <span class="st">"race"</span>: { <span class="st">"probability"</span>: <span class="nu">0.85</span> },
    <span class="st">"rephrased_text"</span>: {
      <span class="st">"original"</span>:  <span class="st">"Should people be judged by their race?"</span>,
      <span class="st">"rephrased"</span>: <span class="st">"Should people be judged by character?"</span>,
      <span class="st">"meaning_preserved"</span>: <span class="kw">true</span>,
      <span class="st">"meaning_change_risk"</span>: <span class="st">"low"</span>
    }
  },
  <span class="st">"response_time"</span>: <span class="st">"14.2s"</span>
}

<span class="cm"># Classify only — no API call</span>
<span class="kw">$</span> safetyrouter classify <span class="st">"I feel hopeless."</span>`,

  http: `<span class="cm"># Install + start the server</span>
<span class="kw">$</span> pip install <span class="st">"safetyrouter[serve]"</span>
<span class="kw">$</span> safetyrouter serve --host 0.0.0.0 --port 8000

<span class="cm"># POST /route</span>
<span class="kw">$</span> curl -s -X POST localhost:8000/route \\
    -H <span class="st">"Content-Type: application/json"</span> \\
    -d <span class="st">'{"text": "Are older workers less productive?"}'</span> | jq

{
  <span class="st">"routing_decision"</span>: {
    <span class="st">"selected_model"</span>: <span class="st">"claude"</span>,
    <span class="st">"bias_category"</span>: <span class="st">"age"</span>,
    <span class="st">"confidence"</span>:     <span class="nu">0.89</span>,
    <span class="st">"model_accuracy"</span>: <span class="nu">100.0</span>,
    <span class="st">"message_content"</span>: <span class="st">"Research consistently shows..."</span>
  },
  <span class="st">"escalation_type"</span>: <span class="kw">null</span>,
  <span class="st">"response_time"</span>: <span class="st">"9.43s"</span>
}

<span class="cm"># Other endpoints</span>
<span class="kw">$</span> curl localhost:8000/health
<span class="kw">$</span> curl localhost:8000/routing-table
<span class="kw">$</span> open localhost:8000/docs`,

  stream: `<span class="kw">import</span> asyncio
<span class="kw">from</span> safetyrouter <span class="kw">import</span> <span class="nm">SafetyRouter</span>

<span class="nm">router</span> <span class="op">=</span> <span class="fn">SafetyRouter</span>()

<span class="kw">async def</span> <span class="fn">stream</span>(<span class="nm">text</span>):
    <span class="cm"># Safety checks run BEFORE any tokens are yielded.</span>
    <span class="cm"># Emergency tier → yields crisis block + returns (no LLM tokens)</span>
    <span class="cm"># Helpline tier  → yields LLM tokens + appends helpline line</span>
    <span class="kw">async for</span> <span class="nm">token</span> <span class="kw">in</span> <span class="nm">router</span>.<span class="fn">stream</span>(<span class="nm">text</span>):
        <span class="fn">print</span>(<span class="nm">token</span>, end<span class="op">=</span><span class="st">""</span>, flush<span class="op">=</span><span class="kw">True</span>)

<span class="cm"># Normal — streams from the routed model</span>
asyncio.<span class="fn">run</span>(<span class="fn">stream</span>(<span class="st">"Are women less suited for leadership?"</span>))

<span class="cm"># Emergency — no LLM tokens, just crisis block</span>
asyncio.<span class="fn">run</span>(<span class="fn">stream</span>(<span class="st">"I want to end it all."</span>))
<span class="cm"># → "CRISIS SUPPORT</span>
<span class="cm">#    Emergency: 911</span>
<span class="cm">#    Crisis line: 988 — 988 Suicide & Crisis Lifeline"</span>

<span class="cm"># Helpline — LLM tokens then helpline appended</span>
asyncio.<span class="fn">run</span>(<span class="fn">stream</span>(<span class="st">"I feel completely hopeless."</span>))`,

  local: `<span class="kw">from</span> safetyrouter <span class="kw">import</span> <span class="nm">SafetyRouter</span>, <span class="nm">SafetyRouterConfig</span>
<span class="kw">from</span> safetyrouter.providers <span class="kw">import</span> <span class="nm">OllamaProvider</span>

<span class="cm"># Route to local models — no external API calls</span>
<span class="nm">router</span> <span class="op">=</span> <span class="fn">SafetyRouter</span>(
    providers<span class="op">=</span>{
        <span class="st">"gpt4"</span>:    <span class="fn">OllamaProvider</span>(model<span class="op">=</span><span class="st">"llama3.2"</span>),
        <span class="st">"claude"</span>:  <span class="fn">OllamaProvider</span>(model<span class="op">=</span><span class="st">"llama3.2"</span>),
        <span class="st">"gemini"</span>:  <span class="fn">OllamaProvider</span>(model<span class="op">=</span><span class="st">"mistral"</span>),
        <span class="st">"mixtral"</span>: <span class="fn">OllamaProvider</span>(model<span class="op">=</span><span class="st">"mixtral"</span>),
    }
)

<span class="cm"># User profile — controls crisis resources + system prompt tone</span>
<span class="nm">config</span> <span class="op">=</span> <span class="fn">SafetyRouterConfig</span>(
    user_name<span class="op">=</span><span class="st">"Alex"</span>,
    user_age_range<span class="op">=</span><span class="st">"Under 18"</span>,
    user_country<span class="op">=</span><span class="st">"AU"</span>,
    self_harm_threshold<span class="op">=</span><span class="nu">0.70</span>,
    helpline_threshold<span class="op">=</span><span class="nu">0.60</span>,
    custom_routing<span class="op">=</span>{<span class="st">"gender"</span>: <span class="st">"claude"</span>},
)

<span class="nm">router</span> <span class="op">=</span> <span class="fn">SafetyRouter</span>(config<span class="op">=</span><span class="nm">config</span>)`,
};

export function Documentation() {
  const [active, setActive] = useState<TabKey>("sdk");
  const activeTab = TABS.find((t) => t.key === active)!;

  return (
    <section className="section section-tight" id="docs">
      <div className="section-label">Documentation</div>
      <h2>
        Three ways
        <br />
        to <em>integrate</em>.
      </h2>
      <p className="section-intro">
        Python SDK for embedding in applications, CLI for quick testing, or HTTP server
        to drop behind any stack.
      </p>

      <div className="docs-grid">
        <aside className="docs-side">
          <div className="docs-side-label">Quick start</div>
          <div className="docs-tabs">
            {TABS.map((t) => (
              <button
                key={t.key}
                className={`docs-tab${active === t.key ? " active" : ""}`}
                onClick={() => setActive(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </aside>

        <div className="docs-codeblock">
          <div className="terminal-bar">
            <div className="term-dots">
              <div className="term-dot" />
              <div className="term-dot" />
              <div className="term-dot" />
            </div>
            <div className="term-title">{activeTab.title}</div>
            <div style={{ width: 42 }} />
          </div>
          <pre dangerouslySetInnerHTML={{ __html: SAMPLES[active] }} />
        </div>
      </div>
    </section>
  );
}
