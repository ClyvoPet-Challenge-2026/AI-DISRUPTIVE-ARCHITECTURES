# Build a partir da raiz do repositório.
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app/api/python

# Dependências primeiro (melhor cache de camadas)
COPY api/python/pyproject.toml api/python/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Código da API
COPY api/python/*.py ./

EXPOSE 8000
CMD ["/app/api/python/.venv/bin/uvicorn", "chatbot:app", "--host", "0.0.0.0", "--port", "8000"]
