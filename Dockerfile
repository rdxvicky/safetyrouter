# SafetyRouter — Docker Image
# Bundles Ollama + gemma3n classifier + FastAPI server.
#
# Build:  docker build -t safetyrouter .
# Run:    docker run -p 8000:8000 \
#           -e OPENAI_API_KEY=sk-... \
#           -e ANTHROPIC_API_KEY=sk-ant-... \
#           safetyrouter

FROM python:3.11-slim

WORKDIR /app

# System deps for Ollama
RUN apt-get update && apt-get install -y curl procps && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python package with all provider extras
COPY pyproject.toml .
COPY safetyrouter/ ./safetyrouter/
RUN pip install --no-cache-dir ".[all]"

# Pre-pull gemma3n classifier model so it's baked into the image
# Use e2b (5.6 GB) for speed; swap to e4b for higher accuracy
RUN ollama serve & \
    sleep 5 && \
    ollama pull gemma3n:e2b && \
    pkill ollama

EXPOSE 8000

# Start Ollama + SafetyRouter server
CMD ["sh", "-c", "ollama serve & sleep 3 && safetyrouter serve --host 0.0.0.0 --port 8000"]
