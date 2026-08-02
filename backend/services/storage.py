"""
In-Memory & File-Backed Storage Service for Submissions

Persists pipeline state objects indexed by request_id.
"""

from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional
from threading import Lock

from backend.config import DATA_DIR

SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions_store.json")

_lock = Lock()
_submissions_cache: Dict[str, Dict[str, Any]] = {}


def _ensure_loaded():
    global _submissions_cache
    if not _submissions_cache and os.path.exists(SUBMISSIONS_FILE):
        try:
            with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
                _submissions_cache = json.load(f)
        except Exception:
            _submissions_cache = {}


def _save_to_disk():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(_submissions_cache, f, indent=2, default=str)


def save_submission(request_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Saves or updates a submission state."""
    with _lock:
        _ensure_loaded()
        now = datetime.now().isoformat()
        if request_id not in _submissions_cache:
            state["created_at"] = now
        state["updated_at"] = now
        state["request_id"] = request_id
        _submissions_cache[request_id] = state
        _save_to_disk()
        return state


def get_submission(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a submission state by request_id."""
    with _lock:
        _ensure_loaded()
        return _submissions_cache.get(request_id)


def list_submissions(
    department: Optional[str] = None, status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists all submissions with optional filters for department and status/decision."""
    with _lock:
        _ensure_loaded()
        results = list(_submissions_cache.values())

    if department:
        results = [s for s in results if s.get("department") == department]

    if status:
        results = [
            s
            for s in results
            if s.get("decision") == status
            or s.get("status") == status
            or s.get("report_type") == status
        ]

    # Sort newest first
    results.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return results
