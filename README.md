# SafetyRouter

**Bias-aware LLM routing** — detects the type of bias in a prompt locally using [gemma3n](https://ollama.com/library/gemma3n) (via Ollama), then automatically routes to the best specialized model for that bias category.

Inspired by [RouteLLM](https://github.com/lm-sys/RouteLLM). Where RouteLLM routes on **cost vs quality**, SafetyRouter routes on **bias type** — sending each query to the model that's empirically best at handling it without bias.

---

## How It Works

```
User Prompt
    │
    ▼
┌─────────────────────────────────────┐
│  gemma3n:e2b (local, via Ollama)    │  ← FREE, runs on your machine
│  Bias Classifier                    │
│  gender: 0.92 ← highest             │
│  race:   0.05                       │
│  age:    0.01  ...                  │
└──────────────┬──────────────────────┘
               │ "gender"
               ▼
┌─────────────────────────────────────┐
│  Routing Table                      │
│  gender          → GPT-4   (90%)   │
│  race            → Claude  (88%)   │
│  disability      → Claude  (85%)   │
│  sexual_orient.  → GPT-4   (91%)   │
│  socioeconomic   → Gemini  (82%)   │
│  age             → Mixtral (83%)   │
│  nationality     → GPT-4   (87%)   │
│  religion        → Claude  (84%)   │
│  physical_appear → Mixtral (79%)   │
└──────────────┬──────────────────────┘
               │
               ▼
          GPT-4o Response
```

Accuracy scores are benchmarked against bias-specific datasets (see the [research paper](./Group10_SafetyRouter%20-%20A%20Scalable%20Bias%20Detection%20and%20Mitigation%20System%20(1).pdf)).

---

## Requirements

- **Ollama** running locally with `gemma3n:e2b` pulled
- API keys only for the providers you use (all are optional)

```bash
# Install Ollama: https://ollama.com
ollama pull gemma3n:e2b
```

---

## Installation

```bash
# Core only (classifier + routing logic)
pip install safetyrouter

# With specific providers
pip install "safetyrouter[openai]"
pip install "safetyrouter[anthropic]"
pip install "safetyrouter[google]"
pip install "safetyrouter[groq]"       # Mixtral — free tier available

# With HTTP server
pip install "safetyrouter[serve]"

# Everything
pip install "safetyrouter[all]"
```

---

## Quick Start

### Python SDK

```python
import asyncio
from safetyrouter import SafetyRouter

router = SafetyRouter()  # reads API keys from environment

async def main():
    response = await router.route("Should women be paid less than men?")
    print(f"Bias detected: {response.bias_category}")       # gender
    print(f"Routed to:     {response.selected_model}")      # gpt4
    print(f"Confidence:    {response.confidence:.0%}")       # 92%
    print(f"Response:      {response.content}")              # GPT-4's answer

asyncio.run(main())
```

**Dry run** (classify only, no API call):

```python
result = await router.route("text here", execute=False)
print(result.bias_category)   # Know the routing without spending tokens
```

**Streaming**:

```python
async for token in router.stream("Is age discrimination legal?"):
    print(token, end="", flush=True)
```

**Custom routing** (override which model handles which bias):

```python
from safetyrouter import SafetyRouter, SafetyRouterConfig

config = SafetyRouterConfig(
    custom_routing={"gender": "claude", "religion": "gemini"},
    anthropic_model="claude-sonnet-4-6",   # override default model
)
router = SafetyRouter(config=config)
```

**Fully local** (route everything to a local Ollama model):

```python
from safetyrouter import SafetyRouter, SafetyRouterConfig
from safetyrouter.providers import OllamaProvider

router = SafetyRouter(
    providers={
        "gpt4": OllamaProvider(model="llama3.2"),
        "claude": OllamaProvider(model="llama3.2"),
        "gemini": OllamaProvider(model="llama3.2"),
        "mixtral": OllamaProvider(model="mixtral"),
    }
)
```

---

### CLI

```bash
# Route a prompt
safetyrouter route "Is discrimination based on religion acceptable?"

# Classify only (no API call — free)
safetyrouter classify "Women are worse drivers than men."

# Show routing table
safetyrouter inspect

# Start HTTP server
safetyrouter serve --port 8000

# JSON output
safetyrouter route "text" --json-output

# Stream response
safetyrouter route "text" --stream
```

---

### HTTP Server

```bash
safetyrouter serve --port 8000
# or
uvicorn safetyrouter.server:app --host 0.0.0.0 --port 8000
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/routing-table` | Inspect routing config |
| `POST` | `/route` | Route + call the best model |
| `POST` | `/classify` | Classify bias only (no model call) |
| `GET` | `/docs` | Interactive Swagger UI |

```bash
# Route a prompt
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"text": "Should people be judged by their race?"}'

# Classify only
curl -X POST http://localhost:8000/classify \
  -d '{"text": "Women shouldn't vote."}'
```

---

### Docker

```bash
docker build -t safetyrouter .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  safetyrouter
```

---

## Configuration

Copy `.env.example` to `.env`:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...          # Free tier at console.groq.com

# Optional overrides
CLASSIFIER_MODEL=gemma3n:e2b  # or gemma3n:e4b for higher accuracy
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-opus-4-6
```

---

## Routing Table

| Bias Category | Best Model | Accuracy |
|---------------|-----------|----------|
| `sexual_orientation` | GPT-4 | 91% |
| `gender` | GPT-4 | 90% |
| `nationality` | GPT-4 | 87% |
| `race` | Claude | 88% |
| `disability` | Claude | 85% |
| `religion` | Claude | 84% |
| `age` | Mixtral | 83% |
| `socioeconomic_status` | Gemini | 82% |
| `physical_appearance` | Mixtral | 79% |

*Accuracy scores from benchmark evaluation in the research paper. Community contributions to improve these mappings are welcome.*

---

## Extending SafetyRouter

### Add a custom provider

```python
from safetyrouter.providers.base import BaseProvider

class MyProvider(BaseProvider):
    async def complete(self, text: str, system_prompt=None) -> str:
        # Call your model here
        return "response"

router = SafetyRouter(providers={"gpt4": MyProvider()})
```

### Add a custom bias category

```python
config = SafetyRouterConfig(
    custom_routing={
        "political": "claude",   # map new category "political" to Claude
    }
)
```

---

## Development

```bash
git clone https://github.com/rdxvicky/safetyrouter
cd safetyrouter
pip install -e ".[all]"

# Run tests
pytest tests/

# Start dev server
safetyrouter serve --reload
```

---

## Contributing

Pull requests welcome! Areas we'd love help with:

- **Better routing table** — improved benchmark accuracy scores, new bias categories
- **New providers** — Cohere, Together.ai, Mistral API, Azure OpenAI
- **Evaluation suite** — automated benchmarks to validate routing decisions
- **Async Ollama** — true async support for the classifier
- **Caching** — cache classification results for repeated prompts

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

## Citation

If you use SafetyRouter in research, please cite:

```
SafetyRouter: A Scalable Bias Detection and Mitigation System
Group 10 Research Paper, 2024
```
