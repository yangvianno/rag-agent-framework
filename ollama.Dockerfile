# ./ollama.Dockerfile
FROM ollama/ollama:latest

# Start the server in the background, pull the models, and then the main container process will start normally.
RUN /bin/sh -c "ollama serve & sleep 5 && ollama pull nomic-embed-text:latest"
