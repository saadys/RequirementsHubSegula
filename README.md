# ⚡ Segula AI Requirement Hub (AI-RH)

<div align="center">

![Segula Technologies](https://img.shields.io/badge/Segula-Technologies-005696?style=for-the-badge&logo=target&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_19-Vite_SPA-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_17-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![DeepSeek R1](https://img.shields.io/badge/DeepSeek_R1-14B_AWQ_(vLLM)-7B1FA2?style=for-the-badge&logo=openai&logoColor=white)
![GCP Cloud Run](https://img.shields.io/badge/Google_Cloud-Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)
![CI/CD](https://img.shields.io/badge/GitHub_Actions-100%25_Automated_CI%2FCD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

**An enterprise-grade, sovereign AI Feasibility Assessment & Engineering Review Platform.**  
*Transforming unstructured business ideas into rigorous, scored, and production-ready AI project dossiers in seconds.*

</div>

---

## 📖 Table of Contents
1. [🎯 Problem Statement & What It Solves](#-problem-statement--what-it-solves)
2. [✨ Key Features & Capabilities](#-key-features--capabilities)
3. [🏛️ System Architecture](#️-system-architecture)
4. [💻 Local Development Guide (Step-by-Step)](#-local-development-guide-step-by-step)
5. [⚡ Sovereign GPU Setup (vLLM + Ollama on Lightning AI)](#-sovereign-gpu-setup-vllm--ollama-on-lightning-ai)
6. [☁️ Deployment to GCP Cloud Run (Step-by-Step)](#️-deployment-to-gcp-cloud-run-step-by-step)
7. [🗃️ Database Migrations & Vector RAG Seeding](#️-database-migrations--vector-rag-seeding)
8. [🧪 Testing & Quality Assurance](#-testing--quality-assurance)
9. [🌐 API Reference & Documentation](#-api-reference--documentation)

---

## 🎯 Problem Statement & What It Solves

Within global engineering firms like **Segula Technologies**, non-technical operational departments (Automotive Engineering, Aerospace, Rail, Energy, and Corporate Support) frequently request AI solutions to automate complex workflows. However, these requests typically suffer from:

* **Vague & Buzzword-laden Scopes:** Lack of defined inputs, outputs, dataset volumes, or quantitative KPIs.
* **Mismatched Technical Expectations:** Requesting generative LLMs for deterministic problems or impossible physics calculations.
* **Data Readiness Deficits:** Lack of labeled datasets, access rights, or unorganized documentation.
* **Engineering Bottlenecks:** AI architects spend dozens of hours screening unviable requests instead of building high-impact systems.

### 💡 The Solution: Segula AI Requirement Hub
**AI-RH** acts as an automated, intelligent gatekeeper and architectural advisor:
1. **Ingests Requirements:** Structured forms, dynamic department schemas, and attached PDF specification documents.
2. **Evaluates 5 Pillars of AI Feasibility:** Viability, Data Readiness, Problem Clarity, Integration Complexity, and Governance/Risk.
3. **Retrieval-Augmented Generation (RAG):** Cosine vector search against past Segula engineering projects to avoid redundant work.
4. **Deterministic Scoring Engine & Veto Rules:** Calculates objective rubric scores (0–100) with non-negotiable circuit breaker vetoes.
5. **Real-Time Token Streaming (SSE):** Streams the AI architect's multi-step chain-of-thought reasoning (`<think>`) directly to the user.
6. **AI Admin Dashboard:** Full lifecycle traceability, historical submission reviews, and human-in-the-loop decision overrides.

---

## ✨ Key Features & Capabilities

* 🧠 **Sovereign Deep Reasoning Engine:** Powered by `deepseek-r1-distill-qwen-14b-awq` served via vLLM with vLLM PagedAttention and AWQ 4-bit quantization.
* ⚡ **High-Speed Vector Embeddings:** Built-in `qwen3-embedding:0.6b` (1024 dimensions) using PostgreSQL `pgvector` HNSW indexes.
* 🛡️ **Zero-Hallucination Scoring:** Pure deterministic mathematical rubric calculations with automated veto gates.
* 📄 **Automated PDF Parsing:** Extracts tables, paragraphs, and specifications from uploaded documents directly into the reasoning pipeline.
* 🔄 **Multi-Round Clarification Loop:** Automatically generates targeted questions if requirements are incomplete or ambiguous.
* 🔒 **100% Enterprise Sovereign:** Zero proprietary vendor lock-in, fully hostable on private VPCs, Lightning AI, and GCP Cloud Run.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([Business / Engineering User]) -->|Submits Requirement + PDF| Frontend[React 19 SPA Glassmorphism]
    Frontend -->|SSE / REST API| FastAPI[FastAPI Backend on Cloud Run]
    
    subgraph Core Pipeline [LangGraph Pipeline]
        FastAPI --> Ingest[1. Input Ingestion & PDF Parser]
        Ingest --> DeptSchema[2. Dynamic Department Schema Validation]
        DeptSchema --> RAG[3. pgvector RAG Similarity Search]
        RAG --> LLM[4. 5-Pillar Fact Extraction DeepSeek-R1]
        LLM --> Scorer[5. Deterministic Scoring & Veto Engine]
        Scorer --> Report[6. Markdown Dossier & Advice Generator]
    end

    subgraph Infrastructure [Sovereign Infrastructure]
        RAG <-->|Session Pooler IPv4| DB[(Supabase PostgreSQL 17 + pgvector)]
        LLM <-->|Bearer Auth /v1| Proxy[Secure Reverse Proxy :8000]
        Proxy -->|/v1| vLLM[vLLM Port 8001: DeepSeek-R1 14B AWQ]
        Proxy -->|/api/embed| Ollama[Ollama Port 11434: Qwen3 Embedding]
    end

    Report --> Frontend
    Report --> Admin[AI Architect Admin Dashboard]
```

---

## 💻 Local Development Guide (Step-by-Step)

### 1. Prerequisites
Ensure you have the following installed on your local system:
* **Python 3.12+**
* **[uv](https://github.com/astral-sh/uv)** (Extremely fast Python package manager)
* **Node.js 20+ & npm**
* **Docker & Docker Compose** (for local PostgreSQL + pgvector)

### 2. Clone the Repository
```bash
git clone https://github.com/saadys/RequirementsHubSegula.git
cd RequirementsHubSegula
```

### 3. Install Backend & Frontend Dependencies
```bash
# Install Python dependencies in a virtual environment
uv sync --extra dev

# Install React frontend dependencies
cd frontend && npm install && cd ..
```

### 4. Configure Environment Variables (`.env`)
Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```ini
ENV=development
PORT=8000

# Database (Local Docker or Supabase Session Pooler)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5435/requirementshub

# Sovereign AI Backend (Lightning AI or local Ollama)
LLM_BACKEND=lightning_vllm
USE_LOCAL_LLM=true
VLLM_BASE_URL=https://8000-YOUR-STUDIO-ID.cloudspaces.litng.ai
VLLM_API_KEY=segula-super-secret-key-2026
VLLM_MODEL=casperhansen/deepseek-r1-distill-qwen-14b-awq

OLLAMA_BASE_URL=https://8000-YOUR-STUDIO-ID.cloudspaces.litng.ai
OLLAMA_API_KEY=segula-super-secret-key-2026
LOCAL_EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024
```

### 5. Start Local PostgreSQL Database
```bash
docker compose -f docker/docker-compose.yml up -d postgres
```

### 6. Apply Database Migrations & Seed Projects
```bash
# Apply schema and pgvector extension
uv run alembic upgrade head

# Seed initial departments and historic vector knowledge base
uv run python -m backend.cli.seed
```

### 7. Run Backend & Frontend Servers
```bash
# Terminal 1: Start FastAPI Backend
uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start React Frontend
cd frontend && npm run dev
```

Visit **`http://localhost:5173`** to access the web application!

---

## ⚡ Sovereign GPU Setup (vLLM + Ollama on Lightning AI)

To run **DeepSeek-R1-14B-AWQ** and **Qwen3-Embedding** on an NVIDIA GPU (T4 / L4 / A10G):

1. Launch a Studio on **[Lightning AI](https://lightning.ai/)** with a GPU instance.
2. In the Studio terminal, clone the repo and execute `start.sh`:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
3. `start.sh` automatically installs Ollama, pulls `qwen3-embedding:0.6b`, starts vLLM on port `8001`, and exposes the unified gateway `proxy_server.py` on port `8000`.
4. In the Studio **Ports** panel, set Port **8000** to **Public**.
5. Copy the generated public URL (e.g., `https://8000-xxxx.cloudspaces.litng.ai`).

---

## ☁️ Deployment to GCP Cloud Run (Step-by-Step)

The application is deployed using a production unified container pattern that serves both the compiled React SPA and the FastAPI REST API from a single lightweight container.

### Step 1: Database Setup (Supabase / Cloud SQL)
1. Create a PostgreSQL project on **[Supabase](https://supabase.com)** (EU Frankfurt / Ireland region).
2. Retrieve your **Session Pooler (IPv4)** connection string on port `5432`.
3. If your password contains special characters (like `@`), encode them (e.g. `@` ➔ `%40`).
4. Example URL format:
   ```text
   postgresql+asyncpg://postgres.PROJECT_ID:PASSWORD%4017@aws-1-eu-west-1.pooler.supabase.com:5432/postgres?ssl=require
   ```

### Step 2: GCP Service Account & Artifact Registry
1. In Google Cloud Console, enable **Cloud Run API** and **Artifact Registry API**.
2. Create an Artifact Registry Docker repository:
   ```bash
   gcloud artifacts repositories create cloud-run-source-deploy \
       --repository-format=docker \
       --location=europe-west9 \
       --description="Segula AI Requirement Hub Images"
   ```
3. Create a Service Account with roles `roles/run.admin`, `roles/artifactregistry.writer`, and `roles/iam.serviceAccountUser`.
4. Generate a JSON Key for the Service Account.

### Step 3: Configure GitHub Secrets
In your GitHub Repository, navigate to **Settings ➔ Secrets and variables ➔ Actions** and add:

| Secret Name | Description / Example Value |
|---|---|
| `GCP_PROJECT_ID` | Your Google Cloud Project ID |
| `GCP_SA_KEY` | The complete JSON content of your GCP Service Account Key |
| `DATABASE_URL` | Your Supabase Session Pooler connection string |
| `VLLM_BASE_URL` | Your Lightning AI Public URL (`https://8000-xxxx.cloudspaces.litng.ai`) |
| `VLLM_API_KEY` | `segula-super-secret-key-2026` |
| `OLLAMA_BASE_URL` | Your Lightning AI Public URL (`https://8000-xxxx.cloudspaces.litng.ai`) |
| `OLLAMA_API_KEY` | `segula-super-secret-key-2026` |

### Step 4: Trigger CI/CD Deployment
Push any commit to the `main` branch:
```bash
git add .
git commit -m "deploy: update production build"
git push origin main
```
GitHub Actions automatically builds the multi-stage Docker image, runs schema checks, executes unit tests, and rolls out the revision to Google Cloud Run!

---

## 🗃️ Database Migrations & Vector RAG Seeding

Database state is strictly version-controlled with Alembic:

```bash
# Run latest migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Verify schema drift against SQLAlchemy models
uv run alembic check

# Seed initial departments and vector knowledge base
uv run python -m backend.cli.seed
```

---

## 🧪 Testing & Quality Assurance

Run the comprehensive automated test suite:

```bash
# Run all fast unit tests (Schemas, Scoring, API routes, Validation)
uv run pytest -m "not integration" -v

# Run database migration integration test
uv run pytest -m integration -v

# Run 20 enterprise test cases benchmark
python tests/benchmark_models.py
```

---

## 🌐 API Reference & Documentation

When the backend is running, explore the interactive documentation:

* **Interactive Swagger UI:** [`/docs`](https://segula-ai-hub-n3bvi3ldua-od.a.run.app/docs)
* **ReDoc Specification:** [`/redoc`](https://segula-ai-hub-n3bvi3ldua-od.a.run.app/redoc)
* **Healthcheck & DB Status:** [`/api/health`](https://segula-ai-hub-n3bvi3ldua-od.a.run.app/api/health)

### Key REST Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and database connectivity check |
| `GET` | `/api/departments` | List all 5 Segula operating departments |
| `GET` | `/api/departments/{id}/fields` | Dynamic department-specific requirement schema |
| `POST` | `/api/submissions` | Standard requirement submission (Async / Polling) |
| `POST` | `/api/submissions/stream` | Real-time Server-Sent Events (SSE) token streaming |
| `POST` | `/api/submissions/upload` | Multipart submission with attached PDF specification |
| `GET` | `/api/submissions/{request_id}` | Retrieve complete feasibility dossier and scores |
| `GET` | `/api/dashboard/stats` | AI Admin telemetry, KPIs, and department breakdowns |
| `GET` | `/api/dashboard/submissions` | Historical submissions list with filter & search |
| `POST` | `/api/clarifications/{id}/answer`| Submit answers to multi-round clarification questions |

---

<div align="center">
  <b>Developed for Segula Technologies AI Engineering Center of Excellence.</b><br>
  <i>Built with FastAPI, React 19, LangGraph, PostgreSQL, and Sovereign DeepSeek-R1.</i>
</div>
