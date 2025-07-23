# Dockerfile

# --- STAGE 1: Build Environment ---
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install build essentials and dependencies
# We add 'mamba' for installing from conda-forge and the libs python-occ-core needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl mamba libgl1-mesa-glx libglib2.0-0 && \
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

# CAD Parsing Library
RUN . /app/.venv/bin/activate && mamba install -c conda-forge python-occ-core=7.7.2 --yes

# --- STAGE 2: Runtime Environment ---
FROM python:3.11-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# --- CHANGE 1: Create a non-root user with a home directory ---
# This fixes the permission error by giving the user a writable home.
RUN adduser --system --group --home /app appuser

# Set working directory
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY ui ./ui
COPY .env ./.env

# --- CHANGE 2: Grant ownership of the entire app directory ---
# This ensures the user can write anywhere inside /app.
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port and run application
EXPOSE 8000
# --- CHANGE 3: Added --reload for easier development ---
CMD ["uvicorn", "src.rag_agent_framework.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]