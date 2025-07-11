# Dockerfile

# --- Stage 1: The Builder ---
# Use the full, official Python image which has Python and its build tools pre-installed.
FROM python:3.11-bullseye AS builder

# ==> COMPILE SQLITE <==
# Install build essentials and other dependencies needed to compile sqlite
RUN apt-get update && apt-get install -y build-essential libsqlite3-dev unzip wget && rm -rf /var/lib/apt/lists/*

# Download and install a newer version of SQLite
ENV SQLITE_VERSION 3.45.1
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3450100.tar.gz -O sqlite.tar.gz && \
    tar -xvf sqlite.tar.gz && \
    cd sqlite-autoconf-3450100 && \
    ./configure && \
    make && \
    make install

# Set the working directory
WORKDIR /app

# Install Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry to create the virtual environment inside the project directory
RUN poetry config virtualenvs.in-project true

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Tell chromadb's dependency to use a pre-compiled version of sqlite3
ENV HNSWLIB_NO_NATIVE=1

# Install dependencies into the .venv directory.
RUN poetry install --no-root --without dev


# --- Stage 2: The Final Image ---
# Start from the slim image for a smaller final size
FROM python:3.11-slim-bullseye

# ==> FIX STARTS HERE <==
# Copy the compiled sqlite3 libraries and binary from the builder stage
COPY --from=builder /usr/local/lib/libsqlite3.so.0* /usr/local/lib/
COPY --from=builder /usr/local/bin/sqlite3 /usr/local/bin/

# Set the library path so the system can find the new sqlite3 library
ENV LD_LIBRARY_PATH="/usr/local/lib"
# ==> FIX ENDS HERE <==

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY src ./src

# Copy the configuration directory into the container
COPY config ./config

# Copy the scripts directory into the container
COPY scripts ./scripts

# Set the PATH to use the virtual environment's Python interpreter
ENV PATH="/app/.venv/bin:$PATH"

# Tell Python where to find your source code to fix import errors
ENV PYTHONPATH=/app/src

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using the Python from the virtual env
CMD ["uvicorn", "rag_agent_framework.api.server:app", "--host", "0.0.0.0", "--port", "8000"]