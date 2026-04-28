export function ProvidersStrip() {
  return (
    <div className="strip">
      <div className="strip-label">Routes across</div>
      <div className="strip-providers">
        <span>OpenAI</span>
        <div className="dot" />
        <span>Anthropic</span>
        <div className="dot" />
        <span>Google</span>
        <div className="dot" />
        <span>Groq</span>
        <div className="dot" />
        <span>Ollama</span>
      </div>
      <div className="strip-label">5 providers · BYO welcome</div>
    </div>
  );
}
