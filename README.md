# ⚡ Lightning AI & Local LLM Setup Guide

This guide explains how to deploy and connect a **free/cloud GPU instance on Lightning AI** (Ollama + DeepSeek-R1 14B + Qwen3 Embedding) to power the **Segula AI Requirement Hub** with 100% offline data sovereignty and zero cloud API dependency.

---

## 🏗️ Architecture Overview

```mermaid
flowchart LR
    subgraph Local["Your Machine (Local Docker / Dev)"]
        Frontend["React UI (Vite :5173)"] --> Backend["FastAPI Backend (:8000)"]
        Backend --> DB[("PostgreSQL + pgvector (:5435)")]
    end

    subgraph LightningAI["Lightning AI Studio (T4 / A10G GPU)"]
        Proxy["Proxy Server (FastAPI :8000)\nBearer Auth + Streaming"]
        Ollama["Ollama Daemon (:11434)\nPersistent Storage"]
        DeepSeek["deepseek-r1:14b\n(Reasoning & 5 Pillars)"]
        QwenEmbed["qwen3-embedding:0.6b\n(RAG Embeddings 1024-dim)"]
        
        Proxy --> Ollama
        Ollama --> DeepSeek
        Ollama --> QwenEmbed
    end

    Backend -- "HTTPS (Port 8000 + Bearer Token)" --> Proxy
```

---

## 🚀 Part 1: Setup on Lightning AI Studio

### 1. Create a Studio
1. Go to [lightning.ai](https://lightning.ai/) and create a new **Studio**.
2. Select hardware: **T4 GPU (16 GB VRAM)** (Free tier / Pay-as-you-go) or **A10G GPU**.

### 2. Upload the Setup Files
Make sure the following two files from this repo are in your Studio directory (`/teamspace/studios/this_studio/`):
* `start.sh`
* `proxy_server.py`

### 3. Install Proxy Dependencies
Open a terminal in your Lightning AI Studio and run:
```bash
pip install fastapi uvicorn httpx
```

### 4. Make `start.sh` Executable & Run It
```bash
chmod +x start.sh
./start.sh
```

`start.sh` automatically:
* Installs the Ollama binary (if not already installed).
* Configures persistent model storage in `/teamspace/studios/this_studio/ollama_models` so your downloaded models are not lost when the Studio stops.
* Starts `ollama serve` in the background.
* Starts the secure streaming reverse proxy (`proxy_server.py`) on port `8000`.

### 5. Pull the AI Models in Ollama
Open a **new terminal tab** in Lightning AI Studio and pull the required models:

```bash
# 1. Primary 5-Pillar Reasoning Model (9.0 GB)
ollama pull deepseek-r1:14b

# 2. Primary RAG Embedding Model (639 MB, 1024 dimensions)
ollama pull qwen3-embedding:0.6b

# (Optional: Lightweight 8B Model baseline)
ollama pull qwen3:8b
```

Verify your models are installed:
```bash
ollama list
```
Expected output:
```text
NAME                    ID              SIZE      MODIFIED
deepseek-r1:14b         c333b7232bdb    9.0 GB    Just now
qwen3-embedding:0.6b    ac6da0dfba84    639 MB    Just now
```

### 6. Expose Port 8000 on Lightning AI
1. In Lightning AI Studio, open the **Ports / Plugin** panel on the right sidebar.
2. Find or add port **`8000`**.
3. Set visibility to **Public / Cloudspace**.
4. Copy the generated public URL. It looks like:
   ```text
   https://8000-01m03qzk5mcssvw8pk45ke8839.cloudspaces.litng.ai
   ```

---

## 💻 Part 2: Connect the Local Codebase

### 1. Configure `.env`
On your local machine, copy the template and configure your environment:
```bash
cp .env.example .env
```

Open `.env` and set the following variables:

```bash
# Enable Local LLM Mode
USE_LOCAL_LLM=true

# Paste your Lightning AI Studio public URL (NO trailing slash, NO trailing space)
OLLAMA_BASE_URL=https://8000-YOUR-STUDIO-ID.cloudspaces.litng.ai

# Bearer Token (must match SECRET_TOKEN in proxy_server.py)
OLLAMA_API_KEY=segula-super-secret-key-2026

# Model Names
LOCAL_MODEL=ollama/deepseek-r1:14b
LOCAL_EMBEDDING_MODEL=qwen3-embedding:0.6b

# Vector Dimension for qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024
```

> ⚠️ **Important:** Ensure there is **no trailing space** after model names (e.g. `ollama/deepseek-r1:14b`, not `ollama/deepseek-r1:14b `).

---

## 🧪 Part 3: Quick Health Check & Testing

### 1. Test Proxy Authentication & Embedding
Run this command from your local terminal to verify that your proxy and embedding model are working:

```bash
curl -X POST "https://8000-YOUR-STUDIO-ID.cloudspaces.litng.ai/api/embed" \
  -H "Authorization: Bearer segula-super-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-embedding:0.6b", "input": "Segula AI Hub Healthcheck"}'
```
If configured correctly, you will receive HTTP `200 OK` with the embedding vector.

### 2. Run the Benchmark Suite
To test all 20 enterprise test cases against your Lightning AI instance:
```bash
python tests/benchmark_models.py
```

### 3. Launch the Application

The compose stack runs the migration as a one-shot job that must finish before
the API starts, so the schema is never behind the code:

```bash
cp docker/env/.env.postgres.example docker/env/.env.postgres  # first run only
docker compose -f docker/docker-compose.yml up
```

Or run the services by hand:

```bash
# Start PostgreSQL & pgvector container
docker compose -f docker/docker-compose.yml up -d postgres

# Apply migrations (required before the first run and after every pull)
uv run alembic upgrade head

# Run backend
uv run uvicorn backend.main:app --reload --port 8000

# Run frontend (in another terminal)
cd frontend && npm run dev
```

---

## 🗃️ Database Migrations

The schema is owned by Alembic. `Base.metadata.create_all` is used **only** by
the SQLite unit-test fixtures — never against PostgreSQL, where it would
bypass the migration history and silently diverge from production.

| Task | Command |
| :--- | :--- |
| Apply all pending migrations | `uv run alembic upgrade head` |
| Create a revision from model changes | `uv run alembic revision --autogenerate -m "add x to y"` |
| Roll back one revision | `uv run alembic downgrade -1` |
| Show current revision | `uv run alembic current` |
| Detect models drifted from migrations | `uv run alembic check` |

`DATABASE_URL` must be set (see `.env.example`); `alembic.ini` deliberately
leaves `sqlalchemy.url` empty so no credentials are ever committed.

**Always review an autogenerated revision before committing it.** Alembic does
not detect renames — it emits a `drop_column` plus an `add_column`, which
destroys the data in that column. Rewrite those pairs as `alter_column` by hand.

### Verifying the migration chain

The unit suite runs on in-memory SQLite and cannot execute the pgvector
revision, so migrations are covered by a separate integration test against a
real PostgreSQL (started on demand via Docker):

```bash
uv run pytest -m integration        # upgrade -> downgrade -> upgrade + drift check
uv run pytest -m "not integration"  # default fast suite
```

Both run in CI on every push (`.github/workflows/ci.yml`).

---

## ☁️ Deployment (GCP)

The backend image carries two roles, dispatched by `docker/entrypoint.sh`:

| Role | Command | Purpose |
| :--- | :--- | :--- |
| `migrate` | `alembic upgrade head` | One-shot schema migration, then exits |
| `api` (default) | `uvicorn backend.main:app` | Serves the application |

Migrations are **not** chained to API start-up. Cloud Run scales to N
instances; if each one ran `upgrade head` on boot, they would race for the
`ACCESS EXCLUSIVE` lock on `alembic_version`, and the losers would stall past
their health-check deadline and crash-loop the rollout. Running the migration
as a separate, single-execution job also keeps an application rollback
independent from the schema.

Deployment order — the migration gates the deploy, so a failed migration
leaves the previous revision serving traffic:

```bash
# 1. Build & push to Artifact Registry
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:$SHA

# 2. Run migrations as a one-shot Cloud Run Job (single execution)
gcloud run jobs deploy requirementshub-migrate \
    --image $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:$SHA \
    --args migrate \
    --set-cloudsql-instances $INSTANCE_CONNECTION_NAME \
    --set-secrets DATABASE_URL=DATABASE_URL:latest \
    --region $REGION
gcloud run jobs execute requirementshub-migrate --wait --region $REGION

# 3. Deploy the service only if step 2 succeeded
gcloud run deploy requirementshub-api \
    --image $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:$SHA \
    --set-cloudsql-instances $INSTANCE_CONNECTION_NAME \
    --set-secrets DATABASE_URL=DATABASE_URL:latest \
    --region $REGION
```

Secrets are bound from **GCP Secret Manager**, never passed as plaintext
environment variables. On Cloud SQL, `backend/config.py` also accepts
`INSTANCE_CONNECTION_NAME` and builds the Unix-socket DSN itself, so
`DATABASE_URL` may be omitted in that setup.

Because migrations run *before* the new code is serving, every revision must
be **backward-compatible with the currently deployed version** for the
duration of the rollout. Expand/contract is the safe pattern: add a nullable
column, deploy the code that writes it, backfill, and only drop the old column
in a later release.

Full infrastructure checklist (IAM roles, WIF, Secret Manager, Firebase
Hosting for the frontend): [`zsystem/gcp_migration_checklist.md`](zsystem/gcp_migration_checklist.md).

---

## 🛠️ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | Incorrect or missing `OLLAMA_API_KEY`. | Ensure `OLLAMA_API_KEY=segula-super-secret-key-2026` in `.env`. |
| **`404 Not Found`** | Model tag mismatch or trailing space in `.env`. | Check `ollama list` on Lightning AI. Ensure `.env` has no trailing space on `LOCAL_MODEL`. |
| **Studio stopped** | Inactive Studio went to sleep. | Wake the Studio on Lightning AI and re-run `./start.sh`. Downloaded models in `/teamspace/studios/this_studio/ollama_models` remain intact. |
| **Slow inference (>90s)** | Large 14B context on T4 GPU. | `deepseek-r1:14b` is performing deep multi-step `<think>` reasoning. Use `qwen3:8b` if latency is preferred over depth. |
