#!/usr/bin/env bash
set -e

echo "Pulling llama3.2:3b (fastest, ~2GB)..."
docker exec documind-ollama ollama pull llama3.2:3b

echo ""
echo "Done! llama3.2:3b is ready."
echo "To also pull mistral:7b (better quality, ~4.1GB), run:"
echo "  docker exec documind-ollama ollama pull mistral:7b"
