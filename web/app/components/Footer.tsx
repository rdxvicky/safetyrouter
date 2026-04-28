export function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-top">
        <div className="footer-brand">
          <div className="nav-logo">
            <div className="nav-logo-mark">SR</div>
            SafetyRouter
          </div>
          <p>
            Safety-aware LLM routing — bias detection, bias rephrasing, mental health
            risk detection, and human escalation. Apache 2.0.
          </p>
        </div>
        <div className="footer-col">
          <h4>Product</h4>
          <a href="#how">How it works</a>
          <a href="#crisis">Crisis safety</a>
          <a href="#features">Features</a>
          <a href="#changelog">Changelog</a>
        </div>
        <div className="footer-col">
          <h4>Documentation</h4>
          <a href="#docs">Quick start</a>
          <a href="#config">Configuration</a>
          <a href="#install">Install</a>
          <a href="https://github.com/rdxvicky/safetyrouter#readme" target="_blank" rel="noopener">README</a>
        </div>
        <div className="footer-col">
          <h4>Resources</h4>
          <a href="https://github.com/rdxvicky/safetyrouter" target="_blank" rel="noopener">GitHub</a>
          <a href="https://pypi.org/project/safetyrouter/" target="_blank" rel="noopener">PyPI</a>
          <a href="https://github.com/rdxvicky/safetyrouter/issues" target="_blank" rel="noopener">Issues</a>
          <a href="https://github.com/rdxvicky/llm-bias-evaluator" target="_blank" rel="noopener">Benchmark</a>
        </div>
      </div>
      <div className="footer-bottom">
        <div>© 2026 SafetyRouter contributors · Apache 2.0</div>
        <div>v0.2.3</div>
      </div>
    </footer>
  );
}
