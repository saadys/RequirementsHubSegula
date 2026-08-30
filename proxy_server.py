# proxy_server.py on Lightning AI Studio
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

app = FastAPI(title="Segula Sovereign AI Gateway")
SECRET_TOKEN = "segula-super-secret-key-2026"

# Clients asynchrones locaux avec pool de connexion robuste
vllm_client = httpx.AsyncClient(base_url="http://127.0.0.1:8001", timeout=300.0)
ollama_client = httpx.AsyncClient(base_url="http://127.0.0.1:11434", timeout=300.0)

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
