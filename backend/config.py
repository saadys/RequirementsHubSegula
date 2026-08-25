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


USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "ollama/qwen3:8b")

#LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")

# Retry (transient errors only: rate limits, timeouts, 5xx) before a key
# rotation (Gemini) or a provider fallback (FallbackLLMProvider) kicks in.
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
LLM_RETRY_BASE_DELAY_SECONDS = float(os.getenv("LLM_RETRY_BASE_DELAY_SECONDS", "1"))

# ========================= Scoring Thresholds =========================

SCORE_GO_THRESHOLD = int(os.getenv("SCORE_GO_THRESHOLD", "70"))
SCORE_NOGO_THRESHOLD = int(os.getenv("SCORE_NOGO_THRESHOLD", "20"))
# Between 40-69 = NEEDS_CLARIFICATION

# ========================= Clarification Settings =========================

MAX_CLARIFICATION_ROUNDS = int(os.getenv("MAX_CLARIFICATION_ROUNDS", "2"))

# ========================= Vector DB Config =========================

RAG_EXACT_MATCH_THRESHOLD = float(os.getenv("RAG_EXACT_MATCH_THRESHOLD", "0.75"))
RAG_SIMILAR_THRESHOLD = float(os.getenv("RAG_SIMILAR_THRESHOLD", "0.60"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

#DEFAULT_EMBEDDING_DIM = "1024" if USE_LOCAL_LLM else "768"
#EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", DEFAULT_EMBEDDING_DIM))
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
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


