import os
from dotenv import load_dotenv

# Bypass loading local .env file when running on GCP Cloud Run (K_SERVICE set) or in production mode
ENV = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
IS_CLOUD_RUN = bool(os.getenv("K_SERVICE"))

if not IS_CLOUD_RUN and ENV not in ("production", "prod"):
    load_dotenv()

# ========================= Logging Config =========================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_FORMAT = "json" if (IS_CLOUD_RUN or ENV in ("production", "prod")) else "text"
LOG_FORMAT = os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT).lower()



# ========================= API Keys =========================

GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1", "")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# ========================= LLM Config =========================

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))  # Deterministic output for fact extraction
LLM_TEMPERATURE_CLARIFICATION = float(os.getenv("LLM_TEMPERATURE_CLARIFICATION", "0.3"))  # Slight variation for natural questions
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini/gemini-2.5-flash")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "openai/gpt-4o")


# ── Backend Selection ────────────────────────────────────────────────
# LLM_BACKEND names the execution target explicitly. The legacy USE_LOCAL_LLM
# boolean could only express two states and could not distinguish a native
# Ollama server from an OpenAI-compatible vLLM one, which speak incompatible
# wire protocols.
BACKEND_OLLAMA_LOCAL = "ollama_local"
BACKEND_LIGHTNING_VLLM = "lightning_vllm"
BACKEND_GEMINI_CLOUD = "gemini_cloud"
BACKEND_OPENAI_CLOUD = "openai_cloud"
BACKEND_NONE = "none"

SUPPORTED_LLM_BACKENDS = (
    BACKEND_OLLAMA_LOCAL,
    BACKEND_LIGHTNING_VLLM,
    BACKEND_GEMINI_CLOUD,
    BACKEND_OPENAI_CLOUD,
)

# Legacy switch, kept so existing callers and tests keep working. It is only
# consulted when LLM_BACKEND is unset.
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"


def _resolve_backend() -> str:
    """Resolves the active backend, honouring the legacy USE_LOCAL_LLM switch."""
    explicit = os.getenv("LLM_BACKEND", "").strip().lower()
    if explicit:
        return explicit
    return BACKEND_OLLAMA_LOCAL if USE_LOCAL_LLM else BACKEND_GEMINI_CLOUD


LLM_BACKEND = _resolve_backend()
# BACKEND_NONE disables fallback entirely (useful to surface primary errors in tests).
LLM_FALLBACK_BACKEND = os.getenv("LLM_FALLBACK_BACKEND", BACKEND_GEMINI_CLOUD).strip().lower()

# ── Native Ollama backend (protocol: /api/chat, /api/tags) ───────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("LOCAL_MODEL", "ollama/qwen3:8b"))
# Backwards-compatible alias still referenced by the factory and tests.
LOCAL_MODEL = OLLAMA_MODEL

# ── Lightning AI vLLM backend (protocol: OpenAI /v1) ─────────────────
# Falls back to the OLLAMA_* variables so an existing .env that pointed those
# at a vLLM endpoint keeps working after switching LLM_BACKEND.
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", OLLAMA_BASE_URL)
VLLM_API_KEY = os.getenv("VLLM_API_KEY", OLLAMA_API_KEY)
VLLM_MODEL = os.getenv("VLLM_MODEL", os.getenv("LOCAL_MODEL", "Qwen/Qwen2.5-14B-Instruct-AWQ"))
# Grammar-constrained JSON decoding. Disable for OpenAI-compatible servers
# that are not vLLM (LM Studio, llama.cpp) — the provider also degrades
# automatically on a 400 response.
VLLM_USE_GUIDED_JSON = os.getenv("VLLM_USE_GUIDED_JSON", "true").lower() == "true"
VLLM_GUIDED_BACKEND = os.getenv("VLLM_GUIDED_BACKEND", "xgrammar")

#LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")

# Retry (transient errors only: rate limits, timeouts, 5xx) before a key
# rotation (Gemini) or a provider fallback (FallbackLLMProvider) kicks in.
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
LLM_RETRY_BASE_DELAY_SECONDS = float(os.getenv("LLM_RETRY_BASE_DELAY_SECONDS", "1"))
# Remote GPU studios cold-start slowly; the default is generous on purpose.
LLM_REQUEST_TIMEOUT_SECONDS = float(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "120"))
LLM_HEALTHCHECK_TIMEOUT_SECONDS = float(os.getenv("LLM_HEALTHCHECK_TIMEOUT_SECONDS", "5"))


def validate_llm_config() -> list[str]:
    """Returns human-readable configuration problems (empty list when valid).

    Called at application startup to fail fast on a misconfigured backend
    rather than surfacing an opaque 500 on the first user submission.
    """
    problems: list[str] = []

    if LLM_BACKEND not in SUPPORTED_LLM_BACKENDS:
        problems.append(
            f"LLM_BACKEND='{LLM_BACKEND}' is not supported. "
            f"Expected one of: {', '.join(SUPPORTED_LLM_BACKENDS)}."
        )
    if LLM_FALLBACK_BACKEND not in SUPPORTED_LLM_BACKENDS + (BACKEND_NONE,):
        problems.append(
            f"LLM_FALLBACK_BACKEND='{LLM_FALLBACK_BACKEND}' is not supported. "
            f"Expected one of: {', '.join(SUPPORTED_LLM_BACKENDS + (BACKEND_NONE,))}."
        )

    requirements = {
        BACKEND_GEMINI_CLOUD: (
            bool(GEMINI_API_KEY_1 or GEMINI_API_KEY_2),
            "GEMINI_API_KEY_1 (or GEMINI_API_KEY_2) is required",
        ),
        BACKEND_OPENAI_CLOUD: (bool(OPENAI_API_KEY), "OPENAI_API_KEY is required"),
        BACKEND_LIGHTNING_VLLM: (bool(VLLM_BASE_URL), "VLLM_BASE_URL is required"),
        BACKEND_OLLAMA_LOCAL: (bool(OLLAMA_BASE_URL), "OLLAMA_BASE_URL is required"),
    }
    for role, backend in (("LLM_BACKEND", LLM_BACKEND), ("LLM_FALLBACK_BACKEND", LLM_FALLBACK_BACKEND)):
        satisfied, message = requirements.get(backend, (True, ""))
        if not satisfied:
            problems.append(f"{role}='{backend}': {message}.")

    if LLM_BACKEND == BACKEND_LIGHTNING_VLLM:
        # vLLM serves the OpenAI surface under /v1; without it every call 404s.
        if not VLLM_BASE_URL.rstrip("/").endswith("/v1"):
            problems.append(
                f"VLLM_BASE_URL='{VLLM_BASE_URL}' should end with '/v1' "
                "(vLLM exposes the OpenAI-compatible API under that prefix)."
            )
        # LocalLLMProvider adds the ollama/ prefix; OpenAICompatProvider adds
        # openai/. A model id carrying the wrong one is routed to the wrong stack.
        if VLLM_MODEL.startswith("ollama/"):
            problems.append(
                f"VLLM_MODEL='{VLLM_MODEL}' carries the 'ollama/' prefix, which routes "
                "to the native Ollama protocol. Use the bare served model id."
            )

    if LLM_BACKEND == BACKEND_OLLAMA_LOCAL and OLLAMA_BASE_URL.rstrip("/").endswith("/v1"):
        problems.append(
            f"OLLAMA_BASE_URL='{OLLAMA_BASE_URL}' ends with '/v1', which is the "
            "OpenAI-compatible surface. Use LLM_BACKEND=lightning_vllm for that, "
            "or drop the '/v1' suffix for the native Ollama API."
        )

    return problems

# ========================= Scoring Thresholds =========================

SCORE_GO_THRESHOLD = int(os.getenv("SCORE_GO_THRESHOLD", "70"))
SCORE_NOGO_THRESHOLD = int(os.getenv("SCORE_NOGO_THRESHOLD", "20"))
# Between 40-69 = NEEDS_CLARIFICATION

# ========================= Clarification Settings =========================

MAX_CLARIFICATION_ROUNDS = int(os.getenv("MAX_CLARIFICATION_ROUNDS", "2"))

# ========================= Vector DB Config =========================

# Automatically determine calibrated RAG threshold defaults based on active embedding provider
IS_LOCAL_EMBEDDING = (
    LLM_BACKEND in (BACKEND_OLLAMA_LOCAL, BACKEND_LIGHTNING_VLLM)
    or USE_LOCAL_LLM
)

DEFAULT_RAG_EXACT = "0.75" if IS_LOCAL_EMBEDDING else "0.82"
DEFAULT_RAG_SIMILAR = "0.50" if IS_LOCAL_EMBEDDING else "0.70"

RAG_EXACT_MATCH_THRESHOLD = float(os.getenv("RAG_EXACT_MATCH_THRESHOLD", DEFAULT_RAG_EXACT))
RAG_SIMILAR_THRESHOLD = float(os.getenv("RAG_SIMILAR_THRESHOLD", DEFAULT_RAG_SIMILAR))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

DEFAULT_EMBEDDING_DIM = "1024" if IS_LOCAL_EMBEDDING else "768"
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", DEFAULT_EMBEDDING_DIM))
# ========================= Path Config =========================

DATA_DIR = os.getenv(
    "DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
)
HISTORIC_PROJECTS_PATH = os.getenv(
    "HISTORIC_PROJECTS_PATH",
    os.path.join(os.path.dirname(__file__), "data", "historic_projects.json")
)
DEPARTMENT_CONFIGS_PATH = os.getenv(
    "DEPARTMENT_CONFIGS_PATH",
    os.path.join(os.path.dirname(__file__), "data", "department_configs.json")
)

# ========================= DataBase Config =========================

DATABASE_URL = os.getenv("DATABASE_URL", "")

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "")
if not DATABASE_URL and INSTANCE_CONNECTION_NAME:
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "")
    db_name = os.getenv("DB_NAME", "requirementshub")
    db_socket_dir = os.getenv("DB_SOCKET_DIR", "/cloudsql")
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host={db_socket_dir}/{INSTANCE_CONNECTION_NAME}"

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Set it in .env: postgresql+asyncpg://user:password@localhost:5435/requirementshub "
        "or for Cloud SQL: postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE"
    )

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# psycopg (used by AsyncPostgresSaver / psycopg_pool) requires a plain "postgresql://"
# DSN — it does not understand the "+asyncpg" SQLAlchemy dialect suffix.
CHECKPOINTER_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

# ========================= LangGraph Checkpointer Pool =========================
# Separate from the SQLAlchemy pool (DB_POOL_SIZE/DB_MAX_OVERFLOW above) — keep the
# sum of both pools under the target Postgres instance's max_connections.
CHECKPOINTER_POOL_MIN_SIZE = int(os.getenv("CHECKPOINTER_POOL_MIN_SIZE", "2"))
CHECKPOINTER_POOL_MAX_SIZE = int(os.getenv("CHECKPOINTER_POOL_MAX_SIZE", "5"))


