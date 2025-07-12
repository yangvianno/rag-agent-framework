# --- STAGE 1: Build Environment ---
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install build essentials and dependencies (SQLite parts removed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python - && \
    ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies
RUN poetry install --no-root

# --- STAGE 2: Runtime Environment ---
FROM python:3.11-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV XDG_DATA_HOME="/app/.local/share"

# Create a non-root user
RUN adduser --system --group appuser

# Create directories and set ownership
RUN mkdir -p /app/.local/share && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Set working directory
WORKDIR /app

# Copy installed dependencies and set PATH
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY ui ./ui
COPY .env ./.env

# Expose port and run application
EXPOSE 8000
CMD ["uvicorn", "rag_agent_framework.api.server:app", "--host", "0.0.0.0", "--port", "8000"]