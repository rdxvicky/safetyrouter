"""
FastAPI server for SafetyRouter.

Start with:
    safetyrouter serve
    # or
    uvicorn safetyrouter.server:app --host 0.0.0.0 --port 8000
"""
import logging
import threading
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .config import SafetyRouterConfig
from .models import RoutingDecision, RoutingResponse, TextInput
from .router import SafetyRouter, MAX_INPUT_LENGTH

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafetyRouter",
    description=(
        "Safety-Aware LLM Router: Bias Detection + Mental Health Risk Detection + Human Escalation. "
        "Classifies bias type and mental health risk locally at zero API cost, "
        "then routes to the best specialized model or escalates to crisis services."
    ),
    version="0.2.2",
)

# Issue #12: thread-safe lazy initialization with double-checked locking
_router: SafetyRouter | None = None
_router_lock = threading.Lock()


def get_router() -> SafetyRouter:
    global _router
    if _router is None:
        with _router_lock:
            if _router is None:
                _router = SafetyRouter(config=SafetyRouterConfig.from_env())
    return _router


# Issue #17: simple in-memory rate limiter — no external dependency required
class _RateLimiter:
    """Token-bucket rate limiter keyed by client IP."""

    def __init__(self, calls_per_minute: int = 60):
        self._limit = calls_per_minute
        self._window = 60.0
        self._calls: dict = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            timestamps = self._calls[key]
            # Drop calls outside the rolling window
            self._calls[key] = [t for t in timestamps if now - t < self._window]
            if len(self._calls[key]) >= self._limit:
                return False
            self._calls[key].append(now)
            return True


_rate_limiter = _RateLimiter(calls_per_minute=60)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Issue #17: 60 requests/minute per IP on /route and /classify."""
    if request.url.path in ("/route", "/classify"):
        client_ip = request.client.host if request.client else "unknown"
        if not _rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                {"detail": "Rate limit exceeded — max 60 requests/minute per IP."},
                status_code=429,
            )
    return await call_next(request)


@app.middleware("http")
async def input_length_middleware(request: Request, call_next):
    """Issue #16: reject request bodies that are obviously too large before parsing."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_INPUT_LENGTH * 10:
        return JSONResponse(
            {"detail": f"Request body too large (max ~{MAX_INPUT_LENGTH} chars of text)."},
            status_code=413,
        )
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok", "classifier_model": get_router().config.classifier_model}


@app.get("/routing-table")
async def routing_table():
    """Inspect the current bias-to-model routing table."""
    return get_router().inspect()


@app.post("/route", response_model=RoutingResponse)
async def route(input_data: TextInput):
    """
    Classify bias + mental health risk in text and route to the best LLM.

    If self-harm risk is high, returns emergency escalation info instead of LLM response.
    If distress/crisis risk is elevated, returns LLM response plus helpline info.
    Set `stream: true` to get a streaming response (escalation handled before any tokens).
    """
    try:
        router = get_router()

        if input_data.stream:
            # Issue #1 (server side): stream() now checks escalation before yielding tokens
            async def token_generator():
                async for token in router.stream(input_data.text):
                    yield token

            return StreamingResponse(token_generator(), media_type="text/plain")

        result = await router.route(input_data.text, execute=True)

        return RoutingResponse(
            routing_decision=RoutingDecision(
                selected_model=result.selected_model,
                bias_category=result.bias_category,
                confidence=result.confidence,
                model_accuracy=result.model_accuracy,
                reason=result.reason,
                message_content=result.content,
            ),
            bias_analysis=result.bias_analysis,
            response_time=f"{result.response_time:.3f}s",
            mental_health_scores=result.mental_health_scores,
            escalation_type=result.escalation_type,
            escalation_number=result.escalation_number,
            escalation_service=result.escalation_service,
            escalation_webchat=result.escalation_webchat,
            escalation_message=result.escalation_message,
            session_transcript_path=result.session_transcript_path,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Routing failed")
        raise HTTPException(status_code=500, detail=f"Routing failed: {e}")


@app.post("/classify")
async def classify_only(input_data: TextInput):
    """
    Only run the bias + mental health classifier — no LLM call.
    Useful for inspecting which model would be selected without incurring API costs.
    """
    try:
        result = await get_router().route(input_data.text, execute=False)
        return {
            "would_route_to": result.selected_model,
            "bias_category": result.bias_category,
            "confidence": result.confidence,
            "model_accuracy": result.model_accuracy,
            "bias_analysis": result.bias_analysis,
            "mental_health_scores": result.mental_health_scores,
            "escalation_type": result.escalation_type,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Classification failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup():
    logger.info(
        f"SafetyRouter v0.2.2 started — classifier: {get_router().config.classifier_model}"
    )
