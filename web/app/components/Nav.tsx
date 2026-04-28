export function Nav() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <a href="#" className="nav-logo">
          <div className="nav-logo-mark">SR</div>
          SafetyRouter
        </a>
        <div className="nav-links">
          <a href="#how">How it works</a>
          <a href="#crisis">Crisis safety</a>
          <a href="#docs">Documentation</a>
          <a href="#changelog">Changelog</a>
          <a
            href="https://github.com/rdxvicky/safetyrouter"
            target="_blank"
            rel="noopener"
            className="nav-cta"
          >
            Get started →
          </a>
        </div>
      </div>
    </nav>
  );
}
