FROM python:3.9-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ ./backend/
CMD ["sh", "-c", "uv run uvicorn backend.service:app --host 0.0.0.0 --port ${PORT:-8000}"]
