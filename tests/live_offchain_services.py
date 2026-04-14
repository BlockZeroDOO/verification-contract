from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from live_chain_integration import (
    DENOTARY_CHAIN_ID,
    LocalServiceStack,
    assert_equal,
    assert_status,
    ensure_chain_identity,
    ensure_kyc_state,
    extract_tx_metadata,
    get_table_rows,
    log,
    prepare_batch_payload,
    prepare_single_payload,
    request_json,
    require_command,
    run_cleos_push_action,
    wait_for_finalized,
    wait_for_row,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live off-chain service tests against a real chain.")
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
    parser.add_argument("--watcher-auth-token", default="live-offchain-shared-token")
    parser.add_argument("--wait-timeout-sec", type=int, default=180)
    parser.add_argument("--poll-interval-sec", type=float, default=3.0)
    return parser.parse_args()


def request_text(
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, str, Dict[str, str]]:
    data = None
    request_headers: Dict[str, str] = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, body, dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, body, dict(exc.headers.items())


def watcher_headers(args: argparse.Namespace) -> Dict[str, str]:
    if not args.watcher_auth_token:
        return {}
    return {"X-DeNotary-Token": args.watcher_auth_token}


def assert_true(value: bool, context: str) -> None:
    if not value:
        raise AssertionError(context)


def assert_in(member: str, container: str, context: str) -> None:
    if member not in container:
        raise AssertionError(f"{context}: expected {member!r} to be present")


def assert_healthz(services: LocalServiceStack) -> None:
    log("Checking health endpoints for all off-chain services")
    for name, base_url, expected_service in (
        ("ingress", services.ingress_base_url, "ingress-api"),
        ("finality", services.watcher_base_url, "finality-watcher"),
        ("receipt", services.receipt_base_url, "receipt-service"),
        ("audit", services.audit_base_url, "audit-api"),
    ):
        status_code, payload = request_json(f"{base_url}/healthz")
        assert_status(status_code, 200, f"{name} healthz")
        assert_equal(payload["status"], "ok", f"{name} health status")
        assert_equal(payload["service"], expected_service, f"{name} service label")


def exercise_ingress_surface(
    args: argparse.Namespace,
    services: LocalServiceStack,
    schema_id: int,
    single_policy_id: int,
    batch_policy_id: int,
    suffix: str,
) -> None:
    log("Checking ingress default and debug-material behavior")

    single_payload = prepare_single_payload(
        schema_id,
        single_policy_id,
        args.submitter_account,
        f"svc-single-{suffix}",
        args.kyc_expires_at,
    )
    status_code, single_default = request_json(
        f"{services.ingress_base_url}/v1/single/prepare",
        method="POST",
        payload=single_payload,
    )
    assert_status(status_code, 200, "single prepare default")
    assert_true("canonical_form" not in single_default, "single prepare should redact canonical_form by default")

    single_debug_payload = dict(single_payload)
    single_debug_payload["include_debug_material"] = True
    status_code, single_debug = request_json(
        f"{services.ingress_base_url}/v1/single/prepare",
        method="POST",
        payload=single_debug_payload,
    )
    assert_status(status_code, 200, "single prepare with debug")
    assert_in("canonical_form", single_debug, "single debug response")
    assert_equal(single_default["request_id"], single_debug["request_id"], "single request_id stability")
    assert_equal(single_default["object_hash"], single_debug["object_hash"], "single object_hash stability")

    batch_payload = prepare_batch_payload(
        schema_id,
        batch_policy_id,
        args.submitter_account,
        f"svc-batch-{suffix}",
        args.kyc_expires_at,
    )
    status_code, batch_default = request_json(
        f"{services.ingress_base_url}/v1/batch/prepare",
        method="POST",
        payload=batch_payload,
    )
    assert_status(status_code, 200, "batch prepare default")
    assert_true("manifest" not in batch_default, "batch prepare should redact manifest by default")
    assert_true("leaf_hashes" not in batch_default, "batch prepare should redact leaf_hashes by default")

    batch_debug_payload = dict(batch_payload)
    batch_debug_payload["include_debug_material"] = True
    status_code, batch_debug = request_json(
        f"{services.ingress_base_url}/v1/batch/prepare",
        method="POST",
        payload=batch_debug_payload,
    )
    assert_status(status_code, 200, "batch prepare with debug")
    assert_in("manifest", batch_debug, "batch debug manifest")
    assert_in("leaf_hashes", batch_debug, "batch debug leaf hashes")
    assert_equal(batch_default["request_id"], batch_debug["request_id"], "batch request_id stability")
    assert_equal(batch_default["manifest_hash"], batch_debug["manifest_hash"], "batch manifest_hash stability")
    assert_equal(batch_default["root_hash"], batch_debug["root_hash"], "batch root_hash stability")

    log("Checking ingress validation on invalid payloads")
    invalid_single_payload = dict(single_payload)
    invalid_single_payload["payload"] = None
    status_code, invalid_response = request_json(
        f"{services.ingress_base_url}/v1/single/prepare",
        method="POST",
        payload=invalid_single_payload,
    )
    assert_status(status_code, 400, "single prepare invalid payload")
    assert_equal(invalid_response["error"], "payload must not be null", "single invalid payload message")


def exercise_failed_request_surface(
    args: argparse.Namespace,
    services: LocalServiceStack,
    schema_id: int,
    single_policy_id: int,
    suffix: str,
) -> None:
    log("Checking watcher auth, failed-request handling, and audit visibility")

    prepared_payload = prepare_single_payload(
        schema_id,
        single_policy_id,
        args.submitter_account,
        f"svc-failed-{suffix}",
        args.kyc_expires_at,
    )
    status_code, prepared = request_json(
        f"{services.ingress_base_url}/v1/single/prepare",
        method="POST",
        payload=prepared_payload,
    )
    assert_status(status_code, 200, "failed-surface prepare")

    register_payload = {
        "request_id": prepared["request_id"],
        "trace_id": prepared["trace_id"],
        "mode": "single",
        "submitter": args.submitter_account,
        "contract": args.verification_account,
        "anchor": {
            "object_hash": prepared["object_hash"],
            "external_ref_hash": prepared["external_ref_hash"],
        },
        "rpc_url": args.rpc_url,
    }

    status_code, unauthorized = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload=register_payload,
    )
    assert_status(status_code, 401, "watcher register without auth")
    assert_in("requires valid auth token", unauthorized["error"], "watcher auth rejection")

    status_code, registered = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload=register_payload,
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "watcher register with auth")
    assert_equal(registered["status"], "submitted", "failed-surface registered status")

    status_code, registered_again = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload=register_payload,
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "watcher idempotent re-register")
    assert_equal(registered_again["request_id"], prepared["request_id"], "idempotent re-register request_id")

    conflict_payload = dict(register_payload)
    conflict_payload["submitter"] = args.owner_account
    status_code, conflict_response = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload=conflict_payload,
        headers=watcher_headers(args),
    )
    assert_status(status_code, 400, "watcher conflicting re-register")
    assert_in("does not match existing request", conflict_response["error"], "watcher conflicting re-register message")

    status_code, watcher_record = request_json(f"{services.watcher_base_url}/v1/watch/{prepared['request_id']}")
    assert_status(status_code, 200, "watcher get request")
    assert_equal(watcher_record["status"], "submitted", "watcher get request status")

    status_code, failed = request_json(
        f"{services.watcher_base_url}/v1/watch/{prepared['request_id']}/failed",
        method="POST",
        payload={"reason": "tx_dropped", "details": {"note": "manual live test failure path"}},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "watcher mark failed")
    assert_equal(failed["status"], "failed", "failed request status")
    assert_equal(failed["failure_reason"], "tx_dropped", "failed request reason")

    status_code, pending_receipt = request_json(
        f"{services.receipt_base_url}/v1/receipts/{prepared['request_id']}",
    )
    assert_status(status_code, 409, "failed request receipt conflict")
    assert_equal(pending_receipt["status"], "failed", "failed receipt status")
    assert_equal(pending_receipt["failure_reason"], "tx_dropped", "failed receipt reason")

    status_code, included_error = request_json(
        f"{services.watcher_base_url}/v1/watch/{prepared['request_id']}/included",
        method="POST",
        payload={"tx_id": "a" * 64, "block_num": 1},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 400, "failed request inclusion rejection")
    assert_equal(included_error["error"], "failed request cannot move to included", "failed request inclusion message")

    status_code, anchor_error = request_json(
        f"{services.watcher_base_url}/v1/watch/{prepared['request_id']}/anchor",
        method="POST",
        payload={"anchor": {"commitment_id": 999}},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 400, "failed request anchor rejection")
    assert_equal(anchor_error["error"], "terminal request cannot accept new anchor mutations", "failed anchor rejection")

    status_code, audit_record = request_json(f"{services.audit_base_url}/v1/audit/requests/{prepared['request_id']}")
    assert_status(status_code, 200, "failed audit request record")
    assert_equal(audit_record["status"], "failed", "failed audit request status")

    status_code, audit_chain = request_json(f"{services.audit_base_url}/v1/audit/chain/{prepared['request_id']}")
    assert_status(status_code, 200, "failed audit chain")
    assert_equal(audit_chain["record"]["status"], "failed", "failed audit chain record status")
    assert_equal(audit_chain["receipt"], None, "failed audit chain receipt")

    query = urllib.parse.urlencode({"status": "failed", "mode": "single", "limit": 5, "offset": 0})
    status_code, search_payload = request_json(f"{services.audit_base_url}/v1/audit/search?{query}")
    assert_status(status_code, 200, "failed audit search")
    assert_true(search_payload["count"] >= 1, "failed audit search should return at least one record")


def run_single_offchain_surface(
    args: argparse.Namespace,
    services: LocalServiceStack,
    schema_id: int,
    single_policy_id: int,
    suffix: str,
) -> None:
    log("Running live single flow with extended off-chain assertions")

    external_ref = f"svc-live-single-{suffix}"
    permission = f"{args.submitter_account}@active"
    prepare_payload = prepare_single_payload(
        schema_id,
        single_policy_id,
        args.submitter_account,
        external_ref,
        args.kyc_expires_at,
    )
    prepare_payload["include_debug_material"] = True

    status_code, prepared = request_json(
        f"{services.ingress_base_url}/v1/single/prepare",
        method="POST",
        payload=prepare_payload,
    )
    assert_status(status_code, 200, "single live prepare")
    assert_in("canonical_form", prepared, "single live debug material")

    request_id = prepared["request_id"]
    external_ref_hash = prepared["external_ref_hash"]

    register_payload = {
        "request_id": request_id,
        "trace_id": prepared["trace_id"],
        "mode": "single",
        "submitter": args.submitter_account,
        "contract": args.verification_account,
        "anchor": {
            "object_hash": prepared["object_hash"],
            "external_ref_hash": external_ref_hash,
        },
        "rpc_url": args.rpc_url,
    }
    status_code, registered = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload=register_payload,
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "single watcher register")
    assert_equal(registered["status"], "submitted", "single watcher status")

    status_code, pending_receipt = request_json(f"{services.receipt_base_url}/v1/receipts/{request_id}")
    assert_status(status_code, 409, "single receipt pending")
    assert_equal(pending_receipt["status"], "submitted", "single pending receipt status")

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

    status_code, anchored = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/anchor",
        method="POST",
        payload={"anchor": {"commitment_id": commitment_id}},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "single watcher anchor")
    assert_equal(anchored["anchor"]["commitment_id"], commitment_id, "single watcher commitment id")

    status_code, included = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/included",
        method="POST",
        payload={"tx_id": tx_id, "block_num": block_num},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "single watcher included")
    assert_equal(included["status"], "included", "single watcher included status")

    status_code, poll_all = request_json(
        f"{services.watcher_base_url}/v1/watch/poll",
        method="POST",
        payload={},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "watcher global poll")
    assert_true(request_id in poll_all["updated"], "watcher global poll should include request_id")

    finalized = wait_for_finalized(
        services.watcher_base_url,
        request_id,
        args.wait_timeout_sec,
        args.poll_interval_sec,
        watcher_headers(args),
    )
    assert_equal(finalized["status"], "finalized", "single final status")

    status_code, receipt = request_json(f"{services.receipt_base_url}/v1/receipts/{request_id}")
    assert_status(status_code, 200, "single receipt finalized")
    assert_equal(receipt["tx_id"], tx_id, "single receipt tx_id")
    assert_equal(receipt["block_num"], block_num, "single receipt block_num")

    status_code, audit_request = request_json(f"{services.audit_base_url}/v1/audit/requests/{request_id}")
    assert_status(status_code, 200, "single audit request endpoint")
    assert_equal(audit_request["commitment_id"], commitment_id, "single audit request commitment_id")

    status_code, audit_chain = request_json(f"{services.audit_base_url}/v1/audit/chain/{request_id}")
    assert_status(status_code, 200, "single audit chain endpoint")
    assert_equal(audit_chain["record"]["tx_id"], tx_id, "single audit chain tx_id")
    assert_equal(audit_chain["receipt"]["request_id"], request_id, "single audit chain receipt request_id")

    status_code, audit_by_commitment = request_json(f"{services.audit_base_url}/v1/audit/by-commitment/{commitment_id}")
    assert_status(status_code, 200, "single audit by commitment")
    assert_equal(audit_by_commitment["record"]["request_id"], request_id, "single audit by commitment request_id")

    status_code, audit_by_tx = request_json(f"{services.audit_base_url}/v1/audit/by-tx/{tx_id}")
    assert_status(status_code, 200, "single audit by tx")
    assert_equal(audit_by_tx["record"]["commitment_id"], commitment_id, "single audit by tx commitment_id")

    status_code, audit_by_external_ref = request_json(
        f"{services.audit_base_url}/v1/audit/by-external-ref/{external_ref_hash}"
    )
    assert_status(status_code, 200, "single audit by external_ref")
    assert_equal(audit_by_external_ref["record"]["tx_id"], tx_id, "single audit by external_ref tx_id")

    search_query = urllib.parse.urlencode(
        {
            "mode": "single",
            "status": "finalized",
            "submitter": args.submitter_account,
            "contract": args.verification_account,
            "commitment_id": commitment_id,
            "limit": 10,
        }
    )
    status_code, search_payload = request_json(f"{services.audit_base_url}/v1/audit/search?{search_query}")
    assert_status(status_code, 200, "single audit search")
    assert_true(search_payload["count"] >= 1, "single audit search should return at least one record")

    jsonl_query = urllib.parse.urlencode({"commitment_id": commitment_id, "format": "jsonl"})
    status_code, jsonl_body, headers = request_text(f"{services.audit_base_url}/v1/audit/search?{jsonl_query}")
    assert_status(status_code, 200, "single audit jsonl")
    assert_in("application/x-ndjson", headers.get("Content-Type", ""), "single audit jsonl content-type")
    jsonl_lines = [line for line in jsonl_body.splitlines() if line.strip()]
    assert_true(len(jsonl_lines) >= 1, "single audit jsonl should contain at least one line")
    first_jsonl_item = json.loads(jsonl_lines[0])
    assert_equal(first_jsonl_item["commitment_id"], commitment_id, "single audit jsonl commitment_id")


def run_batch_offchain_surface(
    args: argparse.Namespace,
    services: LocalServiceStack,
    schema_id: int,
    batch_policy_id: int,
    suffix: str,
) -> None:
    log("Running live batch flow with extended off-chain assertions")

    external_ref = f"svc-live-batch-{suffix}"
    permission = f"{args.submitter_account}@active"
    prepare_payload = prepare_batch_payload(
        schema_id,
        batch_policy_id,
        args.submitter_account,
        external_ref,
        args.kyc_expires_at,
    )
    prepare_payload["include_debug_material"] = True

    status_code, prepared = request_json(
        f"{services.ingress_base_url}/v1/batch/prepare",
        method="POST",
        payload=prepare_payload,
    )
    assert_status(status_code, 200, "batch live prepare")
    assert_in("manifest", prepared, "batch live debug material")

    request_id = prepared["request_id"]
    external_ref_hash = prepared["external_ref_hash"]

    register_payload = {
        "request_id": request_id,
        "trace_id": prepared["trace_id"],
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
    }
    status_code, registered = request_json(
        f"{services.watcher_base_url}/v1/watch/register",
        method="POST",
        payload=register_payload,
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "batch watcher register")
    assert_equal(registered["status"], "submitted", "batch watcher status")

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
    submitroot_tx_id, _ = extract_tx_metadata(submitroot_result)

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

    linkmanifest_result = run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "linkmanifest",
        [batch_id, prepared["manifest_hash"]],
        permission,
    )
    linkmanifest_tx_id, _ = extract_tx_metadata(linkmanifest_result)

    closebatch_result = run_cleos_push_action(
        args.rpc_url,
        args.verification_account,
        "closebatch",
        [batch_id],
        permission,
    )
    closebatch_tx_id, closebatch_block_num = extract_tx_metadata(closebatch_result)

    status_code, anchored = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/anchor",
        method="POST",
        payload={"anchor": {"batch_id": batch_id}},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "batch watcher anchor")
    assert_equal(anchored["anchor"]["batch_id"], batch_id, "batch watcher batch_id")

    status_code, included = request_json(
        f"{services.watcher_base_url}/v1/watch/{request_id}/included",
        method="POST",
        payload={"tx_id": closebatch_tx_id, "block_num": closebatch_block_num},
        headers=watcher_headers(args),
    )
    assert_status(status_code, 200, "batch watcher included")
    assert_equal(included["status"], "included", "batch watcher included status")

    finalized = wait_for_finalized(
        services.watcher_base_url,
        request_id,
        args.wait_timeout_sec,
        args.poll_interval_sec,
        watcher_headers(args),
    )
    assert_equal(finalized["status"], "finalized", "batch final status")

    status_code, receipt = request_json(f"{services.receipt_base_url}/v1/receipts/{request_id}")
    assert_status(status_code, 200, "batch receipt finalized")
    assert_equal(receipt["tx_id"], closebatch_tx_id, "batch receipt tx_id")
    assert_equal(receipt["manifest_hash"], prepared["manifest_hash"], "batch receipt manifest_hash")
    assert_equal(receipt["root_hash"], prepared["root_hash"], "batch receipt root_hash")

    status_code, audit_request = request_json(f"{services.audit_base_url}/v1/audit/requests/{request_id}")
    assert_status(status_code, 200, "batch audit request endpoint")
    assert_equal(audit_request["batch_id"], batch_id, "batch audit request batch_id")

    status_code, audit_chain = request_json(f"{services.audit_base_url}/v1/audit/chain/{request_id}")
    assert_status(status_code, 200, "batch audit chain endpoint")
    assert_equal(audit_chain["receipt"]["request_id"], request_id, "batch audit chain receipt request_id")

    status_code, audit_by_batch = request_json(f"{services.audit_base_url}/v1/audit/by-batch/{batch_id}")
    assert_status(status_code, 200, "batch audit by batch")
    assert_equal(audit_by_batch["record"]["tx_id"], closebatch_tx_id, "batch audit by batch tx_id")

    status_code, audit_by_external_ref = request_json(
        f"{services.audit_base_url}/v1/audit/by-external-ref/{external_ref_hash}"
    )
    assert_status(status_code, 200, "batch audit by external_ref")
    assert_equal(audit_by_external_ref["record"]["batch_id"], batch_id, "batch audit by external_ref batch_id")

    search_query = urllib.parse.urlencode(
        {
            "mode": "batch",
            "status": "finalized",
            "submitter": args.submitter_account,
            "batch_id": batch_id,
            "limit": 10,
        }
    )
    status_code, search_payload = request_json(f"{services.audit_base_url}/v1/audit/search?{search_query}")
    assert_status(status_code, 200, "batch audit search")
    assert_true(search_payload["count"] >= 1, "batch audit search should return at least one record")

    log(
        "Batch off-chain surface passed; "
        f"batch_id={batch_id}, submitroot_tx={submitroot_tx_id}, linkmanifest_tx={linkmanifest_tx_id}, closebatch_tx={closebatch_tx_id}"
    )


def main() -> int:
    args = parse_args()
    require_command("cleos")
    ensure_chain_identity(args)

    suffix = str(int(time.time()))
    schema_id = int(time.time()) + 4000
    single_policy_id = schema_id + 1000
    batch_policy_id = schema_id + 1001

    with LocalServiceStack(args.rpc_url, args.verification_account, args.watcher_auth_token) as services:
        assert_healthz(services)
        ensure_kyc_state(args, args.submitter_account)

        owner_permission = f"{args.owner_account}@active"
        log("Creating live schema and policies for off-chain service tests")
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "addschema",
            [
                schema_id,
                "1.0.0",
                "a" * 64,
                "b" * 64,
            ],
            owner_permission,
        )
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "setpolicy",
            [single_policy_id, True, False, False, 0, True],
            owner_permission,
        )
        run_cleos_push_action(
            args.rpc_url,
            args.verification_account,
            "setpolicy",
            [batch_policy_id, False, True, False, 0, True],
            owner_permission,
        )

        exercise_ingress_surface(args, services, schema_id, single_policy_id, batch_policy_id, suffix)
        exercise_failed_request_surface(args, services, schema_id, single_policy_id, suffix)
        run_single_offchain_surface(args, services, schema_id, single_policy_id, suffix)
        run_batch_offchain_surface(args, services, schema_id, batch_policy_id, suffix)

    log("All live off-chain service tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
