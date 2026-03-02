"""
CLI for SafetyRouter.

Usage:
    safetyrouter route "Should women be engineers?"
    safetyrouter classify "text here"
    safetyrouter serve --port 8000
    safetyrouter inspect
"""
import asyncio
import json
import sys

import click

from .config import SafetyRouterConfig
from .router import SafetyRouter

OLLAMA_ERROR_MSG = """
Ollama is not running. SafetyRouter needs Ollama to classify bias locally.

Fix it in 2 steps:
  1. Install Ollama:   https://ollama.com/download
  2. Pull the model:   ollama pull gemma3n:e2b
  3. Start Ollama:     ollama serve

Then try again.
"""


def _handle_error(e: Exception):
    """Convert known exceptions into clean user-facing messages."""
    msg = str(e)
    if "Failed to connect to Ollama" in msg or "ConnectionError" in msg or "Connection refused" in msg:
        click.echo(click.style("Error:", fg="red", bold=True) + OLLAMA_ERROR_MSG, err=True)
        sys.exit(1)
    if "OPENAI_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "OPENAI_API_KEY not set.\nAdd it to your .env file or run: export OPENAI_API_KEY=sk-...", err=True)
        sys.exit(1)
    if "ANTHROPIC_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "ANTHROPIC_API_KEY not set.\nAdd it to your .env file or run: export ANTHROPIC_API_KEY=sk-ant-...", err=True)
        sys.exit(1)
    if "GOOGLE_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "GOOGLE_API_KEY not set.\nAdd it to your .env file or run: export GOOGLE_API_KEY=AIza...", err=True)
        sys.exit(1)
    if "GROQ_API_KEY" in msg:
        click.echo(click.style("Error: ", fg="red", bold=True) + "GROQ_API_KEY not set.\nAdd it to your .env file or run: export GROQ_API_KEY=gsk_...", err=True)
        sys.exit(1)
    # Generic fallback
    click.echo(click.style("Error: ", fg="red", bold=True) + msg, err=True)
    sys.exit(1)


def _get_router() -> SafetyRouter:
    return SafetyRouter(config=SafetyRouterConfig.from_env())


@click.group()
@click.version_option(package_name="safetyrouter")
def main():
    """SafetyRouter — always get an unbiased answer."""
    pass


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
