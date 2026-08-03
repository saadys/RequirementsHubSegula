"""
Application Configuration

Centralized settings for the AI Requirement Hub.

⚠️  SHARED FILE — Do not edit without agreement from both engineers.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────────

GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1", "")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── LLM Settings ─────────────────────────────────────────────────

LLM_TEMPERATURE = 0  # Deterministic output for fact extraction
LLM_TEMPERATURE_CLARIFICATION = 0.3  # Slight variation for natural questions
PRIMARY_MODEL = "gemini/gemini-3.1-flash-lite"
FALLBACK_MODEL = "openai/gpt-4o"

# ── Scoring Thresholds ───────────────────────────────────────────

SCORE_GO_THRESHOLD = 70        
SCORE_NOGO_THRESHOLD = 20        
# Between 40-69 = NEEDS_CLARIFICATION

# ── Clarification Settings ───────────────────────────────────────

MAX_CLARIFICATION_ROUNDS = 2

# ── RAG Settings ─────────────────────────────────────────────────

RAG_EXACT_MATCH_THRESHOLD = 0.95
RAG_SIMILAR_THRESHOLD = 0.60
RAG_TOP_K = 5
CHROMA_COLLECTION_NAME = "historic_projects"
EMBEDDING_MODEL = "models/text-embedding-004"

# ── Paths ────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORIC_PROJECTS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "historic_projects.json"
)
DEPARTMENT_CONFIGS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "department_configs.json"
)
