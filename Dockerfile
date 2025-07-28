# Dockerfile

# --- STAGE 1: Build Environment ---
# Use a standard, stable Python 3.11 base image. No more conda.
FROM python:3.11-slim-bookworm AS builder

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# Install Poetry itself
RUN pip install poetry

# Set the working directory
WORKDIR /app

# Copy only the files needed for installing dependencies
COPY pyproject.toml poetry.lock* ./

# Install the project dependencies
RUN poetry install --no-root --only main

# --- STAGE 2: Final Runtime Environment ---
FROM python:3.11-slim-bookworm AS runtime

# Set the working directory
WORKDIR /app

# Copy the installed dependencies and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# THIS IS THE FIX: Copy executables like 'uvicorn' into the PATH
COPY --from=builder /usr/local/bin /usr/local/bin

# Create a non-root user for security
RUN adduser --system --group --home /app appuser

# Copy your application code
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY ui ./ui
COPY .env ./.env

# Grant ownership to the app user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port and run the application
EXPOSE 8000
CMD ["uvicorn", "src.rag_agent_framework.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]