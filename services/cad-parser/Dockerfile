# services/cad-parser/Dockerfile

# Use the official Conda-Forge Mambaforge base for reproducible OCC deps
FROM condaforge/mambaforge:23.3.1-0

# Install necessary packages
RUN mamba install -y -c conda-forge \
    pythonocc-core \
    fastapi \
    uvicorn \
    pydantic \
    python-multipart \
    pytest && \
    mamba clean -afy

# Create and switch to a non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /home/appuser
USER appuser

# Set working directory
WORKDIR /home/appuser/app

# Copy the application code
COPY --chown=appuser:appuser app/ ./app

# Copy test files
COPY --chown=appuser:appuser test/ ./test

# Expose the port
EXPOSE 8000

# Default command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]