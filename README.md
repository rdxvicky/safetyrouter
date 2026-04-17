# SafetyRouter

**A Safety-Aware LLM Routing Framework** — detects bias type and mental health risk locally, routes to the model best equipped for that category, rephrases biased input, and escalates to human crisis services when needed.

No matter what you ask, SafetyRouter ensures the response comes from the model with the strongest track record for fairness in that specific domain — and steps aside entirely when a human is the right answer.

---

## How It Works

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────┐
│  Local Safety Classifier                │  ← FREE, runs on your machine
│                                         │
│  BIAS                                   │
│    gender: 0.92 ← highest               │
│    race:   0.05, age: 0.01, ...         │
│                                         │
│  MENTAL HEALTH                          │
│    self_harm:          0.03             │
│    severe_distress:    0.08             │
│    existential_crisis: 0.04             │
│    emotional_dependency: 0.11           │
└────────┬─────────────────────┬──────────┘
         │                     │
         ▼                     ▼
  self_harm ≥ 0.70?    distress/crisis ≥ 0.60?
  EMERGENCY escalation  HELPLINE + LLM response
  (skip LLM entirely)   (crisis line shown below response)
         │
         ▼  (below threshold — normal routing)
┌─────────────────────────────────────────┐
│  Routing Table                          │
│  gender          → GPT-4   (96.7%)      │
│  race            → Claude  (83.3%)      │
│  disability      → GPT-4   (100.0%)     │
│  sexual_orient.  → Claude  (83.3%)      │
│  socioeconomic   → Claude  (96.7%)      │
│  age             → Claude  (100.0%)     │
│  nationality     → Gemini  (96.7%)      │
│  religion        → GPT-4   (96.7%)      │
│  physical_appear → Gemini  (100.0%)     │
└────────────────────┬────────────────────┘
                     │
                     ▼
              Unbiased Response
```

Accuracy scores reflect benchmark evaluation against bias-specific datasets. Community contributions to improve these mappings are welcome.

---

## Installation

```bash
pip install safetyrouter
safetyrouter setup
```

`safetyrouter setup` walks you through everything interactively:

```
SafetyRouter Setup
──────────────────────────────

[1/5] Checking Ollama installation...
      ✓ Ollama already installed.

[2/5] Checking Ollama is running...
      ✓ Ollama already running.

[3/5] Pulling classifier model (gemma3n:e2b)...
      ✓ gemma3n:e2b is ready.

[4/5] A few quick questions to personalize your experience...

  What should we call you? (press Enter to skip): Alex

  Age range:
    [1] Under 18    [2] 18–25    [3] 26–40
    [4] 41–60       [5] 60+      [0] Prefer not to say

  Country (for safety resources):
  Enter country code or name: US
  ✓ Crisis resources loaded for United States
     Emergency  : 911
     Crisis line: 988 — 988 Suicide & Crisis Lifeline
     Web chat   : https://988lifeline.org/chat

[5/5] Configure LLM provider API keys...
      Keys saved to ~/.safetyrouter.env

  OpenAI       key (sk-...): sk-proj-...
  ✓ OpenAI key saved.
  Anthropic    key (sk-ant-...): [Enter]
  — Anthropic skipped
  Groq         key (gsk_...): gsk_live-...
  ✓ Groq key saved.

✓ Setup complete! SafetyRouter is ready to use.
```

**API keys are saved to `~/.safetyrouter.env`** and loaded automatically — no manual `export` needed. You can skip any provider and add keys later.

**Ollama outdated?** Setup detects it and offers to update in-place:

```
[3/5] Pulling classifier model (gemma3n:e2b)...
      Error: requires a newer version of Ollama.

      Ollama is outdated and cannot run gemma3n:e2b.
      Update Ollama now? (recommended) [Y/n]: Y
      ✓ Ollama updated.
      ✓ gemma3n:e2b is ready.
```

If you decline the update, setup lets you pick a compatible fallback model (e.g. `gemma2:2b`, `llama3.2:3b`).

> **Bring your own model** — `safetyrouter setup --model <model-name>` uses any Ollama model as the classifier.
> **Skip API key step** — `safetyrouter setup --skip-keys` if you prefer to configure keys manually.

### Install with specific providers

```bash
pip install "safetyrouter[openai]"      # GPT-4o
pip install "safetyrouter[anthropic]"   # Claude
pip install "safetyrouter[google]"      # Gemini
pip install "safetyrouter[groq]"        # Mixtral — free tier available
pip install "safetyrouter[serve]"       # HTTP server
pip install "safetyrouter[all]"         # Everything
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
    print(f"Response:      {response.content}")              # unbiased answer

asyncio.run(main())
```

**Check for crisis escalation:**

```python
response = await router.route(text)

if response.escalation_type == "emergency":
    # self_harm score ≥ 0.70 — LLM was skipped
    print(response.escalation_message)          # emergency number + crisis line
    print(response.session_transcript_path)     # ~/.safetyrouter/sessions/<ts>.json

elif response.escalation_type == "helpline":
    # distress score ≥ 0.60 — LLM responded, helpline appended
    print(response.content)                     # LLM response
    print(response.escalation_message)          # "Support line: 988 — ..."
```

**Dry run** (classify only, no API call):

```python
result = await router.route("text here", execute=False)
print(result.bias_category)          # know the routing without spending tokens
print(result.mental_health_scores)   # {"self_harm": 0.02, "severe_distress": 0.07, ...}
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
# First-time setup (Ollama + classifier model + user profile + API keys)
safetyrouter setup

# Skip the API key step
safetyrouter setup --skip-keys

# Use a custom classifier model
safetyrouter setup --model llama3.2

# Route a prompt — outputs structured JSON
safetyrouter route "Is discrimination based on religion acceptable?"

# Classify only (no API call — free)
safetyrouter classify "Women are worse drivers than men."

# Show routing table
safetyrouter inspect

# Start HTTP server
safetyrouter serve --port 8000

# Stream response
safetyrouter route "text" --stream
```

**`route` outputs structured JSON** with routing decision, per-category bias scores, rephrased text, and response time:

```json
{
  "routing_decision": {
    "selected_model": "claude",
    "bias_category": "race",
    "confidence": 0.8,
    "model_accuracy": 83.3,
    "reason": "Routed to claude for 'race' bias (benchmark accuracy: 83.3%)",
    "message_content": "No, people should not be judged by their race..."
  },
  "bias_analysis": {
    "race": { "probability": 0.8 },
    "gender": { "probability": 0.02 },
    "age": { "probability": 0.01 },
    "religion": { "probability": 0.01 },
    "nationality": { "probability": 0.03 },
    "disability": { "probability": 0.0 },
    "socioeconomic_status": { "probability": 0.0 },
    "sexual_orientation": { "probability": 0.0 },
    "physical_appearance": { "probability": 0.0 },
    "demographic": { "probability": 0.0 },
    "others": { "probability": 0.0 },
    "highest_probability_category": { "category": "race", "probability": 0.8 },
    "rephrased_text": {
      "original": "Should people be judged by their race?",
      "rephrased": "Should people be judged by their individual character and actions?",
      "changes_made": [
        "Replaced 'race' with 'individual character and actions' to remove racial framing"
      ],
      "meaning_preserved": true
    }
  },
  "response_time": "18.059s"
}
```

**Emergency escalation** outputs a JSON block with crisis resources (no LLM response):

```json
{
  "routing_decision": { "selected_model": "escalated", ... },
  "escalation": {
    "type": "emergency",
    "emergency_number": "911",
    "crisis_service": "988 Suicide & Crisis Lifeline",
    "webchat": "https://988lifeline.org/chat",
    "session_transcript_path": "~/.safetyrouter/sessions/2026-03-17T14-22-01.json"
  },
  "response_time": "1.2s"
}
```

**Helpline escalation** includes an `escalation` block alongside the normal response:

```json
{
  "routing_decision": { ... },
  "bias_analysis": { ... },
  "escalation": {
    "type": "helpline",
    "number": "988",
    "service": "988 Suicide & Crisis Lifeline",
    "webchat": "https://988lifeline.org/chat"
  },
  "response_time": "9.4s"
}
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
| `POST` | `/route` | Route + call the best model (includes escalation fields) |
| `POST` | `/classify` | Classify bias + mental health only (no model call) |
| `GET` | `/docs` | Interactive Swagger UI |

```bash
# Route a prompt
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"text": "Should people be judged by their race?"}'

# Classify only — returns bias scores + mental health scores + escalation_type
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel like there is no point to anything."}'
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

## Mental Health Safety & Crisis Escalation

SafetyRouter includes a two-tier human escalation system that runs alongside bias detection at zero extra API cost.

### How escalation works

The local classifier scores four mental health risk signals on every request:

| Signal | Description |
|--------|-------------|
| `self_harm` | Explicit mentions of self-harm, suicide, or wanting to die |
| `severe_distress` | Expressions of hopelessness, despair, or overwhelming pain |
| `existential_crisis` | Loss of purpose, meaninglessness, or reasons to live |
| `emotional_dependency` | Unhealthy attachment, isolation, or emotional reliance |

These scores trigger two escalation tiers:

| Tier | Condition | Action |
|------|-----------|--------|
| **EMERGENCY** | `self_harm` ≥ 0.70 | LLM is skipped entirely. Red crisis box shown with emergency number + helpline. Session transcript saved. |
| **HELPLINE** | `severe_distress` or `existential_crisis` ≥ 0.60 | LLM responds normally. Helpline number and webchat appended below response. |

### Supported countries

Crisis resources are built in for 15 countries:

| Code | Country | Emergency | Crisis Line |
|------|---------|-----------|-------------|
| US | United States | 911 | 988 Suicide & Crisis Lifeline |
| UK | United Kingdom | 999 | 116 123 (Samaritans) |
| CA | Canada | 911 | 1-833-456-4566 (Crisis Services Canada) |
| AU | Australia | 000 | 13 11 14 (Lifeline) |
| IN | India | 112 | 9152987821 (iCall) |
| NZ | New Zealand | 111 | 1737 (Need to Talk?) |
| DE | Germany | 112 | 0800 111 0 111 (Telefonseelsorge) |
| FR | France | 15 | 3114 |
| JP | Japan | 119 | 0120-783-556 (Inochi no Denwa) |
| BR | Brazil | 192 | 188 (CVV) |
| MX | Mexico | 911 | 800 290 0024 (SAPTEL) |
| ZA | South Africa | 10111 | 0800 567 567 (SADAG) |
| SG | Singapore | 999 | 1800 221 4444 (SOS) |
| IE | Ireland | 999 | 116 123 (Samaritans Ireland) |
| MY | Malaysia | 999 | 015-4882 3500 (Befrienders KL) |

Other countries fall back to a global helpline reference. PRs to add more countries are very welcome.

### Session transcripts

When EMERGENCY escalation fires, SafetyRouter saves a JSON transcript to `~/.safetyrouter/sessions/` with the user profile, mental health scores, and original text. This can be shared with a crisis counselor or support contact.

### Thresholds

Thresholds can be adjusted via environment variables or config:

```env
SR_SELF_HARM_THRESHOLD=0.70   # default — triggers EMERGENCY
SR_HELPLINE_THRESHOLD=0.60    # default — triggers HELPLINE
```

```python
config = SafetyRouterConfig(
    self_harm_threshold=0.80,
    helpline_threshold=0.65,
)
```

---

## Configuration

### PyPI users
Run `safetyrouter setup` — all settings are saved to `~/.safetyrouter.env` and loaded automatically.

### Developers / self-hosted
Copy `.env.example` to `.env` in your project root:

```env
# LLM Provider API keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...          # Free tier at console.groq.com

# Classifier model — defaults to gemma3n:e2b
CLASSIFIER_MODEL=gemma3n:e2b
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-opus-4-5-20251101

# User profile (set by `safetyrouter setup` or manually)
SR_USER_NAME=Alex
SR_USER_AGE_RANGE=18-25
SR_USER_COUNTRY=US

# Mental health escalation thresholds
SR_SELF_HARM_THRESHOLD=0.70
SR_HELPLINE_THRESHOLD=0.60
```

Priority order: environment variables → local `.env` → `~/.safetyrouter.env`.

---

## Routing Table

Derived from the [LLM Bias Evaluator](https://github.com/rdxvicky/llm-bias-evaluator) — 270 samples across 9 categories (StereoSet, CrowS-Pairs, BBQ, HolisticBias, BOLD).

| Bias Category | Best Model | Accuracy |
|---------------|-----------|----------|
| `gender` | GPT-4 | 96.7% |
| `disability` | GPT-4 | 100.0% |
| `religion` | GPT-4 | 96.7% |
| `race` | Claude | 83.3% |
| `age` | Claude | 100.0% |
| `sexual_orientation` | Claude | 83.3% |
| `socioeconomic_status` | Claude | 96.7% |
| `nationality` | Gemini | 96.7% |
| `physical_appearance` | Gemini | 100.0% |

**Key findings:** Age is universally solved (all models 100%). Race is hardest (all below 84%). No single model dominates — routing consistently outperforms any fixed choice.

*Community contributions to improve these mappings are welcome.*

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

- **Crisis resource coverage** — add more countries to `safetyrouter/crisis.py`
- **Better routing table** — improved benchmark accuracy scores, new bias categories
- **New providers** — Cohere, Together.ai, Mistral API, Azure OpenAI
- **Evaluation suite** — automated benchmarks to validate routing and escalation decisions
- **Async Ollama** — true async support for the classifier
- **Caching** — cache classification results for repeated prompts

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

## Citation

If you use SafetyRouter in research, please cite:

```
SafetyRouter: A Safety-Aware LLM Routing Framework for Bias Detection,
Mental Health Risk Detection, and Human Escalation
https://github.com/rdxvicky/safetyrouter
```
