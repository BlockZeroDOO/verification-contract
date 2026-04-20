#!/usr/bin/env python3
"""Verify that a batch leaf belongs to an anchored batch root."""

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
        description="Verify a Merkle inclusion proof for a verif batch anchor."
    )
    parser.add_argument("--leaf-hash", help="Leaf hash as 64 hex characters.")
    parser.add_argument(
        "--leaf-index",
        type=int,
        help="Zero-based leaf index. Used to infer sibling side when proof steps do not specify it.",
    )
    parser.add_argument(
        "--sibling",
        action="append",
        default=[],
        help="Sibling hash for one Merkle level. Repeat in bottom-up order.",
    )
    parser.add_argument(
        "--proof-file",
        help="Optional JSON file that provides leaf_hash, leaf_index, siblings, or proof steps.",
    )
    parser.add_argument(
        "--root-hash",
        help="Expected root hash as 64 hex characters. Optional if --external-ref is provided.",
    )
    parser.add_argument(
        "--external-ref",
        help="Batch external_ref as 64 hex characters. If supplied, the script fetches the batch row from RPC.",
    )
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL, help="Antelope read RPC URL.")
    parser.add_argument(
        "--verification-account",
        default=DEFAULT_VERIFICATION_ACCOUNT,
        help="Account that hosts the verif tables.",
    )
    parser.add_argument(
        "--manifest-hash",
        help="Optional expected manifest_hash from the proof package.",
    )
    parser.add_argument(
        "--leaf-count",
        type=int,
        help="Optional expected leaf_count from the proof package.",
    )
    return parser.parse_args()


def load_json_file(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_step_list(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise ValueError("proof steps must be a list")
    steps: list[dict[str, str]] = []
    for index, item in enumerate(payload):
        if isinstance(item, str):
            steps.append({"hash": ensure_hex_256(item, f"sibling[{index}]"), "side": "auto"})
            continue
        if not isinstance(item, dict):
            raise ValueError(f"proof step {index} must be a string or object")
        hash_value = ensure_hex_256(str(item.get("hash", "")), f"proof[{index}].hash")
        side = str(item.get("side", "auto")).lower()
        if side not in ("left", "right", "auto"):
            raise ValueError(f"proof[{index}].side must be left, right, or auto")
        steps.append({"hash": hash_value, "side": side})
    return steps


def load_proof(args: argparse.Namespace) -> dict[str, Any]:
    proof: dict[str, Any] = {
        "leaf_hash": args.leaf_hash,
        "leaf_index": args.leaf_index,
        "steps": [{"hash": sibling, "side": "auto"} for sibling in args.sibling],
        "root_hash": args.root_hash,
        "external_ref": args.external_ref,
        "manifest_hash": args.manifest_hash,
        "leaf_count": args.leaf_count,
    }

    if args.proof_file:
        file_payload = load_json_file(args.proof_file)
        if not isinstance(file_payload, dict):
            raise ValueError("--proof-file must contain a JSON object")
        proof.update(
            {
                "leaf_hash": file_payload.get("leaf_hash", proof["leaf_hash"]),
                "leaf_index": file_payload.get("leaf_index", proof["leaf_index"]),
                "root_hash": file_payload.get("root_hash", proof["root_hash"]),
                "external_ref": file_payload.get("external_ref", proof["external_ref"]),
                "manifest_hash": file_payload.get("manifest_hash", proof["manifest_hash"]),
                "leaf_count": file_payload.get("leaf_count", proof["leaf_count"]),
            }
        )
        if "proof" in file_payload:
            proof["steps"] = parse_step_list(file_payload["proof"])
        elif "siblings" in file_payload:
            proof["steps"] = parse_step_list(file_payload["siblings"])

    if not proof["leaf_hash"]:
        raise ValueError("leaf_hash is required")
    proof["leaf_hash"] = ensure_hex_256(str(proof["leaf_hash"]), "leaf_hash")

    if proof["leaf_index"] is not None and int(proof["leaf_index"]) < 0:
        raise ValueError("leaf_index must be non-negative")
    if not proof["steps"]:
        raise ValueError("at least one proof step is required")

    normalized_steps = []
    for index, step in enumerate(proof["steps"]):
        normalized_steps.append(
            {
                "hash": ensure_hex_256(str(step["hash"]), f"proof[{index}].hash"),
                "side": str(step.get("side", "auto")).lower(),
            }
        )
    proof["steps"] = normalized_steps

    if proof["root_hash"]:
        proof["root_hash"] = ensure_hex_256(str(proof["root_hash"]), "root_hash")
    if proof["external_ref"]:
        proof["external_ref"] = ensure_hex_256(str(proof["external_ref"]), "external_ref")
    if proof["manifest_hash"]:
        proof["manifest_hash"] = ensure_hex_256(str(proof["manifest_hash"]), "manifest_hash")
    return proof


def sha256_concat(left_hex: str, right_hex: str) -> str:
    return hashlib.sha256(bytes.fromhex(left_hex) + bytes.fromhex(right_hex)).hexdigest()


def compute_root(leaf_hash: str, steps: list[dict[str, str]], leaf_index: int | None) -> dict[str, Any]:
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

        if side == "left":
            parent = sha256_concat(sibling, current)
        elif side == "right":
            parent = sha256_concat(current, sibling)
        else:
            raise ValueError(f"proof step {level} has unsupported side {side}")

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


def get_batch_by_external_ref(rpc_url: str, verification_account: str, external_ref: str) -> dict[str, Any]:
    result_rows = get_table_rows(
        rpc_url,
        verification_account,
        verification_account,
        "batches",
    )
    matches = [
        row
        for row in result_rows
        if str(row.get("external_ref", "")).lower() == external_ref
    ]
    if not matches:
        raise LookupError(f"no batch row found for external_ref {external_ref}")
    if len(matches) > 1:
        raise LookupError(f"multiple batch rows found for external_ref {external_ref}")
    return matches[0]


def main() -> int:
    try:
        args = parse_args()
        proof = load_proof(args)
        computed = compute_root(proof["leaf_hash"], proof["steps"], proof.get("leaf_index"))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    batch_row = None
    expected_root = proof.get("root_hash")
    if proof.get("external_ref"):
        try:
            batch_row = get_batch_by_external_ref(
                args.rpc_url, args.verification_account, proof["external_ref"]
            )
            expected_root = str(batch_row.get("root_hash", "")).lower()
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            return 1

    checks = {
        "computed_root": True,
        "root_matches_expected": expected_root is None
        or computed["computed_root"] == expected_root,
    }
    if batch_row is not None:
        checks["batch_row_found"] = True
        if proof.get("manifest_hash") is not None:
            checks["manifest_hash"] = (
                str(batch_row.get("manifest_hash", "")).lower() == proof["manifest_hash"]
            )
        if proof.get("leaf_count") is not None:
            checks["leaf_count"] = int(batch_row.get("leaf_count", 0)) == int(proof["leaf_count"])

    ok = all(checks.values())
    result = {
        "ok": ok,
        "rpc_url": args.rpc_url,
        "verification_account": args.verification_account,
        "expected": {
            "leaf_hash": proof["leaf_hash"],
            "leaf_index": proof.get("leaf_index"),
            "root_hash": expected_root,
            "external_ref": proof.get("external_ref"),
            "manifest_hash": proof.get("manifest_hash"),
            "leaf_count": proof.get("leaf_count"),
        },
        "checks": checks,
        "computed": computed,
        "batch_row": batch_row,
    }
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
