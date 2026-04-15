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


def request_text(url: str) -> tuple[int, str, Dict[str, str]]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.status, body, dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, body, dict(exc.headers.items())


class MockChainHandler(BaseHTTPRequestHandler):
    server_version = "MockChain/0.1"

    def do_GET(self) -> None:
        if not self.path.startswith("/v2/history/get_transaction"):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        request_id = self.path.split("id=", 1)[1].split("&", 1)[0] if "id=" in self.path else ""
        payload = self.server.transactions.get(request_id)
        if payload is None:
            body = json.dumps(
                {
                    "query_time_ms": 0.1,
                    "executed": False,
                    "trx_id": request_id,
                    "lib": self.server.chain_state["last_irreversible_block_num"],
                }
            ).encode("utf-8")
        else:
            body = json.dumps(payload).encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
        self.transactions: Dict[str, Dict[str, Any]] = {}


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

        cls.receipt_public_port = find_free_port()
        cls.receipt_public_server = receipt_service.ReceiptServiceServer(
            ("127.0.0.1", cls.receipt_public_port),
            receipt_service.ReceiptServiceHandler,
            finality_watcher.FinalityStore(cls.state_file),
            privacy_mode="public",
        )
        cls._start_server(cls.receipt_public_server)

        cls.audit_port = find_free_port()
        cls.audit_server = audit_api.AuditApiServer(
            ("127.0.0.1", cls.audit_port),
            audit_api.AuditApiHandler,
            finality_watcher.FinalityStore(cls.state_file),
        )
        cls._start_server(cls.audit_server)

        cls.audit_public_port = find_free_port()
        cls.audit_public_server = audit_api.AuditApiServer(
            ("127.0.0.1", cls.audit_public_port),
            audit_api.AuditApiHandler,
            finality_watcher.FinalityStore(cls.state_file),
            privacy_mode="public",
        )
        cls._start_server(cls.audit_public_server)

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

    def _mock_transaction(self, tx_id: str, block_num: int, actions: list[Dict[str, Any]]) -> None:
        self.mock_chain_server.transactions[tx_id] = {
            "trx_id": tx_id,
            "executed": True,
            "block_num": block_num,
            "actions": actions,
        }

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

    def test_public_services_expose_openapi_and_docs(self) -> None:
        status, ingress_spec = request_json(f"http://127.0.0.1:{self.ingress_port}/openapi.json")
        self.assertEqual(status, 200)
        self.assertEqual(ingress_spec["info"]["title"], "DeNotary Ingress API")

        status, receipt_spec = request_json(f"http://127.0.0.1:{self.receipt_port}/openapi.json")
        self.assertEqual(status, 200)
        self.assertEqual(receipt_spec["info"]["title"], "DeNotary Receipt Service")

        status, audit_spec = request_json(f"http://127.0.0.1:{self.audit_port}/openapi.json")
        self.assertEqual(status, 200)
        self.assertEqual(audit_spec["info"]["title"], "DeNotary Audit API")

        status, ingress_docs, ingress_headers = request_text(f"http://127.0.0.1:{self.ingress_port}/docs")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ingress_headers.get("Content-Type", ""))
        self.assertIn("swagger-ui", ingress_docs.lower())

        status, receipt_docs, receipt_headers = request_text(f"http://127.0.0.1:{self.receipt_port}/docs")
        self.assertEqual(status, 200)
        self.assertIn("text/html", receipt_headers.get("Content-Type", ""))
        self.assertIn("swagger-ui", receipt_docs.lower())

        status, audit_docs, audit_headers = request_text(f"http://127.0.0.1:{self.audit_port}/docs")
        self.assertEqual(status, 200)
        self.assertIn("text/html", audit_headers.get("Content-Type", ""))
        self.assertIn("swagger-ui", audit_docs.lower())

        status, watcher_health = request_json(f"http://127.0.0.1:{self.watcher_port}/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(watcher_health["store"]["backend"], "file")
        self.assertEqual(watcher_health["verification_policy"], "single-provider")
        self.assertEqual(watcher_health["verification_min_success"], 1)
        self.assertIn("startup_checks", watcher_health)
        self.assertIn("startup_recovery", watcher_health)

    def test_public_privacy_mode_redacts_receipt_and_audit_metadata(self) -> None:
        tx_id = "4" * 64
        block_num = 140
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("privacy-public-mode"),
        )
        self.assertEqual(status, 200)
        request_id = prepared["request_id"]
        object_hash = prepared["object_hash"]
        external_ref_hash = prepared["external_ref_hash"]

        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "account": "verification",
                    "name": "submit",
                    "data": {
                        "submitter": "alice",
                        "schema_id": 1,
                        "policy_id": 10,
                        "object_hash": object_hash,
                        "external_ref": external_ref_hash,
                    },
                }
            ],
        )
        self.mock_chain_server.chain_state["head_block_num"] = 180
        self.mock_chain_server.chain_state["last_irreversible_block_num"] = 180

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
                "trace_id": prepared["trace_id"],
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "anchor": {
                    "object_hash": object_hash,
                    "external_ref_hash": external_ref_hash,
                },
                "rpc_url": self.mock_chain_url,
            },
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/poll",
            method="POST",
            payload={},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, receipt_health = request_json(f"http://127.0.0.1:{self.receipt_public_port}/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(receipt_health["privacy_mode"], "public")

        status, audit_health = request_json(f"http://127.0.0.1:{self.audit_public_port}/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(audit_health["privacy_mode"], "public")

        status, receipt = request_json(f"http://127.0.0.1:{self.receipt_public_port}/v1/receipts/{request_id}")
        self.assertEqual(status, 200)
        self.assertEqual(receipt["request_id"], request_id)
        self.assertEqual(receipt["trust_state"], "finalized_verified")
        self.assertNotIn("trace_id", receipt)
        self.assertNotIn("submitter", receipt)
        self.assertNotIn("tx_id", receipt)
        self.assertNotIn("block_num", receipt)
        self.assertNotIn("external_ref_hash", receipt)
        self.assertNotIn("verification_state", receipt)

        status, audit_chain = request_json(f"http://127.0.0.1:{self.audit_public_port}/v1/audit/chain/{request_id}")
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["request_id"], request_id)
        self.assertEqual(audit_chain["record"]["trust_state"], "finalized_verified")
        self.assertNotIn("trace_id", audit_chain["record"])
        self.assertNotIn("submitter", audit_chain["record"])
        self.assertNotIn("tx_id", audit_chain["record"])
        self.assertNotIn("anchor", audit_chain["record"])
        self.assertIsNotNone(audit_chain["receipt"])
        self.assertNotIn("tx_id", audit_chain["receipt"])

        verification_stage = next(
            item for item in audit_chain["proof_chain"] if item["stage"] == "transaction_verified"
        )
        self.assertNotIn("verification_state", verification_stage["details"])
        self.assertNotIn("verified_action", verification_stage["details"])

    def test_sqlite_watcher_restart_recovers_included_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_db = str(Path(temp_dir) / "restart-finality.sqlite3")
            request_id = "a1" * 32
            tx_id = "7" * 64
            block_num = 150

            status, prepared = request_json(
                f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
                method="POST",
                payload=self._single_prepare_payload("restart-recovery"),
            )
            self.assertEqual(status, 200)

            self._mock_transaction(
                tx_id,
                block_num,
                [
                    {
                        "account": "verification",
                        "name": "submit",
                        "data": {
                            "submitter": "alice",
                            "schema_id": 1,
                            "policy_id": 10,
                            "object_hash": prepared["object_hash"],
                            "external_ref": prepared["external_ref_hash"],
                        },
                    }
                ],
            )
            self.mock_chain_server.chain_state["head_block_num"] = 145
            self.mock_chain_server.chain_state["last_irreversible_block_num"] = 145

            watcher_port = find_free_port()
            watcher_store = finality_watcher.build_finality_store(
                state_backend="sqlite",
                state_file=str(Path(temp_dir) / "unused.json"),
                state_db=state_db,
            )
            watcher = finality_watcher.FinalityWatcherServer(
                ("127.0.0.1", watcher_port),
                finality_watcher.FinalityWatcherHandler,
                watcher_store,
                self.mock_chain_url,
                3600,
                self.WATCHER_AUTH_TOKEN,
            )
            watcher_thread = threading.Thread(target=watcher.serve_forever, daemon=True)
            watcher_thread.start()
            time.sleep(0.05)

            try:
                status, _ = request_json(
                    f"http://127.0.0.1:{watcher_port}/v1/watch/register",
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
                    headers=self._watcher_headers(),
                )
                self.assertEqual(status, 200)

                status, included = request_json(
                    f"http://127.0.0.1:{watcher_port}/v1/watch/{prepared['request_id']}/included",
                    method="POST",
                    payload={"tx_id": tx_id, "block_num": block_num},
                    headers=self._watcher_headers(),
                )
                self.assertEqual(status, 200)
                self.assertEqual(included["status"], "included")
            finally:
                watcher.shutdown()
                watcher.server_close()
                watcher_thread.join(timeout=2)

            self.mock_chain_server.chain_state["head_block_num"] = 180
            self.mock_chain_server.chain_state["last_irreversible_block_num"] = 180

            recovered_port = find_free_port()
            recovered_store = finality_watcher.build_finality_store(
                state_backend="sqlite",
                state_file=str(Path(temp_dir) / "unused.json"),
                state_db=state_db,
            )
            recovered_watcher = finality_watcher.FinalityWatcherServer(
                ("127.0.0.1", recovered_port),
                finality_watcher.FinalityWatcherHandler,
                recovered_store,
                self.mock_chain_url,
                3600,
                self.WATCHER_AUTH_TOKEN,
            )
            recovered_thread = threading.Thread(target=recovered_watcher.serve_forever, daemon=True)
            recovered_thread.start()
            time.sleep(0.05)

            receipt_port = find_free_port()
            receipt_store = finality_watcher.build_finality_store(
                state_backend="sqlite",
                state_file=str(Path(temp_dir) / "unused.json"),
                state_db=state_db,
            )
            receipt_server = receipt_service.ReceiptServiceServer(
                ("127.0.0.1", receipt_port),
                receipt_service.ReceiptServiceHandler,
                receipt_store,
            )
            receipt_thread = threading.Thread(target=receipt_server.serve_forever, daemon=True)
            receipt_thread.start()
            time.sleep(0.05)

            try:
                status, health = request_json(f"http://127.0.0.1:{recovered_port}/healthz")
                self.assertEqual(status, 200)
                self.assertEqual(health["store"]["backend"], "sqlite")
                self.assertEqual(health["startup_recovery"]["attempted"], 1)
                self.assertEqual(health["startup_recovery"]["finalized"], 1)

                status, recovered = request_json(
                    f"http://127.0.0.1:{recovered_port}/v1/watch/{prepared['request_id']}"
                )
                self.assertEqual(status, 200)
                self.assertEqual(recovered["status"], "finalized")
                self.assertTrue(recovered["inclusion_verified"])

                status, receipt = request_json(
                    f"http://127.0.0.1:{receipt_port}/v1/receipts/{prepared['request_id']}"
                )
                self.assertEqual(status, 200)
                self.assertEqual(receipt["trust_state"], "finalized_verified")
            finally:
                receipt_server.shutdown()
                receipt_server.server_close()
                receipt_thread.join(timeout=2)
                recovered_watcher.shutdown()
                recovered_watcher.server_close()
                recovered_thread.join(timeout=2)

    def test_ingress_can_auto_register_in_watcher(self) -> None:
        payload = self._single_prepare_payload("single-auto-register")
        payload["watcher"] = {
            "url": f"http://127.0.0.1:{self.watcher_port}",
            "auth_token": self.WATCHER_AUTH_TOKEN,
            "rpc_url": self.mock_chain_url,
        }

        status, response = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=payload,
        )
        self.assertEqual(status, 200)
        self.assertIn("watcher_handoff", response)
        self.assertTrue(response["watcher_handoff"]["ok"])
        self.assertEqual(response["watcher_handoff"]["status_code"], 200)
        self.assertEqual(
            response["watcher_handoff"]["response"]["request_id"],
            response["request_id"],
        )

        status, watcher_record = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{response['request_id']}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(watcher_record["status"], "submitted")

    def test_ingress_reports_watcher_handoff_failure_without_losing_prepare_result(self) -> None:
        payload = self._single_prepare_payload("single-auto-register-failure")
        payload["watcher"] = {
            "url": f"http://127.0.0.1:{self.watcher_port}",
            "auth_token": "wrong-token",
            "rpc_url": self.mock_chain_url,
        }

        status, response = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=payload,
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["mode"], "single")
        self.assertIn("prepared_action", response)
        self.assertIn("watcher_handoff", response)
        self.assertFalse(response["watcher_handoff"]["ok"])
        self.assertEqual(response["watcher_handoff"]["status_code"], 401)

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

        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "block_num": block_num,
                    "act": {
                        "account": "verification",
                        "name": "submit",
                        "data": {
                            "submitter": "alice",
                            "object_hash": prepared["object_hash"],
                            "external_ref": prepared["external_ref_hash"],
                        },
                    },
                }
            ],
        )

        status, included = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(included["status"], "included")
        self.assertTrue(included["inclusion_verified"])

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
        self.assertTrue(receipt["receipt_available"])
        self.assertTrue(receipt["inclusion_verified"])
        self.assertEqual(receipt["trust_state"], "finalized_verified")

        status, audit_chain = request_json(
            f"http://127.0.0.1:{self.audit_port}/v1/audit/by-commitment/42",
        )
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["request_id"], request_id)
        self.assertEqual(audit_chain["record"]["tx_id"], tx_id)
        self.assertTrue(audit_chain["record"]["receipt_available"])
        self.assertTrue(audit_chain["record"]["inclusion_verified"])
        self.assertEqual(audit_chain["record"]["trust_state"], "finalized_verified")
        self.assertEqual(audit_chain["receipt"]["request_id"], request_id)
        self.assertEqual(audit_chain["proof_chain"][-1]["stage"], "block_finalized")
        self.assertEqual(audit_chain["proof_chain"][-1]["status"], "completed")

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

        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "block_num": block_num,
                    "act": {
                        "account": "verification",
                        "name": "closebatch",
                        "data": {
                            "id": 7,
                        },
                    },
                }
            ],
        )

        status, included = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(included["status"], "included")
        self.assertTrue(included["inclusion_verified"])

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
        self.assertTrue(audit_chain["record"]["receipt_available"])
        self.assertTrue(audit_chain["record"]["inclusion_verified"])
        self.assertEqual(audit_chain["record"]["trust_state"], "finalized_verified")
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

    def test_watcher_rejects_request_id_mismatch(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-request-id-mismatch"),
        )
        self.assertEqual(status, 200)

        status, response = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": "f" * 64,
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
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 400)
        self.assertIn("request_id", response["error"])

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

    def test_watcher_rejects_mismatched_indexed_transaction(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-mismatch-tx"),
        )
        self.assertEqual(status, 200)

        request_id = prepared["request_id"]
        tx_id = "3" * 64
        block_num = 140
        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "block_num": block_num,
                    "act": {
                        "account": "verification",
                        "name": "submit",
                        "data": {
                            "submitter": "alice",
                            "object_hash": "0" * 64,
                            "external_ref": prepared["external_ref_hash"],
                        },
                    },
                }
            ],
        )

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
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
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, response = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 400)
        self.assertIn("indexed transaction", response["error"])

    def test_watcher_uses_fallback_rpc_provider_for_inclusion_verification(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-fallback-provider"),
        )
        self.assertEqual(status, 200)

        request_id = prepared["request_id"]
        tx_id = "4" * 64
        block_num = 145
        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "block_num": block_num,
                    "act": {
                        "account": "verification",
                        "name": "submit",
                        "data": {
                            "submitter": "alice",
                            "object_hash": prepared["object_hash"],
                            "external_ref": prepared["external_ref_hash"],
                        },
                    },
                }
            ],
        )

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
                "trace_id": prepared["trace_id"],
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "anchor": {
                    "object_hash": prepared["object_hash"],
                    "external_ref_hash": prepared["external_ref_hash"],
                },
                "rpc_urls": [
                    "http://127.0.0.1:1",
                    self.mock_chain_url,
                ],
            },
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, included = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(included["verification_policy"], "single-provider")
        self.assertEqual(included["verification_min_success"], 1)
        self.assertTrue(included["inclusion_verified"])
        self.assertIsNotNone(included["verification_state"])
        self.assertEqual(included["verification_state"]["consensus"]["provider_count_ok"], 1)
        self.assertEqual(included["verification_state"]["consensus"]["provider_count_total"], 2)
        self.assertFalse(included["provider_disagreement"])

    def test_watcher_quorum_policy_blocks_single_provider_match(self) -> None:
        status, prepared = request_json(
            f"http://127.0.0.1:{self.ingress_port}/v1/single/prepare",
            method="POST",
            payload=self._single_prepare_payload("single-quorum-provider"),
        )
        self.assertEqual(status, 200)

        request_id = prepared["request_id"]
        tx_id = "5" * 64
        block_num = 146
        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "block_num": block_num,
                    "act": {
                        "account": "verification",
                        "name": "submit",
                        "data": {
                            "submitter": "alice",
                            "object_hash": prepared["object_hash"],
                            "external_ref": prepared["external_ref_hash"],
                        },
                    },
                }
            ],
        )

        status, _ = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/register",
            method="POST",
            payload={
                "request_id": request_id,
                "trace_id": prepared["trace_id"],
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "verification_policy": "quorum",
                "verification_min_success": 2,
                "anchor": {
                    "object_hash": prepared["object_hash"],
                    "external_ref_hash": prepared["external_ref_hash"],
                },
                "rpc_urls": [
                    "http://127.0.0.1:1",
                    self.mock_chain_url,
                ],
            },
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)

        status, included = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/included",
            method="POST",
            payload={"tx_id": tx_id, "block_num": block_num},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(included["status"], "included")
        self.assertFalse(included["inclusion_verified"])
        self.assertEqual(included["verification_policy"], "quorum")
        self.assertEqual(included["verification_min_success"], 2)
        self.assertIn("requires 2 successful providers", included["inclusion_verification_error"])
        self.assertEqual(included["verification_state"]["consensus"]["provider_count_ok"], 1)
        self.assertEqual(included["verification_state"]["consensus"]["provider_count_total"], 2)
        self.assertFalse(included["verification_state"]["consensus"]["verified"])

        self.mock_chain_server.chain_state = {
            "head_block_num": 147,
            "last_irreversible_block_num": 147,
        }
        status, polled = request_json(
            f"http://127.0.0.1:{self.watcher_port}/v1/watch/{request_id}/poll",
            method="POST",
            payload={},
            headers=self._watcher_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(polled["status"], "included")
        self.assertFalse(polled["inclusion_verified"])

        status, receipt = request_json(f"http://127.0.0.1:{self.receipt_port}/v1/receipts/{request_id}")
        self.assertEqual(status, 409)
        self.assertEqual(receipt["trust_state"], "included_unverified")
        self.assertEqual(receipt["verification_policy"], "quorum")
        self.assertEqual(receipt["verification_min_success"], 2)

        status, audit_chain = request_json(f"http://127.0.0.1:{self.audit_port}/v1/audit/chain/{request_id}")
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["verification_policy"], "quorum")
        self.assertEqual(audit_chain["record"]["verification_min_success"], 2)
        self.assertEqual(
            audit_chain["proof_chain"][-2]["details"]["verification_policy"],
            "quorum",
        )

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
        self.assertFalse(receipt["receipt_available"])
        self.assertEqual(receipt["failure_reason"], "tx_dropped")
        self.assertEqual(receipt["trust_state"], "failed")

        status, audit_chain = request_json(
            f"http://127.0.0.1:{self.audit_port}/v1/audit/chain/{request_id}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["status"], "failed")
        self.assertEqual(audit_chain["record"]["failure_reason"], "tx_dropped")
        self.assertFalse(audit_chain["record"]["receipt_available"])
        self.assertEqual(audit_chain["record"]["trust_state"], "failed")
        self.assertIsNone(audit_chain["receipt"])

        status, search = request_json(
            f"http://127.0.0.1:{self.audit_port}/v1/audit/search?trust_state=failed&limit=10",
        )
        self.assertEqual(status, 200)
        self.assertGreaterEqual(search["count"], 1)
        self.assertTrue(any(item["request_id"] == request_id for item in search["results"]))

    def test_finalized_unverified_state_exposes_trust_state_without_receipt(self) -> None:
        request_id = "9" * 64
        payload = {
            "request_id": request_id,
            "trace_id": "manual-finalized-unverified",
            "mode": "single",
            "submitter": "alice",
            "contract": "verification",
            "anchor": {
                "object_hash": "a" * 64,
                "external_ref_hash": "b" * 64,
                "commitment_id": 4242,
            },
            "tx_id": "c" * 64,
            "block_num": 222,
            "status": "finalized",
            "registered_at": "2026-04-15T00:00:00Z",
            "updated_at": "2026-04-15T00:02:00Z",
            "finalized_at": "2026-04-15T00:02:00Z",
            "failed_at": None,
            "failure_reason": None,
            "failure_details": None,
            "inclusion_verified": False,
            "inclusion_verified_at": None,
            "inclusion_verification_error": "history backend unavailable",
            "verified_action": None,
            "chain_state": {
                "head_block_num": 223,
                "last_irreversible_block_num": 223,
            },
        }
        self.watcher_server.store.upsert_request(request_id, payload)

        status, receipt = request_json(f"http://127.0.0.1:{self.receipt_port}/v1/receipts/{request_id}")
        self.assertEqual(status, 409)
        self.assertEqual(receipt["status"], "finalized")
        self.assertFalse(receipt["receipt_available"])
        self.assertEqual(receipt["trust_state"], "finalized_unverified")
        self.assertEqual(receipt["error"], "receipt is not available before inclusion verification")

        status, audit_chain = request_json(f"http://127.0.0.1:{self.audit_port}/v1/audit/chain/{request_id}")
        self.assertEqual(status, 200)
        self.assertEqual(audit_chain["record"]["trust_state"], "finalized_unverified")
        self.assertFalse(audit_chain["record"]["receipt_available"])
        self.assertIsNone(audit_chain["receipt"])
        self.assertEqual(audit_chain["proof_chain"][-1]["stage"], "block_finalized")
        self.assertEqual(audit_chain["proof_chain"][-1]["status"], "completed")
        self.assertFalse(audit_chain["proof_chain"][-1]["details"]["verification_gate_satisfied"])

    def test_startup_recovery_replays_included_request_from_sqlite_store(self) -> None:
        request_id = "7" * 64
        tx_id = "8" * 64
        block_num = 150
        self._mock_transaction(
            tx_id,
            block_num,
            [
                {
                    "block_num": block_num,
                    "act": {
                        "account": "verification",
                        "name": "submit",
                        "data": {
                            "submitter": "alice",
                            "object_hash": "a" * 64,
                            "external_ref": "b" * 64,
                        },
                    },
                }
            ],
        )
        self.mock_chain_server.chain_state = {
            "head_block_num": 151,
            "last_irreversible_block_num": 151,
        }

        sqlite_path = str(Path(self.temp_dir.name) / "startup-recovery.sqlite3")
        sqlite_store = finality_watcher.build_finality_store(
            state_backend="sqlite",
            state_db=sqlite_path,
        )
        sqlite_store.upsert_request(
            request_id,
            {
                "request_id": request_id,
                "trace_id": "startup-recovery",
                "mode": "single",
                "submitter": "alice",
                "contract": "verification",
                "rpc_url": self.mock_chain_url,
                "anchor": {
                    "object_hash": "a" * 64,
                    "external_ref_hash": "b" * 64,
                },
                "tx_id": tx_id,
                "block_num": block_num,
                "status": "included",
                "registered_at": "2026-04-15T00:00:00Z",
                "included_at": "2026-04-15T00:01:00Z",
                "updated_at": "2026-04-15T00:01:00Z",
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
            },
        )

        port = find_free_port()
        recovery_server = finality_watcher.FinalityWatcherServer(
            ("127.0.0.1", port),
            finality_watcher.FinalityWatcherHandler,
            sqlite_store,
            self.mock_chain_url,
            3600,
            self.WATCHER_AUTH_TOKEN,
        )
        try:
            recovered = sqlite_store.get_request(request_id)
            self.assertEqual(recovered["status"], "finalized")
            self.assertTrue(recovered["inclusion_verified"])
            self.assertEqual(recovery_server.startup_checks["recoverable_request_count"], 1)
            self.assertEqual(recovery_server.startup_recovery["attempted"], 1)
            self.assertEqual(recovery_server.startup_recovery["finalized"], 1)
            self.assertEqual(recovery_server.store.describe()["backend"], "sqlite")
        finally:
            recovery_server.server_close()


if __name__ == "__main__":
    unittest.main()
