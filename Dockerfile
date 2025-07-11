# Dockerfile

# --- STAGE 1: Build Environment ---
# Using a full Python image for the build stage to compile SQLite and install dependencies.
FROM python:3.11-slim-bookworm AS builder

# Set environment variables for Python and Poetry
ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install build essentials and other dependencies needed to compile sqlite
# and for installing Poetry (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libsqlite3-dev unzip wget curl && \
    rm -rf /var/lib/apt/lists/*

# ==> COMPILE SQLITE <==
# Download, compile, and install a newer version of SQLite.
# This ensures chromadb (or similar) can use the required SQLite version.
ENV SQLITE_VERSION 3.45.1
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3450100.tar.gz -O sqlite.tar.gz && \
    tar -xvf sqlite.tar.gz && \
    cd sqlite-autoconf-3450100 && \
    ./configure && \
    make && \
    make install && \
    ldconfig /usr/local/lib # Update dynamic linker run-time bindings

# Install Poetry and make it globally accessible via symlink
RUN curl -sSL https://install.python-poetry.org | python - && \
    chmod +x $POETRY_HOME/bin/poetry && \
    ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry # Symlink to make 'poetry' command globally available

# Set working directory
WORKDIR /app

# Copy project files for dependency installation
COPY pyproject.toml poetry.lock* ./

# Tell chromadb's dependency to use a pre-compiled version of sqlite3 if needed
ENV HNSWLIB_NO_NATIVE=1

# Install project dependencies
# --no-root: no longer needed, as `poetry install --no-root` defaults to production dependencies
RUN poetry install --no-root

# --- STAGE 2: Runtime Environment ---
# Start from a slim image for a smaller final size
FROM python:3.11-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app/src:$PYTHONPATH" 

# ==> SQLITE FIX <==
# Copy the compiled sqlite3 libraries and binary from the builder stage
COPY --from=builder /usr/local/lib/libsqlite3.so.0* /usr/local/lib/
COPY --from=builder /usr/local/bin/sqlite3 /usr/local/bin/

# Set the library path so the system can find the new sqlite3 library
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH" 

# Set XDG_DATA_HOME to a writable directory for non-root user
# This prevents permission errors when applications try to write to default data directories.
ENV XDG_DATA_HOME="/app/.local/share"

# Create a non-root user for security
RUN adduser --system --group appuser
USER appuser

# Set working directory
WORKDIR /app

# Copy installed dependencies (virtual environment) from the builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" 

# Copy the application code and necessary files
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY ui ./ui
COPY .env ./.env 

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the FastAPI application using uvicorn
CMD ["uvicorn", "rag_agent_framework.api.server:app", "--host", "0.0.0.0", "--port", "8000"]