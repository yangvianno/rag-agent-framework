# services/pdf-parser/Dockerfile

# Base image: lightweight Python
FROM python:3.10-slim

# Create a non-root user for security
RUN useradd -m appuser

# Set the working directory for the application
WORKDIR /home/appuser/app

# Install dependecies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY --chown=appuser:appuser app/ .

USER appuser

EXPOSE 8000

# Launch with multiple workers for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]