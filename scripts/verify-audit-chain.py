#!/usr/bin/env python3
"""Run the full external audit chain from canonical row payload to on-chain verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_RPC_URL = "https://history.denotary.io"
DEFAULT_VERIFICATION_ACCOUNT = "verif"


def ensure_hex_256(value: str, field_name: str) -> str:
    normalized = value.lower()
    if len(normalized) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    try:
        int(normalized, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be valid hex") from exc
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the full external audit chain for a single anchor or a batch leaf."
    )
    parser.add_argument("--mode", choices=("single", "batch"), required=True)
    parser.add_argument("--row-json-file", required=True, help="Canonical row JSON payload.")
    parser.add_argument("--submitter", required=True)
    parser.add_argument("--schema-id", type=int, required=True)
    parser.add_argument("--policy-id", type=int, required=True)
    parser.add_argument("--external-ref", required=True, help="Expected external_ref as 64 hex.")
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--verification-account", default=DEFAULT_VERIFICATION_ACCOUNT)
    parser.add_argument(
        "--proof-file",
        help="Batch proof JSON with leaf_index and proof steps. Required for batch mode.",
    )
    parser.add_argument(
        "--allow-inactive-registry",
        action="store_true",
        help="Do not fail when schema or policy rows are inactive.",
    )
    return parser.parse_args()


def stable_json_bytes(payload: Any) -> bytes:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return canonical.encode("utf-8")


def load_json_file(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_request_key(submitter: str, external_ref_hex: str) -> str:
    payload = submitter.encode("utf-8") + b":" + bytes.fromhex(external_ref_hex)
    return sha256_hex(payload)


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_table_rows(
    rpc_url: str,
    code: str,
    scope: str,
    table: str,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    endpoint = rpc_url.rstrip("/") + "/v1/chain/get_table_rows"
    rows: list[dict[str, Any]] = []
    lower_bound: str | int | None = None

    while True:
        payload: dict[str, Any] = {
            "json": True,
            "code": code,
            "scope": scope,
            "table": table,
            "limit": limit,
        }
        if lower_bound is not None:
            payload["lower_bound"] = lower_bound
        result = post_json(endpoint, payload)
        rows.extend(result.get("rows", []))
        more = result.get("more")
        next_key = result.get("next_key")
        if not more or next_key in (None, "", lower_bound):
            break
        lower_bound = next_key

    return rows


def find_row_by_external_ref(rows: list[dict[str, Any]], external_ref: str) -> dict[str, Any]:
    matches = [row for row in rows if str(row.get("external_ref", "")).lower() == external_ref]
    if not matches:
        raise LookupError(f"no on-chain row found for external_ref {external_ref}")
    if len(matches) > 1:
        raise LookupError(f"multiple on-chain rows found for external_ref {external_ref}")
    return matches[0]


def verify_registry_row(
    rows: list[dict[str, Any]],
    row_id: int,
    field_name: str,
    expected_value: Any | None = None,
) -> dict[str, Any]:
    row = next((current for current in rows if int(current.get("id", 0)) == row_id), None)
    if row is None:
        raise LookupError(f"{field_name} row {row_id} was not found")
    matches_expected = True if expected_value is None else row.get(field_name) == expected_value
    return {
        "id": row_id,
        "exists": True,
        "active": bool(row.get("active", False)),
        field_name: row.get(field_name),
        "row": row,
        "matches_expected": matches_expected,
    }


def parse_proof_steps(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise ValueError("proof must be a list")
    steps: list[dict[str, str]] = []
    for index, item in enumerate(payload):
        if isinstance(item, str):
            steps.append({"hash": ensure_hex_256(item, f"proof[{index}]"), "side": "auto"})
            continue
        if not isinstance(item, dict):
            raise ValueError(f"proof[{index}] must be a string or object")
        side = str(item.get("side", "auto")).lower()
        if side not in ("left", "right", "auto"):
            raise ValueError(f"proof[{index}].side must be left, right, or auto")
        steps.append(
            {
                "hash": ensure_hex_256(str(item.get("hash", "")), f"proof[{index}].hash"),
                "side": side,
            }
        )
    if not steps:
        raise ValueError("proof must not be empty")
    return steps


def sha256_concat(left_hex: str, right_hex: str) -> str:
    return sha256_hex(bytes.fromhex(left_hex) + bytes.fromhex(right_hex))


def compute_merkle_root(
    leaf_hash: str,
    steps: list[dict[str, str]],
    leaf_index: int | None,
) -> dict[str, Any]:
    current = leaf_hash
    current_index = leaf_index
    resolved_steps: list[dict[str, Any]] = []

    for level, step in enumerate(steps):
        sibling = step["hash"]
        side = step["side"]
        if side == "auto":
            if current_index is None:
                raise ValueError(
                    f"proof step {level} uses side=auto but leaf_index was not provided"
                )
            side = "right" if current_index % 2 == 0 else "left"

        parent = (
            sha256_concat(sibling, current)
            if side == "left"
            else sha256_concat(current, sibling)
        )
        resolved_steps.append(
            {
                "level": level,
                "input_hash": current,
                "sibling_hash": sibling,
                "side": side,
                "parent_hash": parent,
            }
        )
        current = parent
        if current_index is not None:
            current_index //= 2

    return {"computed_root": current, "resolved_steps": resolved_steps}


def build_single_result(args: argparse.Namespace, row_payload: Any) -> dict[str, Any]:
    external_ref = ensure_hex_256(args.external_ref, "external_ref")
    object_hash = sha256_hex(stable_json_bytes(row_payload))
    request_key = compute_request_key(args.submitter, external_ref)

    commitments = get_table_rows(
        args.rpc_url, args.verification_account, args.verification_account, "commitments"
    )
    schemas = get_table_rows(
        args.rpc_url, args.verification_account, args.verification_account, "schemas"
    )
    policies = get_table_rows(
        args.rpc_url, args.verification_account, args.verification_account, "policies"
    )
    row = find_row_by_external_ref(commitments, external_ref)
    schema_status = verify_registry_row(schemas, args.schema_id, "canonicalization_hash", None)
    policy_status = verify_registry_row(policies, args.policy_id, "allow_single", True)

    checks: dict[str, bool] = {
        "submitter": row.get("submitter") == args.submitter,
        "schema_id": int(row.get("schema_id", 0)) == args.schema_id,
        "policy_id": int(row.get("policy_id", 0)) == args.policy_id,
        "external_ref": str(row.get("external_ref", "")).lower() == external_ref,
        "request_key": str(row.get("request_key", "")).lower() == request_key,
        "object_hash": str(row.get("object_hash", "")).lower() == object_hash,
        "schema_exists": schema_status["exists"],
        "policy_exists": policy_status["exists"],
        "policy_supports_mode": policy_status["matches_expected"],
    }
    if not args.allow_inactive_registry:
        checks["schema_active"] = schema_status["active"]
        checks["policy_active"] = policy_status["active"]

    return {
        "mode": "single",
        "ok": all(checks.values()),
        "derived": {
            "object_hash": object_hash,
            "request_key": request_key,
        },
        "checks": checks,
        "on_chain_row": row,
        "schema": schema_status,
        "policy": policy_status,
    }


def build_batch_result(args: argparse.Namespace, row_payload: Any) -> dict[str, Any]:
    if not args.proof_file:
        raise ValueError("--proof-file is required for --mode batch")

    proof_payload = load_json_file(args.proof_file)
    if not isinstance(proof_payload, dict):
        raise ValueError("--proof-file must contain a JSON object")

    external_ref = ensure_hex_256(
        str(proof_payload.get("external_ref", args.external_ref)), "external_ref"
    )
    leaf_hash = sha256_hex(stable_json_bytes(row_payload))
    leaf_index = proof_payload.get("leaf_index")
    if leaf_index is None:
        raise ValueError("proof file must contain leaf_index")
    if int(leaf_index) < 0:
        raise ValueError("leaf_index must be non-negative")
    proof_steps = parse_proof_steps(proof_payload.get("proof", proof_payload.get("siblings")))
    proof_result = compute_merkle_root(leaf_hash, proof_steps, int(leaf_index))

    batches = get_table_rows(
        args.rpc_url, args.verification_account, args.verification_account, "batches"
    )
    schemas = get_table_rows(
        args.rpc_url, args.verification_account, args.verification_account, "schemas"
    )
    policies = get_table_rows(
        args.rpc_url, args.verification_account, args.verification_account, "policies"
    )
    row = find_row_by_external_ref(batches, external_ref)
    request_key = compute_request_key(args.submitter, external_ref)
    schema_status = verify_registry_row(schemas, args.schema_id, "canonicalization_hash", None)
    policy_status = verify_registry_row(policies, args.policy_id, "allow_batch", True)

    expected_root = str(row.get("root_hash", "")).lower()
    manifest_hash = proof_payload.get("manifest_hash")
    leaf_count = proof_payload.get("leaf_count")

    checks: dict[str, bool] = {
        "submitter": row.get("submitter") == args.submitter,
        "schema_id": int(row.get("schema_id", 0)) == args.schema_id,
        "policy_id": int(row.get("policy_id", 0)) == args.policy_id,
        "external_ref": str(row.get("external_ref", "")).lower() == external_ref,
        "request_key": str(row.get("request_key", "")).lower() == request_key,
        "root_hash": proof_result["computed_root"] == expected_root,
        "schema_exists": schema_status["exists"],
        "policy_exists": policy_status["exists"],
        "policy_supports_mode": policy_status["matches_expected"],
    }
    if manifest_hash is not None:
        checks["manifest_hash"] = (
            str(row.get("manifest_hash", "")).lower()
            == ensure_hex_256(str(manifest_hash), "manifest_hash")
        )
    if leaf_count is not None:
        checks["leaf_count"] = int(row.get("leaf_count", 0)) == int(leaf_count)
    if not args.allow_inactive_registry:
        checks["schema_active"] = schema_status["active"]
        checks["policy_active"] = policy_status["active"]

    return {
        "mode": "batch",
        "ok": all(checks.values()),
        "derived": {
            "leaf_hash": leaf_hash,
            "request_key": request_key,
            "computed_root": proof_result["computed_root"],
        },
        "proof": proof_result,
        "checks": checks,
        "on_chain_row": row,
        "schema": schema_status,
        "policy": policy_status,
    }


def main() -> int:
    try:
        args = parse_args()
        row_payload = load_json_file(args.row_json_file)
        result = (
            build_single_result(args, row_payload)
            if args.mode == "single"
            else build_batch_result(args, row_payload)
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    result["rpc_url"] = args.rpc_url
    result["verification_account"] = args.verification_account
    result["row_json_file"] = args.row_json_file
    result["external_ref"] = args.external_ref
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
