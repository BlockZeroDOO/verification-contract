from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = PROJECT_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import audit_api  # noqa: E402
import finality_watcher  # noqa: E402
import ingress_api  # noqa: E402
import receipt_service  # noqa: E402


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def request_json(
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> tuple[int, Dict[str, Any]]:
    data = None
    request_headers: Dict[str, str] = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


class MockChainHandler(BaseHTTPRequestHandler):
    server_version = "MockChain/0.1"

    def do_POST(self) -> None:
        if self.path != "/v1/chain/get_info":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = json.dumps(self.server.chain_state).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


class MockChainServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler]):
        super().__init__(server_address, handler)
        self.chain_state = {
            "head_block_num": 100,
            "last_irreversible_block_num": 90,
        }


class ServiceIntegrationTest(unittest.TestCase):
    WATCHER_AUTH_TOKEN = "integration-shared-token"

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.state_file = str(Path(cls.temp_dir.name) / "finality-state.json")
        cls.threads: list[threading.Thread] = []
        cls.servers: list[Any] = []

        cls.mock_chain_port = find_free_port()
        cls.mock_chain_url = f"http://127.0.0.1:{cls.mock_chain_port}"
        cls.mock_chain_server = MockChainServer(("127.0.0.1", cls.mock_chain_port), MockChainHandler)
        cls._start_server(cls.mock_chain_server)

        cls.ingress_port = find_free_port()
        cls.ingress_server = ingress_api.IngressHttpServer(
            ("127.0.0.1", cls.ingress_port),
            ingress_api.IngressApiHandler,
            "verification",
        )
        cls._start_server(cls.ingress_server)

        cls.watcher_port = find_free_port()
        cls.watcher_server = finality_watcher.FinalityWatcherServer(
            ("127.0.0.1", cls.watcher_port),
            finality_watcher.FinalityWatcherHandler,
            finality_watcher.FinalityStore(cls.state_file),
            cls.mock_chain_url,
            3600,
            cls.WATCHER_AUTH_TOKEN,
        )
        cls._start_server(cls.watcher_server)

        cls.receipt_port = find_free_port()
        cls.receipt_server = receipt_service.ReceiptServiceServer(
            ("127.0.0.1", cls.receipt_port),
            receipt_service.ReceiptServiceHandler,
            finality_watcher.FinalityStore(cls.state_file),
        )
        cls._start_server(cls.receipt_server)

        cls.audit_port = find_free_port()
        cls.audit_server = audit_api.AuditApiServer(
            ("127.0.0.1", cls.audit_port),
            audit_api.AuditApiHandler,
            finality_watcher.FinalityStore(cls.state_file),
        )
        cls._start_server(cls.audit_server)

    @classmethod
    def tearDownClass(cls) -> None:
        for server in reversed(cls.servers):
            server.shutdown()
            server.server_close()
        for thread in reversed(cls.threads):
            thread.join(timeout=2)
        cls.temp_dir.cleanup()

    @classmethod
    def _start_server(cls, server: Any) -> None:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        cls.servers.append(server)
        cls.threads.append(thread)
        time.sleep(0.05)

    def _single_prepare_payload(self, external_ref: str) -> Dict[str, Any]:
        return {
            "submitter": "alice",
            "external_ref": external_ref,
            "schema": {
                "id": 1,
                "version": "1.0.0",
                "active": True,
                "canonicalization_profile": "json-sorted-v1",
            },
            "policy": {
                "id": 10,
                "active": True,
                "allow_single": True,
                "allow_batch": False,
                "require_kyc": False,
                "min_kyc_level": 0,
            },
            "payload": {
                "doc_id": external_ref,
                "kind": "invoice",
                "amount": 42,
            },
        }

    def _batch_prepare_payload(self, external_ref: str) -> Dict[str, Any]:
        return {
            "submitter": "alice",
            "external_ref": external_ref,
            "schema": {
                "id": 1,
                "version": "1.0.0",
                "active": True,
                "canonicalization_profile": "json-sorted-v1",
            },
            "policy": {
                "id": 20,
                "active": True,
                "allow_single": False,
                "allow_batch": True,
                "require_kyc": False,
                "min_kyc_level": 0,
            },
            "items": [
                {"external_leaf_ref": "leaf-a", "payload": {"doc_id": "a", "amount": 1}},
                {"external_leaf_ref": "leaf-b", "payload": {"doc_id": "b", "amount": 2}},
            ],
        }

    def _watcher_headers(self) -> Dict[str, str]:
        return {"X-DeNotary-Token": self.WATCHER_AUTH_TOKEN}

    def test_ingress_redacts_debug_material_by_default(self) -> None:
        status, response = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-redacted"),
        )
        self.assertEqual(status, 200)
        self.assertNotIn("canonical_form", response)

        status, response = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/batch/prepare",
            method="POST",
            payload=self._batch_prepare_payload("batch-redacted"),
        )
        self.assertEqual(status, 200)
        self.assertNotIn("manifest", response)
        self.assertNotIn("leaf_hashes", response)

    def test_single_pipeline_end_to_end(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-e2e"),
        )
        self.assertEqual(status, 200)

        request_id = prepared["request_id"]
        trace_id = prepared["trace_id"]
        tx_id = "1" * 64
        block_num = 120

        status, registered = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
                "trace_id": trace_id,
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "anchor": {
                    "object_hash": prepared["object_hash"],
                    "external_ref_hash": prepared["external_ref_hash"],
                },
                "rpc_url": self.mock_chain_url,
            },
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(registered["status"], "submitted")

        status, response = request_json(
            f"http://127.0.0.1:{self.receipt_port}/v1/receipts/{request_id}",
        )
        self.assertEqual(status, 409)
        self.assertEqual(response["status"], "submitted")

        status, anchored = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/anchor",
            method="POST",
            payload={"anchor": {"commitment_id": 42}},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(anchored["anchor"]["commitment_id"], 42)

        status, included = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(included["status"], "included")

        self.mock_chain_server.chain_state = {
            "head_block_num": 121,
            "last_irreversible_block_num": 119,
        }
        status, polled = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/poll",
            method="POST",
            payload={},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(polled["status"], "included")

        self.mock_chain_server.chain_state = {
            "head_block_num": 125,
            "last_irreversible_block_num": 125,
        }
        status, polled = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/poll",
            method="POST",
            payload={},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(polled["status"], "finalized")

        status, receipt = request_json(
            f"http://127.0.0.1:{self.receipt_port}/v1/receipts/{request_id}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(receipt["request_id"], request_id)
        self.assertTrue(receipt["finality_flag"])

        status, audit_chain = request_json(
            f"http://127.0.0.1:{self.audit_port}/v1/audit/by-commitment/42",
        )
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["request_id"], request_id)
        self.assertEqual(audit_chain["record"]["tx_id"], tx_id)
        self.assertEqual(audit_chain["receipt"]["request_id"], request_id)
        self.assertEqual(audit_chain["proof_chain"][-1]["stage"], "block_finalized")

    def test_batch_pipeline_end_to_end(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/batch/prepare",
            method="POST",
            payload=self._batch_prepare_payload("batch-e2e"),
        )
        self.assertEqual(status, 200)

        request_id = prepared["request_id"]
        trace_id = prepared["trace_id"]
        tx_id = "2" * 64
        block_num = 130

        status, registered = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
                "trace_id": trace_id,
                "mode": "batch",
                "submitter": "alice",
                "contract": "verification",
                "anchor": {
                    "root_hash": prepared["root_hash"],
                    "manifest_hash": prepared["manifest_hash"],
                    "external_ref_hash": prepared["external_ref_hash"],
                    "leaf_count": prepared["leaf_count"],
                },
                "rpc_url": self.mock_chain_url,
            },
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(registered["status"], "submitted")

        status, anchored = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/anchor",
            method="POST",
            payload={"anchor": {"batch_id": 7}},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(anchored["anchor"]["batch_id"], 7)

        status, included = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(included["status"], "included")

        self.mock_chain_server.chain_state = {
            "head_block_num": 131,
            "last_irreversible_block_num": 131,
        }
        status, finalized = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/poll",
            method="POST",
            payload={},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(finalized["status"], "finalized")

        status, audit_chain = request_json(
            f"http://127.0.0.1:{self.audit_port}/v1/audit/by-batch/7",
        )
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["request_id"], request_id)
        self.assertEqual(audit_chain["record"]["batch_id"], 7)
        self.assertEqual(audit_chain["receipt"]["manifest_hash"], prepared["manifest_hash"])

    def test_watcher_rejects_conflicting_reregistration(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-reregister"),
        )
        self.assertEqual(status, 200)

        payload = {
            "request_id": prepared["request_id"],
            "trace_id": prepared["trace_id"],
            "mode": "single",
            "submitter": "alice",
            "contract": "verification",
            "anchor": {
                "object_hash": prepared["object_hash"],
                "external_ref_hash": prepared["external_ref_hash"],
            },
            "rpc_url": self.mock_chain_url,
        }

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload=payload,
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, response = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={**payload, "trace_id": "conflict-trace"},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 400)
        self.assertIn("trace_id", response["error"])

    def test_watcher_rejects_unauthorized_mutation(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-unauthorized"),
        )
        self.assertEqual(status, 200)

        status, response = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": prepared["request_id"],
                "trace_id": prepared["trace_id"],
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "anchor": {
                    "object_hash": prepared["object_hash"],
                    "external_ref_hash": prepared["external_ref_hash"],
                },
                "rpc_url": self.mock_chain_url,
            },
        )
        self.assertEqual(status, 401)
        self.assertIn("auth token", response["error"])

    def test_failed_request_blocks_receipt_and_is_visible_in_audit(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-failed"),
        )
        self.assertEqual(status, 200)

        request_id = prepared["request_id"]
        trace_id = prepared["trace_id"]

        status, registered = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
                "trace_id": trace_id,
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "anchor": {
                    "object_hash": prepared["object_hash"],
                    "external_ref_hash": prepared["external_ref_hash"],
                },
                "rpc_url": self.mock_chain_url,
            },
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(registered["status"], "submitted")

        status, failed = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/failed",
            method="POST",
            payload={"reason": "tx_dropped", "details": {"stage": "broadcast"}},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["failure_reason"], "tx_dropped")

        status, receipt = request_json(
            f"http://127.0.0.1:{self.receipt_port}/v1/receipts/{request_id}",
        )
        self.assertEqual(status, 409)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["failure_reason"], "tx_dropped")

        status, audit_chain = request_json(
            f"http://127.0.0.1:{self.audit_port}/v1/audit/chain/{request_id}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["status"], "failed")
        self.assertEqual(audit_chain["record"]["failure_reason"], "tx_dropped")
        self.assertIsNone(audit_chain["receipt"])


if __name__ == "__main__":
    unittest.main()
