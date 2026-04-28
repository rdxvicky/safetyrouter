const steps = [
  {
    n: "01",
    title: "Receive prompt",
    desc: "Any text sent via SDK, CLI, or HTTP. Input is length-validated up to 10,000 characters before classification.",
  },
  {
    n: "02",
    title: "Classify locally",
    desc: "gemma3n:e2b scores 9 bias categories and 4 mental health signals on-device via Ollama. Zero API cost, zero data egress.",
  },
  {
    n: "03",
    title: "Route or escalate",
    desc: "Emergency → skip LLM, return crisis line. Helpline → LLM + appended support info. Otherwise → route to bias-specialist model.",
  },
  {
    n: "04",
    title: "Safe response",
    desc: "Fair answer plus a rephrased bias-free version of your prompt — or crisis resources if a human is the right answer.",
  },
];

export function HowItWorks() {
  return (
    <section className="section" id="how">
      <div className="section-label">How it works</div>
      <h2>
        A safer path
        <br />
        to a <em>fairer</em> answer.
      </h2>
      <p className="section-intro">
        Every prompt is classified locally for bias and mental health risk before any API
        call is made. The router then decides — escalate, route to a specialist, or answer
        normally.
      </p>
      <div className="steps-grid">
        {steps.map((s) => (
          <div className="step" key={s.n}>
            <div className="step-num">— {s.n}</div>
            <div className="step-title">{s.title}</div>
            <div className="step-desc">{s.desc}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
