"""
CLI for SafetyRouter.

Usage:
    safetyrouter setup                              # first-time setup
    safetyrouter route "Should women be engineers?"
    safetyrouter classify "text here"
    safetyrouter serve --port 8000
    safetyrouter inspect
"""
import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
import time

import click

from .config import SafetyRouterConfig
from .router import SafetyRouter

DEFAULT_MODEL = "gemma3n:e2b"

GLOBAL_CONFIG_FILE = os.path.expanduser("~/.safetyrouter.env")

# Fallback models when the default requires a newer Ollama
FALLBACK_MODELS = [
    ("gemma2:2b",   "Gemma 2 2B   — small, fast, widely compatible"),
    ("llama3.2:3b", "Llama 3.2 3B — popular, good quality"),
    ("phi3:mini",   "Phi-3 Mini   — very lightweight"),
]

# LLM providers for interactive API key setup
PROVIDERS = [
    ("OPENAI_API_KEY",    "OpenAI",    "GPT-4o",  "sk-..."),
    ("ANTHROPIC_API_KEY", "Anthropic", "Claude",  "sk-ant-..."),
    ("GOOGLE_API_KEY",    "Google",    "Gemini",  "AIza..."),
    ("GROQ_API_KEY",      "Groq",      "Mixtral", "gsk_...  (free tier: console.groq.com)"),
]

OLLAMA_ERROR_MSG = (
    "Ollama is not running.\n\n"
    "  Run this to fix it:\n"
    "  → safetyrouter setup\n\n"
    "  Or start Ollama manually: ollama serve"
)


# ── Global config helpers ──────────────────────────────────────────────────

def _read_global_config() -> dict:
    """Read ~/.safetyrouter.env as a dict."""
    result = {}
    if os.path.exists(GLOBAL_CONFIG_FILE):
        with open(GLOBAL_CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    result[k.strip()] = v.strip()
    return result


def _save_global_config(values: dict):
    """Merge key=value pairs into ~/.safetyrouter.env."""
    existing = _read_global_config()
    existing.update(values)
    with open(GLOBAL_CONFIG_FILE, "w") as f:
        f.write("# SafetyRouter global configuration\n")
        for k, v in existing.items():
            f.write(f"{k}={v}\n")


# ── Error handling ─────────────────────────────────────────────────────────

def _handle_error(e: Exception):
    msg = str(e)
    if "Failed to connect to Ollama" in msg or "ConnectionError" in msg or "Connection refused" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + OLLAMA_ERROR_MSG, err=True)
        sys.exit(1)
    if "OPENAI_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "OPENAI_API_KEY not set.\nRun: export OPENAI_API_KEY=sk-...", err=True)
        sys.exit(1)
    if "ANTHROPIC_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "ANTHROPIC_API_KEY not set.\nRun: export ANTHROPIC_API_KEY=sk-ant-...", err=True)
        sys.exit(1)
    if "GOOGLE_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "GOOGLE_API_KEY not set.\nRun: export GOOGLE_API_KEY=AIza...", err=True)
        sys.exit(1)
    if "GROQ_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "GROQ_API_KEY not set.\nRun: export GROQ_API_KEY=gsk_...", err=True)
        sys.exit(1)
    click.echo(click.style("Error: ", fg="red", bold=True) + msg, err=True)
    sys.exit(1)


# ── Ollama helpers ─────────────────────────────────────────────────────────

def _is_ollama_installed() -> bool:
    return shutil.which("ollama") is not None


def _is_ollama_running() -> bool:
    try:
        import httpx
        r = httpx.get("http://localhost:11434", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _install_ollama():
    system = platform.system()
    click.echo(click.style("  Installing Ollama...", fg="yellow"))

    if system == "Darwin" or system == "Linux":
        result = subprocess.run(
            "curl -fsSL https://ollama.com/install.sh | sh",
            shell=True,
        )
        if result.returncode != 0:
            click.echo(click.style("  ✗ Auto-install failed.", fg="red"))
            click.echo("  Please install manually: https://ollama.com/download")
            sys.exit(1)
    elif system == "Windows":
        click.echo(click.style("  Windows detected.", fg="yellow"))
        click.echo("  Please download and install Ollama from: https://ollama.com/download")
        click.echo("  Then re-run: safetyrouter setup")
        sys.exit(0)
    else:
        click.echo("  Unknown OS. Install Ollama manually: https://ollama.com/download")
        sys.exit(1)

    click.echo(click.style("  ✓ Ollama installed.", fg="green"))


def _update_ollama() -> bool:
    """Update Ollama in-place. Returns True on success."""
    system = platform.system()
    click.echo(click.style("  Updating Ollama...", fg="yellow"))

    if system == "Darwin" or system == "Linux":
        result = subprocess.run(
            "curl -fsSL https://ollama.com/install.sh | sh",
            shell=True,
        )
        if result.returncode != 0:
            click.echo(click.style("  ✗ Update failed.", fg="red"))
            return False
    elif system == "Windows":
        result = subprocess.run(
            ["powershell", "-Command", "irm https://ollama.com/install.ps1 | iex"],
            shell=True,
        )
        if result.returncode != 0:
            click.echo(click.style("  ✗ Update failed.", fg="red"))
            return False
    else:
        click.echo(click.style("  ✗ Cannot auto-update on this OS.", fg="red"))
        return False

    click.echo(click.style("  ✓ Ollama updated.", fg="green"))
    return True


def _start_ollama():
    click.echo(click.style("  Starting Ollama...", fg="yellow"))
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(15):
        time.sleep(1)
        if _is_ollama_running():
            click.echo(click.style("  ✓ Ollama is running.", fg="green"))
            return
    click.echo(click.style("  ✗ Ollama didn't start in time. Try running `ollama serve` manually.", fg="red"))
    sys.exit(1)


def _do_pull(model: str) -> bool:
    """Run ollama pull, stream output. Returns True on success."""
    proc = subprocess.Popen(
        ["ollama", "pull", model],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines = []
    for line in proc.stdout:
        click.echo(f"  {line}", nl=False)
        lines.append(line)
    proc.wait()
    return proc.returncode == 0, "".join(lines)


def _handle_outdated_ollama(original_model: str) -> str:
    """
    Called when ollama pull fails with 'newer version required'.
    Offers to auto-update Ollama, or pick a fallback classifier model.
    Returns the model name that was successfully set up.
    """
    click.echo()
    click.echo(click.style(f"  Ollama is outdated and cannot run {original_model}.", fg="yellow"))
    click.echo()

    if click.confirm("  Update Ollama now? (recommended)", default=True):
        if _update_ollama():
            # The update script stops and restarts Ollama — wait for it
            if not _is_ollama_running():
                _start_ollama()
            click.echo(click.style(f"\n  Retrying {original_model}...", fg="yellow"))
            ok, _ = _do_pull(original_model)
            if ok:
                click.echo(click.style(f"  ✓ {original_model} is ready.", fg="green"))
                return original_model
            click.echo(click.style(f"  ✗ Still unable to pull {original_model}.", fg="red"))
        else:
            click.echo(click.style("  ✗ Update failed.", fg="red"))

    # Fallback model picker
    click.echo()
    click.echo("  Pick a compatible classifier model:")
    for i, (m, desc) in enumerate(FALLBACK_MODELS, 1):
        click.echo(f"    [{i}] {m:<16}  {desc}")
    click.echo(f"    [0] Enter a custom model name")
    click.echo()

    choice = click.prompt(
        "  Choice",
        type=click.IntRange(0, len(FALLBACK_MODELS)),
        default=1,
    )
    chosen = click.prompt("  Model name") if choice == 0 else FALLBACK_MODELS[choice - 1][0]

    click.echo(click.style(f"\n  Pulling {chosen}...", fg="yellow"))
    result = subprocess.run(["ollama", "pull", chosen])
    if result.returncode != 0:
        click.echo(click.style(f"  ✗ Failed to pull {chosen}.", fg="red"))
        sys.exit(1)

    click.echo(click.style(f"  ✓ {chosen} is ready.", fg="green"))
    _save_global_config({"CLASSIFIER_MODEL": chosen})
    click.echo(click.style(f"  ✓ Saved {chosen} as your classifier model in ~/.safetyrouter.env", fg="green"))
    return chosen


def _pull_model(model: str) -> str:
    """Pull an Ollama model. Returns the model name that ended up being set up."""
    click.echo(click.style(f"  Pulling {model} (this may take a few minutes)...", fg="yellow"))
    ok, output = _do_pull(model)
    if not ok:
        if "newer version" in output.lower():
            return _handle_outdated_ollama(model)
        click.echo(click.style(f"\n  ✗ Failed to pull {model}.", fg="red"))
        sys.exit(1)
    click.echo(click.style(f"  ✓ {model} is ready.", fg="green"))
    return model


# ── API key setup ──────────────────────────────────────────────────────────

def _setup_api_keys():
    """Interactive API key configuration. Keys saved to ~/.safetyrouter.env."""
    click.echo("\n[4/4] Configure LLM provider API keys...")
    click.echo("      Keys are saved to ~/.safetyrouter.env and loaded automatically.\n")

    global_cfg = _read_global_config()

    for env_key, name, model, hint in PROVIDERS:
        if os.getenv(env_key) or global_cfg.get(env_key):
            click.echo(click.style(f"  ✓ {name:<12} ({model}) already configured.", fg="green"))
            continue

        value = click.prompt(
            f"  {name:<12} key  ({hint})",
            default="",
            show_default=False,
        )
        if value.strip():
            _save_global_config({env_key: value.strip()})
            global_cfg[env_key] = value.strip()
            click.echo(click.style(f"  ✓ {name} key saved.", fg="green"))
        else:
            click.echo(click.style(
                f"  — {name} skipped  (add later: export {env_key}=...)",
                fg="bright_black",
            ))


# ── Router factory ─────────────────────────────────────────────────────────

def _get_router() -> SafetyRouter:
    return SafetyRouter(config=SafetyRouterConfig.from_env())


# ── CLI commands ───────────────────────────────────────────────────────────

@click.group()
@click.version_option(package_name="safetyrouter")
def main():
    """SafetyRouter — always get an unbiased answer."""
    pass


@main.command()
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Ollama model to use as classifier.")
@click.option("--skip-keys", is_flag=True, help="Skip API key configuration step.")
def setup(model: str, skip_keys: bool):
    """First-time setup: installs Ollama, pulls the classifier model, and configures API keys."""
    click.echo(click.style("\nSafetyRouter Setup\n", bold=True) + "─" * 30)

    # Step 1 — Ollama installed?
    click.echo("\n[1/4] Checking Ollama installation...")
    if _is_ollama_installed():
        click.echo(click.style("  ✓ Ollama already installed.", fg="green"))
    else:
        _install_ollama()

    # Step 2 — Ollama running?
    click.echo("\n[2/4] Checking Ollama is running...")
    if _is_ollama_running():
        click.echo(click.style("  ✓ Ollama already running.", fg="green"))
    else:
        _start_ollama()

    # Step 3 — Pull model
    click.echo(f"\n[3/4] Pulling classifier model ({model})...")
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if model in result.stdout:
        click.echo(click.style(f"  ✓ {model} already pulled.", fg="green"))
    else:
        _pull_model(model)

    # Step 4 — API keys
    if not skip_keys:
        _setup_api_keys()

    # Done
    click.echo(click.style("\n✓ Setup complete! SafetyRouter is ready to use.\n", fg="green", bold=True))
    click.echo("Try it:")
    click.echo(click.style('  safetyrouter classify "Women are worse drivers than men."', fg="cyan"))
    click.echo(click.style('  safetyrouter route "Should people be judged by their race?"\n', fg="cyan"))


@main.command()
@click.argument("text")
@click.option("--no-execute", is_flag=True, help="Only show routing decision, skip model call.")
@click.option("--stream", is_flag=True, help="Stream the response token by token.")
@click.option("--json-output", is_flag=True, help="Output full JSON response.")
def route(text: str, no_execute: bool, stream: bool, json_output: bool):
    """Classify bias in TEXT and route to the best LLM."""

    async def _run():
        router = _get_router()

        if stream:
            click.echo("Streaming via SafetyRouter...\n", err=True)
            async for token in router.stream(text):
                click.echo(token, nl=False)
            click.echo()
            return

        result = await router.route(text, execute=not no_execute)

        if json_output:
            click.echo(result.model_dump_json(indent=2))
            return

        click.echo(f"\nBias Category : {result.bias_category}")
        click.echo(f"Confidence    : {result.confidence:.2%}")
        click.echo(f"Routed to     : {result.selected_model}")
        if result.model_accuracy:
            click.echo(f"Model Accuracy: {result.model_accuracy}%")
        click.echo(f"Reason        : {result.reason}")
        click.echo(f"Response Time : {result.response_time}s")
        if result.content:
            click.echo(f"\n--- Response ---\n{result.content}")

    try:
        asyncio.run(_run())
    except Exception as e:
        _handle_error(e)


@main.command()
@click.argument("text")
@click.option("--json-output", is_flag=True, help="Output full JSON bias scores.")
def classify(text: str, json_output: bool):
    """Run only the bias classifier (no LLM call). Free — runs locally."""

    async def _run():
        router = _get_router()
        result = await router.route(text, execute=False)

        if json_output:
            click.echo(json.dumps(result.bias_analysis, indent=2))
            return

        highest = result.bias_analysis.get("highest_probability_category", {})
        click.echo(f"\nTop category  : {highest.get('category', 'unknown')}")
        click.echo(f"Confidence    : {float(highest.get('probability', 0)):.2%}")
        click.echo(f"Would route to: {result.selected_model}")
        note = result.bias_analysis.get("note", "")
        if note:
            click.echo(f"Note          : {note}")

    try:
        asyncio.run(_run())
    except Exception as e:
        _handle_error(e)


@main.command()
def inspect():
    """Show the current bias-to-model routing table."""
    router = _get_router()
    table = router.inspect()
    click.echo("\nRouting Table:")
    click.echo(f"{'Category':<25} {'Provider':<12} {'Accuracy'}")
    click.echo("-" * 50)
    for cat, info in table.items():
        acc = f"{info['accuracy']}%" if info["accuracy"] else "custom"
        click.echo(f"{cat:<25} {info['provider']:<12} {acc}")


@main.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind host.")
@click.option("--port", default=8000, show_default=True, help="Bind port.")
@click.option("--reload", is_flag=True, help="Enable auto-reload (development).")
def serve(host: str, port: int, reload: bool):
    """Start the SafetyRouter HTTP server (FastAPI + uvicorn)."""
    try:
        import uvicorn
    except ImportError:
        click.echo(
            click.style("Error: ", fg="red", bold=True) +
            "uvicorn not installed. Run: pip install 'safetyrouter[serve]'",
            err=True
        )
        sys.exit(1)

    click.echo(f"Starting SafetyRouter server on http://{host}:{port}")
    click.echo(f"Docs available at: http://localhost:{port}/docs\n")
    uvicorn.run(
        "safetyrouter.server:app",
        host=host,
        port=port,
        reload=reload,
    )
