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

OLLAMA_ERROR_MSG = (
    "Ollama is not running.\n\n"
    "  Run this to fix it:\n"
    "  → safetyrouter setup\n\n"
    "  Or start Ollama manually: ollama serve"
)


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


def _start_ollama():
    click.echo(click.style("  Starting Ollama...", fg="yellow"))
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Wait for it to be ready
    for _ in range(15):
        time.sleep(1)
        if _is_ollama_running():
            click.echo(click.style("  ✓ Ollama is running.", fg="green"))
            return
    click.echo(click.style("  ✗ Ollama didn't start in time. Try running `ollama serve` manually.", fg="red"))
    sys.exit(1)


def _pull_model(model: str):
    click.echo(click.style(f"  Pulling {model} (this may take a few minutes)...", fg="yellow"))
    result = subprocess.run(["ollama", "pull", model])
    if result.returncode != 0:
        click.echo(click.style(f"  ✗ Failed to pull {model}.", fg="red"))
        sys.exit(1)
    click.echo(click.style(f"  ✓ {model} is ready.", fg="green"))


def _get_router() -> SafetyRouter:
    return SafetyRouter(config=SafetyRouterConfig.from_env())


@click.group()
@click.version_option(package_name="safetyrouter")
def main():
    """SafetyRouter — always get an unbiased answer."""
    pass


@main.command()
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Ollama model to use as classifier.")
def setup(model: str):
    """First-time setup: installs Ollama, pulls the classifier model, and verifies everything works."""
    click.echo(click.style("\nSafetyRouter Setup\n", bold=True) + "─" * 30)

    # Step 1 — Ollama installed?
    click.echo("\n[1/3] Checking Ollama installation...")
    if _is_ollama_installed():
        click.echo(click.style("  ✓ Ollama already installed.", fg="green"))
    else:
        _install_ollama()

    # Step 2 — Ollama running?
    click.echo("\n[2/3] Checking Ollama is running...")
    if _is_ollama_running():
        click.echo(click.style("  ✓ Ollama already running.", fg="green"))
    else:
        _start_ollama()

    # Step 3 — Pull model
    click.echo(f"\n[3/3] Pulling classifier model ({model})...")
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True, text=True
    )
    if model in result.stdout:
        click.echo(click.style(f"  ✓ {model} already pulled.", fg="green"))
    else:
        _pull_model(model)

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
