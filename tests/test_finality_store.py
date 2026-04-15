from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = REPO_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from finality_store import build_finality_store


def sample_request(request_id: str = "a" * 64) -> dict:
    return {
        "request_id": request_id,
        "trace_id": "trace-1",
        "mode": "single",
        "submitter": "verification",
        "contract": "verification",
        "status": "submitted",
        "rpc_url": "https://history.denotary.io",
        "anchor": {
            "external_ref_hash": "b" * 64,
            "object_hash": "c" * 64,
        },
        "tx_id": None,
        "block_num": None,
        "registered_at": "2026-04-15T10:00:00Z",
        "included_at": None,
        "updated_at": "2026-04-15T10:00:00Z",
        "finalized_at": None,
        "failed_at": None,
        "failure_reason": None,
        "failure_details": None,
        "inclusion_verified": False,
        "inclusion_verified_at": None,
        "inclusion_verification_error": None,
        "verified_action": None,
        "chain_state": {
            "head_block_num": None,
            "last_irreversible_block_num": None,
        },
    }


class FinalityStoreParityTests(unittest.TestCase):
    def exercise_store(self, backend: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = str(Path(temp_dir) / "finality-state.json")
            state_db = str(Path(temp_dir) / "finality-state.sqlite3")
            store = build_finality_store(
                state_backend=backend,
                state_file=state_file,
                state_db=state_db,
            )

            payload = sample_request()
            store.upsert_request(payload["request_id"], payload)

            loaded = store.get_request(payload["request_id"])
            self.assertEqual(loaded["submitter"], "verification")
            self.assertEqual(loaded["anchor"]["object_hash"], "c" * 64)

            patched = store.patch_request(
                payload["request_id"],
                {
                    "status": "included",
                    "tx_id": "d" * 64,
                    "block_num": 123,
                },
            )
            self.assertEqual(patched["status"], "included")
            self.assertEqual(patched["tx_id"], "d" * 64)

            exported = store.export_state()
            self.assertIn(payload["request_id"], exported["requests"])
            self.assertEqual(exported["requests"][payload["request_id"]]["block_num"], 123)

            replacement = sample_request("e" * 64)
            replacement["status"] = "failed"
            store.import_state({"requests": {replacement["request_id"]: replacement}})

            all_requests = store.list_requests()
            self.assertEqual(list(all_requests.keys()), [replacement["request_id"]])
            self.assertEqual(all_requests[replacement["request_id"]]["status"], "failed")

    def test_file_backend(self) -> None:
        self.exercise_store("file")

    def test_sqlite_backend(self) -> None:
        self.exercise_store("sqlite")


if __name__ == "__main__":
    unittest.main()
