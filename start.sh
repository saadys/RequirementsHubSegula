#!/bin/bash
set -e
echo "⚡ Starting Segula Sovereign AI Infrastructure (vLLM + Ollama)..."
# 1. Chemins et PATH
export PATH="/usr/local/bin:$PATH"
export HF_HOME="/teamspace/studios/this_studio/hf_cache"
export OLLAMA_MODELS="/teamspace/studios/this_studio/ollama_models"
export OLLAMA_HOST="127.0.0.1:11434"
# 2. Installer Ollama si absent
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama binary..."
    curl -fsSL https://ollama.com/install.sh | sh
fi
# 3. Arrêter proprement les anciens processus
sudo systemctl stop ollama 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
pkill -f "vllm" 2>/dev/null || true
pkill -f "proxy_server.py" 2>/dev/null || true
sleep 2
# 4. Démarrage garanti d'Ollama (Embeddings)
echo "🚀 1/3 Starting Ollama for embeddings (Port 11434)..."
ollama serve > ollama.log 2>&1 &
echo "⏳ Waiting for Ollama engine to be ready..."
until curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Ollama is ready on port 11434!"
# 5. Démarrage de vLLM avec modèle AWQ persistant (Port 8001)
echo "🚀 2/3 Starting vLLM with DeepSeek-R1 14B AWQ (Port 8001)..."
vllm serve casperhansen/deepseek-r1-distill-qwen-14b-awq \
    --download-dir "$HF_HOME" \
    --host 127.0.0.1 \
    --port 8001 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 16 \
    --enforce-eager \
    --disable-log-stats \
    --served-model-name "casperhansen/deepseek-r1-distill-qwen-14b-awq" \
    > vllm.log 2>&1 &
echo "⏳ Loading vLLM weights from local disk (15-20s)..."
until curl -s http://127.0.0.1:8001/v1/models > /dev/null 2>&1; do
    sleep 2
done
echo "✅ vLLM is ready on port 8001!"
# 6. Démarrage du Proxy Sécurisé (Port 8000)
echo "🔒 3/3 Starting Secure Proxy Server on port 8000..."
python proxy_server.py
