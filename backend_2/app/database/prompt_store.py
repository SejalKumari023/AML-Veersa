"""
In-memory prompt store for backend_2.

Provides the same interface as backend_1's PostgresDatabase prompt methods
so the frontend PromptEditor can treat both backends identically.
Data resets on restart — acceptable for hackathon; swap _store for a DB-backed
dict to make it persistent.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

_store: Dict[str, dict] = {}


def seed_defaults(defaults: Dict[str, dict]) -> None:
    """Insert default prompts if they are not already present."""
    for name, data in defaults.items():
        if name not in _store:
            _store[name] = {
                "name": name,
                "description": data.get("description", ""),
                "content": data.get("content", ""),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }


def get_all() -> List[dict]:
    """Return all prompts sorted by name."""
    return sorted(_store.values(), key=lambda x: x["name"])


def get_one(name: str) -> Optional[dict]:
    """Return a single prompt by name, or None."""
    return _store.get(name)


def upsert(name: str, content: str) -> dict:
    """Insert or update a prompt's content."""
    existing = _store.get(name, {"name": name, "description": ""})
    existing["content"] = content
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    _store[name] = existing
    return existing
