#!/bin/bash
set -e

check_gpu() {
    echo "Checking for NVIDIA GPU support..."
    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        echo "NVIDIA GPU detected:"
        nvidia-smi
        if [ -d "/usr/local/cuda" ] || ldconfig -p | grep -q libcuda; then
            echo "CUDA libraries found - GPU acceleration enabled"
            export OLLAMA_GPU=1
            return 0
        else
            echo "Warning: CUDA libraries not found, falling back to CPU"
        fi
    else
        echo "No NVIDIA GPU detected or nvidia-smi not available"
    fi
    echo "Running in CPU mode"
    export CUDA_VISIBLE_DEVICES=""
    export OLLAMA_GPU=0
    return 1
}

echo "Starting Ollama..."
check_gpu

ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama server to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama server is ready!"
        break
    fi
    echo "Waiting... (attempt $i/60)"
    sleep 3
done

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Error: Ollama server failed to start"
    exit 1
fi

echo "Checking for qwen3:8b model..."
if ollama list | grep -q "qwen3:8b"; then
    echo "qwen3:8b already exists, skipping download."
else
    echo "Pulling qwen3:8b (this may take several minutes)..."
    if ollama pull qwen3:8b; then
        echo "qwen3:8b pulled successfully!"
    else
        echo "Warning: Failed to pull qwen3:8b. Pull it manually with: docker exec <container> ollama pull qwen3:8b"
    fi
fi

echo "Ready. Available models:"
ollama list

wait $OLLAMA_PID
