from __future__ import annotations

import json
import os
import tempfile
import threading
from typing import Any, Dict

from finality_store_base import FinalityStoreBase


class FileFinalityStore(FinalityStoreBase):
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def read(self) -> Dict[str, Any]:
        with self._lock:
            return self._read_unlocked()

    def write(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._write_unlocked(payload)

    def upsert_request(self, request_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            state = self._read_unlocked()
            state.setdefault("requests", {})
            state["requests"][request_id] = payload
            self._write_unlocked(state)
            return payload

    def patch_request(self, request_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            state = self._read_unlocked()
            state.setdefault("requests", {})
            if request_id not in state["requests"]:
                raise KeyError(request_id)

            state["requests"][request_id].update(updates)
            self._write_unlocked(state)
            return state["requests"][request_id]

    def get_request(self, request_id: str) -> Dict[str, Any]:
        with self._lock:
            state = self._read_unlocked()
            state.setdefault("requests", {})
            if request_id not in state["requests"]:
                raise KeyError(request_id)
            return state["requests"][request_id]

    def list_requests(self) -> Dict[str, Any]:
        with self._lock:
            state = self._read_unlocked()
            return state.get("requests", {})

    def export_state(self) -> Dict[str, Any]:
        return self.read()

    def import_state(self, payload: Dict[str, Any]) -> None:
        self.write(payload)

    def _read_unlocked(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {"requests": {}}

        with open(self.path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)

    def _write_unlocked(self, payload: Dict[str, Any]) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(prefix="finality-", suffix=".json", dir=directory or None)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
