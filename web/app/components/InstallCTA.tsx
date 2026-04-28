"use client";

import { useState } from "react";

const commands: { label: string; cmd: string }[] = [
  { label: "install",    cmd: "pip install safetyrouter" },
  { label: "setup",      cmd: "safetyrouter setup" },
  { label: "route",      cmd: 'safetyrouter route "your text here"' },
  { label: "all extras", cmd: 'pip install "safetyrouter[all]"' },
  { label: "serve",      cmd: "safetyrouter serve --port 8000" },
];

export function InstallCTA() {
  const [copied, setCopied] = useState<string | null>(null);

  const copy = (cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopied(cmd);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <section className="install" id="install">
      <div className="install-inner">
        <div>
          <div className="section-label" style={{ color: "#b8b29c" }}>Get started</div>
          <h2>
            Two commands
            <br />
            to <em>safer</em> AI.
          </h2>
          <p className="install-sub">
            Install the package, run setup. SafetyRouter handles Ollama, the classifier
            model, your profile, and API keys. You&apos;re routing in under a minute.
          </p>
          <div className="install-pills">
            <div className="install-pill">Python 3.10+</div>
            <div className="install-pill">Apache 2.0</div>
            <div className="install-pill">v0.2.3</div>
          </div>
          <div className="install-buttons">
            <a
              href="https://github.com/rdxvicky/safetyrouter"
              target="_blank"
              rel="noopener"
              className="btn-cream"
            >
              GitHub →
            </a>
            <a
              href="https://pypi.org/project/safetyrouter/"
              target="_blank"
              rel="noopener"
              className="btn-outline-cream"
            >
              PyPI
            </a>
          </div>
        </div>

        <div className="install-cmds">
          {commands.map(({ label, cmd }) => (
            <button
              type="button"
              key={cmd}
              className="cmd-box"
              onClick={() => copy(cmd)}
            >
              <span className="label-pre">{label}</span>
              <span
                className="arrow"
                style={copied === cmd ? { color: "#8ecf9e" } : undefined}
              >
                {copied === cmd ? "✓" : "→"}
              </span>
              <span>{cmd}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
