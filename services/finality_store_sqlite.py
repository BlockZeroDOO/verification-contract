from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any, Dict

from finality_store_base import FinalityStoreBase


class SQLiteFinalityStore(FinalityStoreBase):
    SCHEMA_VERSION = "1"

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._initialize()

    def describe(self) -> Dict[str, Any]:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM store_meta WHERE key = 'schema_version'"
            ).fetchone()
            schema_version = row["value"] if row else None
        return {
            "backend": "sqlite",
            "path": self.path,
            "exists": os.path.exists(self.path),
            "schema_version": schema_version,
        }

    def read(self) -> Dict[str, Any]:
        return self.export_state()

    def write(self, payload: Dict[str, Any]) -> None:
        self.import_state(payload)

    def upsert_request(self, request_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        serialized = self._serialize(payload)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO requests (
                    request_id,
                    mode,
                    submitter,
                    contract,
                    status,
                    tx_id,
                    registered_at,
                    updated_at,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    mode = excluded.mode,
                    submitter = excluded.submitter,
                    contract = excluded.contract,
                    status = excluded.status,
                    tx_id = excluded.tx_id,
                    registered_at = excluded.registered_at,
                    updated_at = excluded.updated_at,
                    payload_json = excluded.payload_json
                """,
                (
                    request_id,
                    payload.get("mode"),
                    payload.get("submitter"),
                    payload.get("contract"),
                    payload.get("status"),
                    payload.get("tx_id"),
                    payload.get("registered_at"),
                    payload.get("updated_at"),
                    serialized,
                ),
            )
        return payload

    def patch_request(self, request_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            payload = self.get_request(request_id)
            payload.update(updates)
            self.upsert_request(request_id, payload)
            return payload

    def get_request(self, request_id: str) -> Dict[str, Any]:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if row is None:
                raise KeyError(request_id)
            return self._deserialize(row[0])

    def list_requests(self) -> Dict[str, Any]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT request_id, payload_json FROM requests ORDER BY request_id"
            ).fetchall()
            return {row["request_id"]: self._deserialize(row["payload_json"]) for row in rows}

    def export_state(self) -> Dict[str, Any]:
        return {"requests": self.list_requests()}

    def import_state(self, payload: Dict[str, Any]) -> None:
        requests = payload.get("requests", {})
        if not isinstance(requests, dict):
            raise ValueError("payload.requests must be an object")

        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM requests")
            for request_id, request_payload in requests.items():
                serialized = self._serialize(request_payload)
                connection.execute(
                    """
                    INSERT INTO requests (
                        request_id,
                        mode,
                        submitter,
                        contract,
                        status,
                        tx_id,
                        registered_at,
                        updated_at,
                        payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request_id,
                        request_payload.get("mode"),
                        request_payload.get("submitter"),
                        request_payload.get("contract"),
                        request_payload.get("status"),
                        request_payload.get("tx_id"),
                        request_payload.get("registered_at"),
                        request_payload.get("updated_at"),
                        serialized,
                    ),
                )

    def _initialize(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS store_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    mode TEXT,
                    submitter TEXT,
                    contract TEXT,
                    status TEXT,
                    tx_id TEXT,
                    registered_at TEXT,
                    updated_at TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_tx_id ON requests(tx_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_submitter ON requests(submitter)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_updated_at ON requests(updated_at)"
            )
            connection.execute(
                """
                INSERT INTO store_meta(key, value)
                VALUES ('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (self.SCHEMA_VERSION,),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        return connection

    @staticmethod
    def _serialize(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _deserialize(payload_json: str) -> Dict[str, Any]:
        return json.loads(payload_json)
