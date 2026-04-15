from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = PROJECT_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import audit_api  # noqa: E402
import finality_watcher  # noqa: E402
import ingress_api  # noqa: E402
import receipt_service  # noqa: E402

DENOTARY_CHAIN_ID = "9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48"


def log(message: str) -> None:
    print(f"[live-chain] {message}", flush=True)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def request_json(
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Dict[str, Any]]:
    data = None
    request_headers: Dict[str, str] = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def rpc_post_json(rpc_url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    request = urllib.request.Request(
        f"{rpc_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_chain_info(rpc_url: str) -> Dict[str, Any]:
    return rpc_post_json(rpc_url, "/v1/chain/get_info", {})


def get_table_rows(rpc_url: str, code: str, scope: str, table: str, limit: int = 1000) -> List[Dict[str, Any]]:
    response = rpc_post_json(
        rpc_url,
        "/v1/chain/get_table_rows",
        {
            "json": True,
            "code": code,
            "scope": scope,
            "table": table,
            "limit": limit,
        },
    )
    rows = response.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError(f"unexpected get_table_rows response for table '{table}'")
    return rows


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"{name} is required but was not found in PATH")


def run_cleos_push_action(
    rpc_url: str,
    contract: str,
    action: str,
    data: List[Any],
    permission: str,
) -> Dict[str, Any]:
    command = [
        "cleos",
        "-u",
        rpc_url,
        "push",
        "action",
        contract,
        action,
        json.dumps(data, separators=(",", ":"), ensure_ascii=False),
        "-p",
        permission,
        "-j",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"cleos push action {contract} {action} failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"cleos push action {contract} {action} returned non-JSON output:\n{completed.stdout}"
        ) from exc


def assert_cleos_push_action_fails(
    rpc_url: str,
    contract: str,
    action: str,
    data: List[Any],
    permission: str,
    expected_substring: str,
) -> None:
    command = [
        "cleos",
        "-u",
        rpc_url,
        "push",
        "action",
        contract,
        action,
        json.dumps(data, separators=(",", ":"), ensure_ascii=False),
        "-p",
        permission,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode == 0:
        raise AssertionError(f"expected cleos push action {contract} {action} to fail")

    combined_output = f"{completed.stdout}\n{completed.stderr}"
    if expected_substring not in combined_output:
        raise AssertionError(
            f"expected cleos failure output for {contract} {action} to contain {expected_substring!r}, got:\n"
            f"{combined_output}"
        )


def extract_tx_metadata(result: Dict[str, Any]) -> Tuple[str, int]:
    tx_id = result.get("transaction_id")
    processed = result.get("processed", {})
    block_num = processed.get("block_num")

    if not isinstance(tx_id, str) or len(tx_id) != 64:
        raise RuntimeError(f"unexpected cleos result: missing transaction_id in {result}")
    if not isinstance(block_num, int) or block_num <= 0:
        raise RuntimeError(f"unexpected cleos result: missing processed.block_num in {result}")

    return tx_id.lower(), block_num


def wait_for_row(
    rpc_url: str,
    code: str,
    scope: str,
    table: str,
    field_name: str,
    expected_value: Any,
    timeout_sec: int,
    interval_sec: float,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_sec
    while True:
        rows = get_table_rows(rpc_url, code, scope, table)
        for row in rows:
            if row.get(field_name) == expected_value:
                return row
        if time.time() >= deadline:
            raise TimeoutError(f"timed out waiting for {table}.{field_name} == {expected_value}")
        time.sleep(interval_sec)


def wait_for_finalized(
    watcher_base_url: str,
    request_id: str,
    timeout_sec: int,
    interval_sec: float,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_sec
    last_status = "submitted"
    while True:
        status_code, payload = request_json(
            f"{watcher_base_url}/v1/watch/{request_id}/poll",
            method="POST",
            payload={},
            headers=headers,
        )
        if status_code != 200:
            raise RuntimeError(f"watcher poll failed for {request_id}: {payload}")

        last_status = payload.get("status", last_status)
        if last_status == "finalized":
            return payload

        if time.time() >= deadline:
            raise TimeoutError(f"timed out waiting for finality on {request_id}; last status was {last_status}")
        time.sleep(interval_sec)


def assert_status(actual: int, expected: int, context: str) -> None:
    if actual != expected:
        raise AssertionError(f"{context}: expected HTTP {expected}, got HTTP {actual}")


def assert_equal(actual: Any, expected: Any, context: str) -> None:
    if actual != expected:
        raise AssertionError(f"{context}: expected {expected!r}, got {actual!r}")


class LocalServiceStack:
    def __init__(self, rpc_url: str, contract_account: str, watcher_auth_token: str = ""):
        self.rpc_url = rpc_url
        self.contract_account = contract_account
        self.watcher_auth_token = watcher_auth_token
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = str(Path(self.temp_dir.name) / "finality-state.json")
        self.state_db = str(Path(self.temp_dir.name) / "finality-state.sqlite3")
        self.threads: Dict[str, threading.Thread] = {}
        self.servers: Dict[str, Any] = {}

        self.ingress_port = find_free_port()
        self.watcher_port = find_free_port()
        self.receipt_port = find_free_port()
        self.audit_port = find_free_port()

    @property
    def ingress_base_url(self) -> str:
        return f"http://127.0.0.1:{self.ingress_port}"

    @property
    def watcher_base_url(self) -> str:
        return f"http://127.0.0.1:{self.watcher_port}"

    @property
    def receipt_base_url(self) -> str:
        return f"http://127.0.0.1:{self.receipt_port}"

    @property
    def audit_base_url(self) -> str:
        return f"http://127.0.0.1:{self.audit_port}"

    def __enter__(self) -> "LocalServiceStack":
        self._start_ingress()
        self._start_watcher()
        self._start_receipt()
        self._start_audit()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        for name in list(self.servers.keys())[::-1]:
            self._stop_server(name)
        self.temp_dir.cleanup()

    def _start_server(self, name: str, server: Any) -> None:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers[name] = server
        self.threads[name] = thread
        time.sleep(0.05)

    def _stop_server(self, name: str) -> None:
        server = self.servers.pop(name, None)
        thread = self.threads.pop(name, None)
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=2)
        time.sleep(0.05)

    def _build_store(self):
        return finality_watcher.build_finality_store(
            state_backend="sqlite",
            state_file=self.state_file,
            state_db=self.state_db,
        )

    def _start_ingress(self) -> None:
        self._start_server(
            "ingress",
            ingress_api.IngressHttpServer(
                ("127.0.0.1", self.ingress_port),
                ingress_api.IngressApiHandler,
                self.contract_account,
            ),
        )

    def _start_watcher(self) -> None:
        self._start_server(
            "watcher",
            finality_watcher.FinalityWatcherServer(
                ("127.0.0.1", self.watcher_port),
                finality_watcher.FinalityWatcherHandler,
                self._build_store(),
                self.rpc_url,
                3600,
                self.watcher_auth_token,
            ),
        )

    def _start_receipt(self) -> None:
        self._start_server(
            "receipt",
            receipt_service.ReceiptServiceServer(
                ("127.0.0.1", self.receipt_port),
                receipt_service.ReceiptServiceHandler,
                self._build_store(),
            ),
        )

    def _start_audit(self) -> None:
        self._start_server(
            "audit",
            audit_api.AuditApiServer(
                ("127.0.0.1", self.audit_port),
                audit_api.AuditApiHandler,
                self._build_store(),
            ),
        )

    def restart_watcher(self) -> None:
        self._stop_server("watcher")
        self._start_watcher()

    def restart_receipt(self) -> None:
        self._stop_server("receipt")
        self._start_receipt()

    def restart_audit(self) -> None:
        self._stop_server("audit")
        self._start_audit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live-chain DeNotary integration tests.")
    parser.add_argument("--rpc-url", default="https://history.denotary.io")
    parser.add_argument("--expected-chain-id", default=DENOTARY_CHAIN_ID)
    parser.add_argument("--skip-chain-id-check", action="store_true")
    parser.add_argument("--network-label", default="deNotary.io")
    parser.add_argument("--verification-account", default="verification")
    parser.add_argument("--owner-account", required=True)
    parser.add_argument("--submitter-account", required=True)
    parser.add_argument("--kyc-provider", default="denotary-kyc")
    parser.add_argument("--kyc-jurisdiction", default="EU")
    parser.add_argument("--kyc-level", type=int, default=2)
    parser.add_argument("--kyc-expires-at", default="2030-01-01T00:00:00")
    parser.add_argument("--watcher-auth-token", default="live-chain-shared-token")
    parser.add_argument("--wait-timeout-sec", type=int, default=180)
    parser.add_argument("--poll-interval-sec", type=float, default=3.0)
    return parser.parse_args()


def ensure_chain_identity(args: argparse.Namespace) -> None:
    chain_info = get_chain_info(args.rpc_url)
    actual_chain_id = chain_info.get("chain_id")
    log(f"Connected to {args.network_label}; head={chain_info.get('head_block_num')} lib={chain_info.get('last_irreversible_block_num')}")
    if args.skip_chain_id_check:
        return
    if actual_chain_id != args.expected_chain_id:
        raise RuntimeError(
            f"unexpected chain id for {args.network_label}: expected {args.expected_chain_id}, got {actual_chain_id}"
        )


def ensure_kyc_state(
    args: argparse.Namespace,
    submitter: str,
) -> None:
    rows = get_table_rows(args.rpc_url, args.verification_account, args.verification_account, "kyc")
    existing = next((row for row in rows if row.get("account") == submitter), None)
    permission = f"{args.owner_account}@active"

    if existing is None:
        log("Creating KYC record for submitter")
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "issuekyc",
            [
                submitter,
                args.kyc_level,
                args.kyc_provider,
                args.kyc_jurisdiction,
                args.kyc_expires_at,
            ],
            permission,
        )
        return

    log("Renewing existing KYC record for submitter")
    run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "renewkyc",
        [submitter, args.kyc_expires_at],
        permission,
    )


def prepare_single_payload(schema_id: int, policy_id: int, submitter: str, external_ref: str, expires_at: str) -> Dict[str, Any]:
    return {
        "submitter": submitter,
        "external_ref": external_ref,
        "schema": {
            "id": schema_id,
            "version": "1.0.0",
            "active": True,
            "canonicalization_profile": "json-sorted-v1",
        },
        "policy": {
            "id": policy_id,
            "active": True,
            "allow_single": True,
            "allow_batch": False,
            "require_kyc": False,
            "min_kyc_level": 0,
        },
        "kyc": {
            "active": True,
            "level": 2,
            "expires_at": expires_at,
        },
        "payload": {
            "doc_id": external_ref,
            "kind": "invoice",
            "amount": 42,
        },
    }


def prepare_batch_payload(schema_id: int, policy_id: int, submitter: str, external_ref: str, expires_at: str) -> Dict[str, Any]:
    return {
        "submitter": submitter,
        "external_ref": external_ref,
        "schema": {
            "id": schema_id,
            "version": "1.0.0",
            "active": True,
            "canonicalization_profile": "json-sorted-v1",
        },
        "policy": {
            "id": policy_id,
            "active": True,
            "allow_single": False,
            "allow_batch": True,
            "require_kyc": False,
            "min_kyc_level": 0,
        },
        "kyc": {
            "active": True,
            "level": 2,
            "expires_at": expires_at,
        },
        "items": [
            {"external_leaf_ref": f"{external_ref}-leaf-a", "payload": {"doc_id": "a", "amount": 1}},
            {"external_leaf_ref": f"{external_ref}-leaf-b", "payload": {"doc_id": "b", "amount": 2}},
        ],
    }


def watcher_headers(args: argparse.Namespace) -> Dict[str, str]:
    if not args.watcher_auth_token:
        return {}
    return {"X-DeNotary-Token": args.watcher_auth_token}


def run_single_flow(args: argparse.Namespace, services: LocalServiceStack, schema_id: int, policy_id: int, suffix: str) -> None:
    external_ref = f"live-single-{suffix}"
    permission = f"{args.submitter_account}@active"

    log("Preparing live single request through Ingress API")
    status_code, prepared = request_json(
        f"{services.ingress_base_url}/v1/single/prepare",
        method="POST",
        payload=prepare_single_payload(
            schema_id,
            policy_id,
            args.submitter_account,
            external_ref,
            args.kyc_expires_at,
        ),
    )
    assert_status(status_code, 200, "single prepare")

    request_id = prepared["request_id"]
    trace_id = prepared["trace_id"]
    external_ref_hash = prepared["external_ref_hash"]

    log("Registering single request in Finality Watcher")
    status_code, registered = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload={
            "request_id": request_id,
            "trace_id": trace_id,
            "mode": "single",
            "submitter": args.submitter_account,
            "contract": args.verification_account,
            "anchor": {
                "object_hash": prepared["object_hash"],
                "external_ref_hash": external_ref_hash,
            },
            "rpc_url": args.rpc_url,
        },
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "single watcher register")
    assert_equal(registered["status"], "submitted", "single watcher status after register")

    status_code, pending_receipt = request_json(
        f"{services.receipt_base_url}/v1/receipts/{request_id}",
    )
    assert_status(status_code, 409, "single receipt before finality")
    assert_equal(pending_receipt["status"], "submitted", "single receipt status before finality")

    log("Broadcasting live single submit transaction")
    submit_result = run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "submit",
        [
            prepared["prepared_action"]["data"]["submitter"],
            prepared["prepared_action"]["data"]["schema_id"],
            prepared["prepared_action"]["data"]["policy_id"],
            prepared["prepared_action"]["data"]["object_hash"],
            prepared["prepared_action"]["data"]["external_ref"],
        ],
        permission,
    )
    tx_id, block_num = extract_tx_metadata(submit_result)

    commitment_row = wait_for_row(
        args.rpc_url,
        args.verification_account,
        args.verification_account,
        "commitments",
        "external_ref",
        external_ref_hash,
        args.wait_timeout_sec,
        args.poll_interval_sec,
    )
    commitment_id = commitment_row["id"]
    assert_equal(commitment_row["status"], 0, "single commitment business status")

    status_code, anchored = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/anchor",
        method="POST",
        payload={"anchor": {"commitment_id": commitment_id}},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "single watcher anchor update")
    assert_equal(anchored["anchor"]["commitment_id"], commitment_id, "single watcher commitment_id")

    status_code, included = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/included",
        method="POST",
        payload={"tx_id": tx_id, "block_num": block_num},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "single watcher inclusion update")
    assert_equal(included["status"], "included", "single watcher status after inclusion")

    log("Waiting for irreversible finality on single request")
    finalized = wait_for_finalized(
        services.watcher_base_url,
        request_id,
        args.wait_timeout_sec,
        args.poll_interval_sec,
        watcher_headers(args),
    )
    assert_equal(finalized["status"], "finalized", "single watcher final status")

    status_code, receipt = request_json(f"{services.receipt_base_url}/v1/receipts/{request_id}")
    assert_status(status_code, 200, "single receipt after finality")
    assert_equal(receipt["request_id"], request_id, "single receipt request_id")
    assert_equal(receipt["tx_id"], tx_id, "single receipt tx_id")
    assert_equal(receipt["block_num"], block_num, "single receipt block_num")
    assert_equal(receipt["finality_flag"], True, "single receipt finality flag")
    assert_equal(receipt["receipt_available"], True, "single receipt availability")
    assert_equal(receipt["inclusion_verified"], True, "single receipt inclusion verification")
    assert_equal(receipt["trust_state"], "finalized_verified", "single receipt trust state")

    status_code, audit_by_commitment = request_json(f"{services.audit_base_url}/v1/audit/by-commitment/{commitment_id}")
    assert_status(status_code, 200, "single audit lookup by commitment")
    assert_equal(audit_by_commitment["record"]["request_id"], request_id, "single audit request_id")
    assert_equal(audit_by_commitment["record"]["tx_id"], tx_id, "single audit tx_id")
    assert_equal(audit_by_commitment["record"]["receipt_available"], True, "single audit receipt availability")
    assert_equal(audit_by_commitment["record"]["inclusion_verified"], True, "single audit inclusion verification")
    assert_equal(audit_by_commitment["record"]["trust_state"], "finalized_verified", "single audit trust state")

    status_code, audit_by_tx = request_json(f"{services.audit_base_url}/v1/audit/by-tx/{tx_id}")
    assert_status(status_code, 200, "single audit lookup by tx")
    assert_equal(audit_by_tx["record"]["commitment_id"], commitment_id, "single audit commitment_id from tx lookup")

    log(f"Single live-chain flow passed; commitment_id={commitment_id}, tx_id={tx_id}")


def run_negative_security_checks(
    args: argparse.Namespace,
    schema_id: int,
    policy_id: int,
    suffix: str,
) -> None:
    permission = f"{args.submitter_account}@active"
    owner_permission = f"{args.owner_account}@active"
    zero_external_ref = f"{suffix:0>64}"[-64:]

    log("Running negative on-chain security checks")
    assert_cleos_push_action_fails(
        args.rpc_url,
        args.verification_account,
        "submit",
        [
            args.submitter_account,
            schema_id,
            policy_id,
            "0" * 64,
            zero_external_ref,
        ],
        permission,
        "object_hash must be non-zero",
    )

    assert_cleos_push_action_fails(
        args.rpc_url,
        args.verification_account,
        "record",
        [
            args.submitter_account,
            "1" * 64,
            "json-sorted-v1",
            f"legacy-record-{suffix}",
        ],
        permission,
        "legacy proof flow is disabled",
    )

    assert_cleos_push_action_fails(
        args.rpc_url,
        args.verification_account,
        "setpaytoken",
        [
            "eosio.token",
            "1.0000 EOS",
        ],
        owner_permission,
        "legacy proof payment configuration is disabled",
    )


def run_batch_flow(args: argparse.Namespace, services: LocalServiceStack, schema_id: int, policy_id: int, suffix: str) -> None:
    external_ref = f"live-batch-{suffix}"
    permission = f"{args.submitter_account}@active"

    log("Preparing live batch request through Ingress API")
    status_code, prepared = request_json(
        f"{services.ingress_base_url}/v1/batch/prepare",
        method="POST",
        payload=prepare_batch_payload(
            schema_id,
            policy_id,
            args.submitter_account,
            external_ref,
            args.kyc_expires_at,
        ),
    )
    assert_status(status_code, 200, "batch prepare")

    request_id = prepared["request_id"]
    trace_id = prepared["trace_id"]
    external_ref_hash = prepared["external_ref_hash"]

    log("Registering batch request in Finality Watcher")
    status_code, registered = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload={
            "request_id": request_id,
            "trace_id": trace_id,
            "mode": "batch",
            "submitter": args.submitter_account,
            "contract": args.verification_account,
            "anchor": {
                "root_hash": prepared["root_hash"],
                "manifest_hash": prepared["manifest_hash"],
                "external_ref_hash": external_ref_hash,
                "leaf_count": prepared["leaf_count"],
            },
            "rpc_url": args.rpc_url,
        },
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "batch watcher register")
    assert_equal(registered["status"], "submitted", "batch watcher status after register")

    log("Broadcasting live batch submitroot transaction")
    submitroot_result = run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "submitroot",
        [
            prepared["prepared_action"]["data"]["submitter"],
            prepared["prepared_action"]["data"]["schema_id"],
            prepared["prepared_action"]["data"]["policy_id"],
            prepared["prepared_action"]["data"]["root_hash"],
            prepared["prepared_action"]["data"]["leaf_count"],
            prepared["prepared_action"]["data"]["external_ref"],
        ],
        permission,
    )
    submitroot_tx_id, submitroot_block_num = extract_tx_metadata(submitroot_result)
    log(f"submitroot accepted in tx {submitroot_tx_id} at block {submitroot_block_num}")

    batch_row = wait_for_row(
        args.rpc_url,
        args.verification_account,
        args.verification_account,
        "batches",
        "external_ref",
        external_ref_hash,
        args.wait_timeout_sec,
        args.poll_interval_sec,
    )
    batch_id = batch_row["id"]
    assert_equal(batch_row["status"], 0, "batch business status after submitroot")

    log("Broadcasting live batch linkmanifest transaction")
    linkmanifest_result = run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "linkmanifest",
        [batch_id, prepared["manifest_hash"]],
        permission,
    )
    linkmanifest_tx_id, linkmanifest_block_num = extract_tx_metadata(linkmanifest_result)
    log(f"linkmanifest accepted in tx {linkmanifest_tx_id} at block {linkmanifest_block_num}")

    batch_row = wait_for_row(
        args.rpc_url,
        args.verification_account,
        args.verification_account,
        "batches",
        "external_ref",
        external_ref_hash,
        args.wait_timeout_sec,
        args.poll_interval_sec,
    )
    assert_equal(batch_row["manifest_hash"], prepared["manifest_hash"], "batch manifest_hash after linkmanifest")

    log("Broadcasting live batch closebatch transaction")
    closebatch_result = run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "closebatch",
        [batch_id],
        permission,
    )
    closebatch_tx_id, closebatch_block_num = extract_tx_metadata(closebatch_result)

    batch_row = wait_for_row(
        args.rpc_url,
        args.verification_account,
        args.verification_account,
        "batches",
        "external_ref",
        external_ref_hash,
        args.wait_timeout_sec,
        args.poll_interval_sec,
    )
    assert_equal(batch_row["status"], 1, "batch business status after closebatch")

    status_code, anchored = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/anchor",
        method="POST",
        payload={"anchor": {"batch_id": batch_id}},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "batch watcher anchor update")
    assert_equal(anchored["anchor"]["batch_id"], batch_id, "batch watcher batch_id")

    status_code, included = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/included",
        method="POST",
        payload={"tx_id": closebatch_tx_id, "block_num": closebatch_block_num},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "batch watcher inclusion update")
    assert_equal(included["status"], "included", "batch watcher status after inclusion")

    log("Waiting for irreversible finality on batch request")
    finalized = wait_for_finalized(
        services.watcher_base_url,
        request_id,
        args.wait_timeout_sec,
        args.poll_interval_sec,
        watcher_headers(args),
    )
    assert_equal(finalized["status"], "finalized", "batch watcher final status")

    status_code, receipt = request_json(f"{services.receipt_base_url}/v1/receipts/{request_id}")
    assert_status(status_code, 200, "batch receipt after finality")
    assert_equal(receipt["request_id"], request_id, "batch receipt request_id")
    assert_equal(receipt["tx_id"], closebatch_tx_id, "batch receipt tx_id")
    assert_equal(receipt["block_num"], closebatch_block_num, "batch receipt block_num")
    assert_equal(receipt["manifest_hash"], prepared["manifest_hash"], "batch receipt manifest_hash")
    assert_equal(receipt["root_hash"], prepared["root_hash"], "batch receipt root_hash")
    assert_equal(receipt["receipt_available"], True, "batch receipt availability")
    assert_equal(receipt["inclusion_verified"], True, "batch receipt inclusion verification")
    assert_equal(receipt["trust_state"], "finalized_verified", "batch receipt trust state")

    status_code, audit_by_batch = request_json(f"{services.audit_base_url}/v1/audit/by-batch/{batch_id}")
    assert_status(status_code, 200, "batch audit lookup by batch")
    assert_equal(audit_by_batch["record"]["request_id"], request_id, "batch audit request_id")
    assert_equal(audit_by_batch["record"]["tx_id"], closebatch_tx_id, "batch audit tx_id")
    assert_equal(audit_by_batch["record"]["receipt_available"], True, "batch audit receipt availability")
    assert_equal(audit_by_batch["record"]["inclusion_verified"], True, "batch audit inclusion verification")
    assert_equal(audit_by_batch["record"]["trust_state"], "finalized_verified", "batch audit trust state")

    status_code, audit_by_external_ref = request_json(
        f"{services.audit_base_url}/v1/audit/by-external-ref/{external_ref_hash}"
    )
    assert_status(status_code, 200, "batch audit lookup by external_ref")
    assert_equal(audit_by_external_ref["record"]["batch_id"], batch_id, "batch audit batch_id from external_ref lookup")

    log(
        "Batch live-chain flow passed; "
        f"batch_id={batch_id}, submitroot_tx={submitroot_tx_id}, linkmanifest_tx={linkmanifest_tx_id}, closebatch_tx={closebatch_tx_id}"
    )


def main() -> int:
    args = parse_args()
    require_command("cleos")
    ensure_chain_identity(args)

    suffix = str(int(time.time()))
    schema_id = int(time.time()) + 1000
    policy_single_id = schema_id + 1000
    policy_batch_id = schema_id + 1001

    with LocalServiceStack(args.rpc_url, args.verification_account, args.watcher_auth_token) as services:
        ensure_kyc_state(args, args.submitter_account)

        log("Creating live schema and policies")
        owner_permission = f"{args.owner_account}@active"
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "addschema",
            [
                schema_id,
                "1.0.0",
                ingress_api.sha256_hex_text(f"schema-rules-{suffix}"),
                ingress_api.sha256_hex_text(f"hash-policy-{suffix}"),
            ],
            owner_permission,
        )
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "setpolicy",
            [policy_single_id, True, False, False, 0, True],
            owner_permission,
        )
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "setpolicy",
            [policy_batch_id, False, True, False, 0, True],
            owner_permission,
        )

        run_negative_security_checks(args, schema_id, policy_single_id, suffix)
        run_single_flow(args, services, schema_id, policy_single_id, suffix)
        run_batch_flow(args, services, schema_id, policy_batch_id, suffix)

    log("All live-chain integration checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
