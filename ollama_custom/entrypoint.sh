# ollama_custom/entrypoint.sh
#!/bin/bash

# Start ollama server in the background
echo "Starting Ollama server in background..."
ollama serve &
SERVER_PID=$! # Capture the PID of the background process

echo "Waiting for Ollama server to be responsive..."
# Loop until the Ollama server responds to a basic command like 'ollama list'
# This indicates the server is up and ready to accept commands.
until ollama list > /dev/null 2>&1; do
  echo "Ollama server not yet ready, waiting..."
  sleep 5
done
echo "Ollama server is responsive."

# Now that the server is running, pull the required model
echo "Pulling nomic-embed-text:latest model..."
ollama pull nomic-embed-text:latest

echo "Model pull command finished."

# Keep the main Ollama serve process running by waiting for its PID
wait $SERVER_PID