# proxy_server.py on Lightning AI Studio
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(
    title="Segula Sovereign AI Gateway",
    description="Unified authenticated gateway for DeepSeek-R1 (vLLM) and Qwen3-Embedding (Ollama)"
)

SECRET_TOKEN = "segula-super-secret-key-2026"

# Clients asynchrones locaux avec pool de connexion robuste
limits = httpx.Limits(max_connections=200, max_keepalive_connections=100)
vllm_client = httpx.AsyncClient(base_url="http://127.0.0.1:8001", timeout=300.0, limits=limits)
ollama_client = httpx.AsyncClient(base_url="http://127.0.0.1:11434", timeout=300.0, limits=limits)


@app.get("/")
@app.get("/health")
async def health_check():
    """Public healthcheck endpoint for quick browser testing and status verification."""
    vllm_ok = False
    ollama_ok = False
    try:
        r = await vllm_client.get("/v1/models", timeout=2.0)
        vllm_ok = (r.status_code == 200)
    except Exception:
        pass

    try:
        r = await ollama_client.get("/api/tags", timeout=2.0)
        ollama_ok = (r.status_code == 200)
    except Exception:
        pass

    overall_status = "healthy" if (vllm_ok and ollama_ok) else "starting"
    return JSONResponse(
        status_code=200 if overall_status == "healthy" else 503,
        content={
            "status": overall_status,
            "service": "Segula Sovereign AI Gateway",
            "vllm_deepseek_r1": "ready" if vllm_ok else "initializing",
            "ollama_embeddings": "ready" if ollama_ok else "initializing",
            "model": "casperhansen/deepseek-r1-distill-qwen-14b-awq",
            "embedding_model": "qwen3-embedding:0.6b",
            "auth_required": True
        }
    )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_all(path: str, request: Request):
    # 1. Vérification du Bearer Token de sécurité
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {SECRET_TOKEN}":
        return Response(status_code=401, content="Unauthorized: Invalid Segula API Token")

    # 2. Router intelligent : OpenAI API (/v1/...) -> vLLM | Ollama API (/api/...) -> Ollama
    target_client = vllm_client if path.startswith("v1") else ollama_client

    body = await request.body()
    content_type = request.headers.get("Content-Type", "application/json")
    
    req = target_client.build_request(
        method=request.method,
        url=f"/{path}",
        content=body,
        params=request.query_params,
        headers={"Content-Type": content_type}
    )
    
    # 3. Envoi sécurisé avec capture d'erreur propre
    try:
        resp = await target_client.send(req, stream=True)
        return StreamingResponse(
            resp.aiter_raw(),
            status_code=resp.status_code,
            headers={
                "Content-Type": resp.headers.get("Content-Type", "application/json"),
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            },
            background=resp.aclose
        )
    except httpx.ConnectError:
        service_name = "vLLM (port 8001)" if target_client == vllm_client else "Ollama (port 11434)"
        return Response(
            status_code=503,
            content=f"Service Unavailable: Backend is waiting for {service_name} to finish startup."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
