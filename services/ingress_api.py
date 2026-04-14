from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List


def sha256_hex_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_hex_text(payload: str) -> str:
    return sha256_hex_bytes(payload.encode("utf-8"))


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonicalize_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def bytes_from_hex(hex_value: str) -> bytes:
    return bytes.fromhex(hex_value)


def merkle_root_hex(leaf_hashes: List[str]) -> str:
    if not leaf_hashes:
        raise ValueError("leaf_hashes must not be empty")

    level = [bytes_from_hex(item) for item in leaf_hashes]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        next_level: List[bytes] = []
        for index in range(0, len(level), 2):
            next_level.append(hashlib.sha256(level[index] + level[index + 1]).digest())
        level = next_level

    return level[0].hex()


def require_bool(mapping: Dict[str, Any], field_name: str) -> bool:
    value = mapping.get(field_name)
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")
    return value


def require_int(mapping: Dict[str, Any], field_name: str) -> int:
    value = mapping.get(field_name)
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be integer")
    return value


def require_string(mapping: Dict[str, Any], field_name: str) -> str:
    value = mapping.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty string")
    return value


def require_mapping(mapping: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    value = mapping.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def require_list(mapping: Dict[str, Any], field_name: str) -> List[Any]:
    value = mapping.get(field_name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must be a non-empty array")
    return value


def validate_schema_context(schema: Dict[str, Any]) -> str:
    if not require_bool(schema, "active"):
        raise ValueError("schema is inactive")
    require_int(schema, "id")
    require_string(schema, "version")
    profile = require_string(schema, "canonicalization_profile")
    if profile != "json-sorted-v1":
        raise ValueError("unsupported canonicalization_profile")
    return profile


def validate_policy_context(policy: Dict[str, Any], mode: str) -> None:
    if not require_bool(policy, "active"):
        raise ValueError("policy is inactive")

    allow_single = require_bool(policy, "allow_single")
    allow_batch = require_bool(policy, "allow_batch")

    if mode == "single" and not allow_single:
        raise ValueError("policy does not allow single submissions")
    if mode == "batch" and not allow_batch:
        raise ValueError("policy does not allow batch submissions")

    require_bool(policy, "require_kyc")
    require_int(policy, "min_kyc_level")


def validate_kyc_context(policy: Dict[str, Any], body: Dict[str, Any]) -> None:
    if not policy["require_kyc"]:
        return

    kyc = require_mapping(body, "kyc")
    if not require_bool(kyc, "active"):
        raise ValueError("kyc is inactive")
    if require_int(kyc, "level") < policy["min_kyc_level"]:
        raise ValueError("kyc level is below policy minimum")

    expires_at = parse_utc_timestamp(require_string(kyc, "expires_at"))
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("kyc is expired")


def build_trace_metadata(submitter: str, external_ref_hash: str, content_hash: str, mode: str) -> Dict[str, str]:
    trace_id = str(uuid.uuid4())
    request_id = sha256_hex_text(f"{submitter}:{external_ref_hash}:{content_hash}:{mode}")
    return {
        "trace_id": trace_id,
        "request_id": request_id,
        "received_at": iso_now(),
    }


def build_single_response(body: Dict[str, Any], contract_account: str) -> Dict[str, Any]:
    submitter = require_string(body, "submitter")
    external_ref = require_string(body, "external_ref")
    schema = require_mapping(body, "schema")
    policy = require_mapping(body, "policy")

    canonicalization_profile = validate_schema_context(schema)
    validate_policy_context(policy, "single")
    validate_kyc_context(policy, body)

    payload = body.get("payload")
    canonical_form = canonicalize_json(payload)
    object_hash = sha256_hex_text(canonical_form)
    external_ref_hash = sha256_hex_text(external_ref)
    metadata = build_trace_metadata(submitter, external_ref_hash, object_hash, "single")

    return {
        **metadata,
        "mode": "single",
        "canonicalization_profile": canonicalization_profile,
        "canonical_form": canonical_form,
        "object_hash": object_hash,
        "external_ref_hash": external_ref_hash,
        "prepared_action": {
            "contract": contract_account,
            "action": "submit",
            "data": {
                "submitter": submitter,
                "schema_id": schema["id"],
                "policy_id": policy["id"],
                "object_hash": object_hash,
                "external_ref": external_ref_hash,
            },
        },
    }


def build_batch_manifest(
    submitter: str,
    schema: Dict[str, Any],
    policy: Dict[str, Any],
    external_ref_hash: str,
    leafs: List[Dict[str, Any]],
    root_hash: str,
) -> Dict[str, Any]:
    return {
        "manifest_version": "batch-manifest-v1",
        "submitter": submitter,
        "schema_id": schema["id"],
        "schema_version": schema["version"],
        "policy_id": policy["id"],
        "external_ref_hash": external_ref_hash,
        "leaf_count": len(leafs),
        "root_hash": root_hash,
        "leafs": leafs,
    }


def build_batch_response(body: Dict[str, Any], contract_account: str) -> Dict[str, Any]:
    submitter = require_string(body, "submitter")
    external_ref = require_string(body, "external_ref")
    schema = require_mapping(body, "schema")
    policy = require_mapping(body, "policy")

    canonicalization_profile = validate_schema_context(schema)
    validate_policy_context(policy, "batch")
    validate_kyc_context(policy, body)

    items = require_list(body, "items")
    leafs: List[Dict[str, Any]] = []
    leaf_hashes: List[str] = []

    for index, item in enumerate(items):
        payload = item.get("payload") if isinstance(item, dict) else item
        canonical_form = canonicalize_json(payload)
        leaf_hash = sha256_hex_text(canonical_form)
        leaf_ref = item.get("external_leaf_ref") if isinstance(item, dict) else None
        leaf_entry = {
            "index": index,
            "leaf_hash": leaf_hash,
            "canonical_form": canonical_form,
        }
        if isinstance(leaf_ref, str) and leaf_ref:
            leaf_entry["external_leaf_ref"] = leaf_ref
        leafs.append(leaf_entry)
        leaf_hashes.append(leaf_hash)

    root_hash = merkle_root_hex(leaf_hashes)
    external_ref_hash = sha256_hex_text(external_ref)
    manifest = build_batch_manifest(submitter, schema, policy, external_ref_hash, leafs, root_hash)
    manifest_canonical_form = canonicalize_json(manifest)
    manifest_hash = sha256_hex_text(manifest_canonical_form)
    metadata = build_trace_metadata(submitter, external_ref_hash, root_hash, "batch")

    return {
        **metadata,
        "mode": "batch",
        "canonicalization_profile": canonicalization_profile,
        "leaf_count": len(leafs),
        "leaf_hashes": leaf_hashes,
        "root_hash": root_hash,
        "external_ref_hash": external_ref_hash,
        "manifest_hash": manifest_hash,
        "manifest": manifest,
        "manifest_canonical_form": manifest_canonical_form,
        "prepared_action": {
            "contract": contract_account,
            "action": "submitroot",
            "data": {
                "submitter": submitter,
                "schema_id": schema["id"],
                "policy_id": policy["id"],
                "root_hash": root_hash,
                "leaf_count": len(leafs),
                "external_ref": external_ref_hash,
            },
        },
    }


class IngressApiHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryIngress/0.1"

    def do_GET(self) -> None:
        if self.path != "/healthz":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        self.write_json(HTTPStatus.OK, {"status": "ok", "service": "ingress-api"})

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8")) if body else {}

            if self.path == "/v1/single/prepare":
                response = build_single_response(payload, self.server.contract_account)
            elif self.path == "/v1/batch/prepare":
                response = build_batch_response(payload, self.server.contract_account)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return

            self.write_json(HTTPStatus.OK, response)
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except json.JSONDecodeError:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": "request body must be valid JSON"})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def write_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class IngressHttpServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], contract_account: str):
        super().__init__(server_address, handler)
        self.contract_account = contract_account


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeNotary ingestion API scaffold.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--contract-account", default="verification")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = IngressHttpServer((args.host, args.port), IngressApiHandler, args.contract_account)
    print(f"Ingress API listening on http://{args.host}:{args.port} for contract '{args.contract_account}'")
    server.serve_forever()


if __name__ == "__main__":
    main()
