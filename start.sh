#!/bin/bash
echo "⚡ Starting AI Infrastructure..."

# 1. Install Ollama binary if not installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama binary..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 2. Stop default system service so it uses our persistent folder
sudo systemctl stop ollama 2>/dev/null || true
sudo systemctl disable ollama 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true

# 3. Set persistent model path
export OLLAMA_MODELS="/teamspace/studios/this_studio/ollama_models"

# 4. Start Ollama
echo "🚀 Starting Ollama with persistent models..."
ollama serve > /dev/null 2>&1 &
sleep 2

# 5. Start the Secure Proxy Server
echo "🔒 Starting Proxy Server on port 8000..."
python proxy_server.py
