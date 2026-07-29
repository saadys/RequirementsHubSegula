FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY backend/ ./backend/
COPY tests/ ./tests/

# SQLite + ChromaDB data persisted via volume
VOLUME /app/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
