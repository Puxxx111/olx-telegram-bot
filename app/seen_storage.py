from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, Set


class SeenStorage:
    """Stores seen ad IDs per filter name to avoid duplicates."""

    def __init__(self, file_path: str):
        self._path = Path(file_path)
        self._lock = threading.RLock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self._path.exists():
            self._path.write_text("{}", encoding="utf-8")

    def _load(self) -> Dict[str, Set[str]]:
        with self._lock:
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    return {}
                return {k: set(map(str, v or [])) for k, v in raw.items()}
            except Exception:
                return {}

    def _save(self, data: Dict[str, Set[str]]) -> None:
        with self._lock:
            serializable = {k: sorted(list(v)) for k, v in data.items()}
            self._path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_many(self, filter_name: str, ad_ids: Set[str]) -> None:
        with self._lock:
            data = self._load()
            existing = data.get(filter_name, set())
            updated = existing.union(set(ad_ids))
            data[filter_name] = updated
            self._save(data)

    def unseen_only(self, filter_name: str, ad_ids: Set[str]) -> Set[str]:
        with self._lock:
            data = self._load()
            existing = data.get(filter_name, set())
            return set(ad_ids) - existing


