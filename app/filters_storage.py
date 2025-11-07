from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List


class FiltersStorage:
    def __init__(self, file_path: str):
        self._path = Path(file_path)
        self._lock = threading.RLock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self._path.exists():
            self._path.write_text("{}", encoding="utf-8")

    def read(self) -> Dict[str, str]:
        with self._lock:
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    return {}
                # keys: names, values: urls
                return {str(k): str(v) for k, v in data.items()}
            except Exception:
                return {}

    def list_names(self) -> List[str]:
        return sorted(self.read().keys())

    def upsert(self, name: str, url: str) -> None:
        with self._lock:
            data = self.read()
            data[name] = url
            self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def delete(self, name: str) -> bool:
        with self._lock:
            data = self.read()
            existed = name in data
            if existed:
                data.pop(name)
                self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return existed


