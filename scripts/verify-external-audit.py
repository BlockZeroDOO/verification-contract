#!/usr/bin/env python3
"""Verify a single or batch anchor from the perspective of an external auditor."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_RPC_URL = "https://history.denotary.io"
DEFAULT_VERIFICATION_ACCOUNT = "verif"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a verif commitment or batch against externally supplied values."
    )
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL, help="Antelope read RPC URL.")
    parser.add_argument(
        "--verification-account",
        default=DEFAULT_VERIFICATION_ACCOUNT,
        help="Account that hosts the verif tables.",
    )
    parser.add_argument(
        "--mode",
        choices=("single", "batch"),
        required=True,
        help="Anchor mode to verify.",
    )
    parser.add_argument("--submitter", required=True, help="Expected submitter account.")
    parser.add_argument("--schema-id", type=int, required=True, help="Expected schema id.")
    parser.add_argument("--policy-id", type=int, required=True, help="Expected policy id.")
    parser.add_argument(
        "--external-ref",
        required=True,
        help="Expected external_ref as 64 hex characters.",
    )
    parser.add_argument(
        "--object-hash",
        help="Expected object_hash as 64 hex characters for single mode.",
    )
    parser.add_argument(
        "--root-hash",
        help="Expected root_hash as 64 hex characters for batch mode.",
    )
    parser.add_argument(
        "--manifest-hash",
        help="Expected manifest_hash as 64 hex characters for batch mode.",
    )
    parser.add_argument(
        "--leaf-count",
        type=int,
        help="Expected leaf_count for batch mode.",
    )
    parser.add_argument(
        "--id",
        type=int,
        help="Optional expected primary key id in commitments or batches.",
    )
    parser.add_argument(
        "--allow-inactive-registry",
        action="store_true",
        help="Do not fail if schema or policy is inactive.",
    )
    return parser.parse_args()


def ensure_hex_256(value: str, field_name: str) -> str:
    normalized = value.lower()
    if len(normalized) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    try:
        int(normalized, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be valid hex") from exc
    return normalized


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
        batch = result.get("rows", [])
        rows.extend(batch)

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


def compute_request_key(submitter: str, external_ref_hex: str) -> str:
    payload = submitter.encode("utf-8") + b":" + bytes.fromhex(external_ref_hex)
    return hashlib.sha256(payload).hexdigest()


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


def build_single_expectations(args: argparse.Namespace) -> dict[str, Any]:
    if not args.object_hash:
        raise ValueError("--object-hash is required for --mode single")
    return {
        "table": "commitments",
        "hash_field": "object_hash",
        "expected_hash": ensure_hex_256(args.object_hash, "object_hash"),
    }


def build_batch_expectations(args: argparse.Namespace) -> dict[str, Any]:
    if not args.root_hash:
        raise ValueError("--root-hash is required for --mode batch")
    if not args.manifest_hash:
        raise ValueError("--manifest-hash is required for --mode batch")
    if args.leaf_count is None:
        raise ValueError("--leaf-count is required for --mode batch")
    return {
        "table": "batches",
        "hash_field": "root_hash",
        "expected_hash": ensure_hex_256(args.root_hash, "root_hash"),
        "manifest_hash": ensure_hex_256(args.manifest_hash, "manifest_hash"),
        "leaf_count": args.leaf_count,
    }


def main() -> int:
    args = parse_args()
    external_ref = ensure_hex_256(args.external_ref, "external_ref")
    expectations = build_single_expectations(args) if args.mode == "single" else build_batch_expectations(args)

    verification_account = args.verification_account
    rpc_url = args.rpc_url

    try:
        table_rows = get_table_rows(rpc_url, verification_account, verification_account, expectations["table"])
        source_row = find_row_by_external_ref(table_rows, external_ref)
        schemas = get_table_rows(rpc_url, verification_account, verification_account, "schemas")
        policies = get_table_rows(rpc_url, verification_account, verification_account, "policies")
    except (LookupError, urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    request_key = compute_request_key(args.submitter, external_ref)
    checks: dict[str, bool] = {
        "submitter": source_row.get("submitter") == args.submitter,
        "schema_id": int(source_row.get("schema_id", 0)) == args.schema_id,
        "policy_id": int(source_row.get("policy_id", 0)) == args.policy_id,
        "external_ref": str(source_row.get("external_ref", "")).lower() == external_ref,
        "request_key": str(source_row.get("request_key", "")).lower() == request_key,
        expectations["hash_field"]: str(source_row.get(expectations["hash_field"], "")).lower() == expectations["expected_hash"],
    }
    if args.id is not None:
        checks["id"] = int(source_row.get("id", 0)) == args.id
    if args.mode == "batch":
        checks["manifest_hash"] = str(source_row.get("manifest_hash", "")).lower() == expectations["manifest_hash"]
        checks["leaf_count"] = int(source_row.get("leaf_count", 0)) == expectations["leaf_count"]

    schema_status = verify_registry_row(schemas, args.schema_id, "canonicalization_hash", None)
    policy_status = verify_registry_row(policies, args.policy_id, "allow_single" if args.mode == "single" else "allow_batch", True)
    checks["schema_exists"] = schema_status["exists"]
    checks["policy_exists"] = policy_status["exists"]
    checks["policy_supports_mode"] = policy_status["matches_expected"]

    if not args.allow_inactive_registry:
        checks["schema_active"] = schema_status["active"]
        checks["policy_active"] = policy_status["active"]

    ok = all(checks.values())
    result = {
        "ok": ok,
        "mode": args.mode,
        "rpc_url": rpc_url,
        "verification_account": verification_account,
        "table": expectations["table"],
        "checks": checks,
        "expected": {
            "submitter": args.submitter,
            "schema_id": args.schema_id,
            "policy_id": args.policy_id,
            "external_ref": external_ref,
            "request_key": request_key,
            expectations["hash_field"]: expectations["expected_hash"],
        },
        "on_chain_row": source_row,
        "schema": schema_status,
        "policy": policy_status,
    }
    if args.mode == "batch":
        result["expected"]["manifest_hash"] = expectations["manifest_hash"]
        result["expected"]["leaf_count"] = expectations["leaf_count"]

    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
