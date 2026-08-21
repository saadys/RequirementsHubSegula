# proxy_server.py on Lightning AI Studio
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

app = FastAPI()
SECRET_TOKEN = "segula-super-secret-key-2026"

# Keep persistent async client connected to local Ollama
client = httpx.AsyncClient(base_url="http://localhost:11434", timeout=300.0)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_all(path: str, request: Request):
    # 1. Bearer Token Auth Check
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {SECRET_TOKEN}":
        return Response(status_code=401, content="Unauthorized")

    # 2. Forward request body to Ollama with streaming enabled
    body = await request.body()
    content_type = request.headers.get("Content-Type", "application/json")
    
    req = client.build_request(
        method=request.method,
        url=f"/{path}",
        content=body,
        params=request.query_params,
        headers={"Content-Type": content_type}
    )
    
    # 3. Stream from Ollama
    resp = await client.send(req, stream=True)
    
    # 4. Stream back to client in real-time as bytes arrive
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
