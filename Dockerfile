# Dockerfile

# 1. Use an official Python runtime as a parent image
# Using the slim-bullseye version for a smaller image size
FROM python:3.11-slim-bullseye

# 2. Set the working directory in the container
WORKDIR /app

# 3. Set environment variables
# Prevents Python from writing .pyc files to the container
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# 4. Install system dependencies that Poetry might need
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# 5. Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the system's PATH
ENV PATH="/root/.local/bin:$PATH"

# 6. Copy only the dependency definition files to leverage Docker layer caching
COPY poetry.lock pyproject.toml ./

# 7. Install project dependencies
# --no-root: Don't install the project itself, just the dependencies
# --no-dev: Don't install development dependencies (like pytest)
RUN poetry install --no-root --no-dev

# 8. Copy the rest of your application's source code into the container
COPY . .

# 9. Command to run the application (e.g., starting the FastAPI server)
# This will be overridden by docker-compose, but it's good practice to have a default.
# Expose the port the app runs on
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.rag_agent_framework.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
