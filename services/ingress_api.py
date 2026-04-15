from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

from openapi_docs import swagger_ui_html

MAX_REQUEST_BODY_BYTES = 1024 * 1024
MAX_EXTERNAL_REF_LENGTH = 256
MAX_EXTERNAL_LEAF_REF_LENGTH = 128
MAX_BATCH_ITEMS = 2048
MAX_CANONICAL_FORM_BYTES = 256 * 1024
MAX_BATCH_MANIFEST_BYTES = 1024 * 1024

ACCOUNT_NAME_RE = re.compile(r"^[a-z1-5.]{1,12}$")


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


def require_optional_bool(mapping: Dict[str, Any], field_name: str, default: bool = False) -> bool:
    value = mapping.get(field_name, default)
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")
    return value


def validate_account_name(value: str, field_name: str) -> str:
    if not ACCOUNT_NAME_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a valid Antelope account name")
    return value


def validate_limited_text(value: str, field_name: str, max_length: int) -> str:
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long")
    for character in value:
        code = ord(character)
        if code < 32 or code == 127:
            raise ValueError(f"{field_name} must not contain control characters")
    return value


def validate_json_payload(payload: Any, field_name: str) -> None:
    if payload is None:
        raise ValueError(f"{field_name} must not be null")


def validate_canonical_size(canonical_form: str, field_name: str, limit_bytes: int) -> None:
    encoded = canonical_form.encode("utf-8")
    if len(encoded) > limit_bytes:
        raise ValueError(f"{field_name} exceeds maximum allowed size")


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


def request_watcher_json(
    watcher_url: str,
    payload: Dict[str, Any],
    auth_token: str = "",
) -> tuple[int, Dict[str, Any]]:
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["X-DeNotary-Token"] = auth_token

    request = urllib.request.Request(
        f"{watcher_url.rstrip('/')}/v1/watch/register",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def require_optional_string(mapping: Dict[str, Any], field_name: str) -> Optional[str]:
    value = mapping.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty string when provided")
    return value


def resolve_watcher_handoff(body: Dict[str, Any], server: "IngressHttpServer") -> Optional[Dict[str, str]]:
    watcher = body.get("watcher")
    if watcher is None:
        return None
    if not isinstance(watcher, dict):
        raise ValueError("watcher must be an object when provided")

    register = require_optional_bool(watcher, "register", True)
    if not register:
        return None

    watcher_url = require_optional_string(watcher, "url") or server.watcher_url
    if not watcher_url:
        raise ValueError("watcher.url must be provided when watcher handoff is enabled")

    auth_token = require_optional_string(watcher, "auth_token") or server.watcher_auth_token
    rpc_url = require_optional_string(watcher, "rpc_url") or server.watcher_rpc_url

    return {
        "url": watcher_url,
        "auth_token": auth_token,
        "rpc_url": rpc_url,
    }


def build_watcher_register_payload(response: Dict[str, Any], watcher_rpc_url: str) -> Dict[str, Any]:
    anchor: Dict[str, Any]
    if response["mode"] == "single":
        anchor = {
            "object_hash": response["object_hash"],
            "external_ref_hash": response["external_ref_hash"],
        }
    else:
        anchor = {
            "root_hash": response["root_hash"],
            "manifest_hash": response["manifest_hash"],
            "external_ref_hash": response["external_ref_hash"],
            "leaf_count": response["leaf_count"],
        }

    payload = {
        "request_id": response["request_id"],
        "trace_id": response["trace_id"],
        "mode": response["mode"],
        "submitter": response["prepared_action"]["data"]["submitter"],
        "contract": response["prepared_action"]["contract"],
        "anchor": anchor,
    }
    if watcher_rpc_url:
        payload["rpc_url"] = watcher_rpc_url
    return payload


def attach_watcher_handoff(response: Dict[str, Any], watcher_config: Dict[str, str]) -> None:
    register_payload = build_watcher_register_payload(response, watcher_config["rpc_url"])
    handoff: Dict[str, Any] = {
        "attempted": True,
        "ok": False,
        "url": watcher_config["url"],
        "register_payload": register_payload,
    }
    try:
        status_code, watcher_response = request_watcher_json(
            watcher_config["url"],
            register_payload,
            watcher_config["auth_token"],
        )
        handoff["status_code"] = status_code
        handoff["response"] = watcher_response
        handoff["ok"] = 200 <= status_code < 300
    except urllib.error.URLError as exc:
        handoff["error"] = str(exc)

    response["watcher_handoff"] = handoff


def build_openapi_spec(contract_account: str) -> Dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "DeNotary Ingress API",
            "version": "1.0.0",
            "description": (
                "Deterministic preparation API for single and batch anchoring requests, with optional "
                "handoff into Finality Watcher registration."
            ),
        },
        "servers": [
            {"url": "http://127.0.0.1:8080", "description": "Local default"},
        ],
        "paths": {
            "/healthz": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "Service health",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/v1/single/prepare": {
                "post": {
                    "summary": "Prepare a single anchoring request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/SinglePrepareRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Prepared single anchoring payload",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SinglePrepareResponse"}
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "413": {
                            "description": "Body too large",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/v1/batch/prepare": {
                "post": {
                    "summary": "Prepare a batch anchoring request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/BatchPrepareRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Prepared batch anchoring payload",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/BatchPrepareResponse"}
                                }
                            },
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "413": {
                            "description": "Body too large",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/openapi.json": {
                "get": {
                    "summary": "OpenAPI specification",
                    "responses": {"200": {"description": "OpenAPI JSON"}},
                }
            },
            "/docs": {
                "get": {
                    "summary": "Swagger UI",
                    "responses": {"200": {"description": "Interactive API documentation"}},
                }
            },
        },
        "components": {
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "ok"},
                        "service": {"type": "string", "example": "ingress-api"},
                    },
                    "required": ["status", "service"],
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {"error": {"type": "string"}},
                    "required": ["error"],
                },
                "SchemaContext": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "version": {"type": "string"},
                        "active": {"type": "boolean"},
                        "canonicalization_profile": {"type": "string", "example": "json-sorted-v1"},
                    },
                    "required": ["id", "version", "active", "canonicalization_profile"],
                },
                "PolicyContext": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "active": {"type": "boolean"},
                        "allow_single": {"type": "boolean"},
                        "allow_batch": {"type": "boolean"},
                        "require_kyc": {"type": "boolean"},
                        "min_kyc_level": {"type": "integer"},
                    },
                    "required": ["id", "active", "allow_single", "allow_batch", "require_kyc", "min_kyc_level"],
                },
                "KycContext": {
                    "type": "object",
                    "properties": {
                        "active": {"type": "boolean"},
                        "level": {"type": "integer"},
                        "expires_at": {"type": "string", "format": "date-time"},
                    },
                    "required": ["active", "level", "expires_at"],
                },
                "WatcherOptions": {
                    "type": "object",
                    "properties": {
                        "register": {"type": "boolean", "default": True},
                        "url": {"type": "string", "format": "uri"},
                        "auth_token": {"type": "string"},
                        "rpc_url": {"type": "string", "format": "uri"},
                    },
                },
                "PreparedAction": {
                    "type": "object",
                    "properties": {
                        "contract": {"type": "string", "example": contract_account},
                        "action": {"type": "string"},
                        "data": {"type": "object", "additionalProperties": True},
                    },
                    "required": ["contract", "action", "data"],
                },
                "WatcherHandoff": {
                    "type": "object",
                    "properties": {
                        "attempted": {"type": "boolean"},
                        "ok": {"type": "boolean"},
                        "url": {"type": "string", "format": "uri"},
                        "status_code": {"type": "integer"},
                        "register_payload": {"type": "object", "additionalProperties": True},
                        "response": {"type": "object", "additionalProperties": True},
                        "error": {"type": "string"},
                    },
                    "required": ["attempted", "ok", "url", "register_payload"],
                },
                "SinglePrepareRequest": {
                    "type": "object",
                    "properties": {
                        "submitter": {"type": "string"},
                        "external_ref": {"type": "string"},
                        "schema": {"$ref": "#/components/schemas/SchemaContext"},
                        "policy": {"$ref": "#/components/schemas/PolicyContext"},
                        "kyc": {"$ref": "#/components/schemas/KycContext"},
                        "payload": {"type": "object", "additionalProperties": True},
                        "include_debug_material": {"type": "boolean"},
                        "watcher": {"$ref": "#/components/schemas/WatcherOptions"},
                    },
                    "required": ["submitter", "external_ref", "schema", "policy", "payload"],
                },
                "SinglePrepareResponse": {
                    "type": "object",
                    "properties": {
                        "trace_id": {"type": "string"},
                        "request_id": {"type": "string"},
                        "received_at": {"type": "string", "format": "date-time"},
                        "mode": {"type": "string", "enum": ["single"]},
                        "canonicalization_profile": {"type": "string"},
                        "object_hash": {"type": "string"},
                        "external_ref_hash": {"type": "string"},
                        "canonical_form": {"type": "string"},
                        "prepared_action": {"$ref": "#/components/schemas/PreparedAction"},
                        "watcher_handoff": {"$ref": "#/components/schemas/WatcherHandoff"},
                    },
                    "required": [
                        "trace_id",
                        "request_id",
                        "received_at",
                        "mode",
                        "canonicalization_profile",
                        "object_hash",
                        "external_ref_hash",
                        "prepared_action",
                    ],
                },
                "BatchItem": {
                    "type": "object",
                    "properties": {
                        "external_leaf_ref": {"type": "string"},
                        "payload": {"type": "object", "additionalProperties": True},
                    },
                    "required": ["payload"],
                },
                "BatchPrepareRequest": {
                    "type": "object",
                    "properties": {
                        "submitter": {"type": "string"},
                        "external_ref": {"type": "string"},
                        "schema": {"$ref": "#/components/schemas/SchemaContext"},
                        "policy": {"$ref": "#/components/schemas/PolicyContext"},
                        "kyc": {"$ref": "#/components/schemas/KycContext"},
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/BatchItem"},
                        },
                        "include_debug_material": {"type": "boolean"},
                        "watcher": {"$ref": "#/components/schemas/WatcherOptions"},
                    },
                    "required": ["submitter", "external_ref", "schema", "policy", "items"],
                },
                "BatchPrepareResponse": {
                    "type": "object",
                    "properties": {
                        "trace_id": {"type": "string"},
                        "request_id": {"type": "string"},
                        "received_at": {"type": "string", "format": "date-time"},
                        "mode": {"type": "string", "enum": ["batch"]},
                        "canonicalization_profile": {"type": "string"},
                        "leaf_count": {"type": "integer"},
                        "root_hash": {"type": "string"},
                        "external_ref_hash": {"type": "string"},
                        "manifest_hash": {"type": "string"},
                        "leaf_hashes": {"type": "array", "items": {"type": "string"}},
                        "manifest": {"type": "object", "additionalProperties": True},
                        "manifest_canonical_form": {"type": "string"},
                        "prepared_action": {"$ref": "#/components/schemas/PreparedAction"},
                        "watcher_handoff": {"$ref": "#/components/schemas/WatcherHandoff"},
                    },
                    "required": [
                        "trace_id",
                        "request_id",
                        "received_at",
                        "mode",
                        "canonicalization_profile",
                        "leaf_count",
                        "root_hash",
                        "external_ref_hash",
                        "manifest_hash",
                        "prepared_action",
                    ],
                },
            }
        },
    }


def build_single_response(body: Dict[str, Any], contract_account: str) -> Dict[str, Any]:
    submitter = validate_account_name(require_string(body, "submitter"), "submitter")
    external_ref = validate_limited_text(
        require_string(body, "external_ref"),
        "external_ref",
        MAX_EXTERNAL_REF_LENGTH,
    )
    schema = require_mapping(body, "schema")
    policy = require_mapping(body, "policy")
    include_debug_material = require_optional_bool(body, "include_debug_material")

    canonicalization_profile = validate_schema_context(schema)
    validate_policy_context(policy, "single")
    validate_kyc_context(policy, body)

    payload = body.get("payload")
    validate_json_payload(payload, "payload")
    canonical_form = canonicalize_json(payload)
    validate_canonical_size(canonical_form, "canonical_form", MAX_CANONICAL_FORM_BYTES)
    object_hash = sha256_hex_text(canonical_form)
    external_ref_hash = sha256_hex_text(external_ref)
    metadata = build_trace_metadata(submitter, external_ref_hash, object_hash, "single")

    response = {
        **metadata,
        "mode": "single",
        "canonicalization_profile": canonicalization_profile,
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
    if include_debug_material:
        response["canonical_form"] = canonical_form
    return response


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
    submitter = validate_account_name(require_string(body, "submitter"), "submitter")
    external_ref = validate_limited_text(
        require_string(body, "external_ref"),
        "external_ref",
        MAX_EXTERNAL_REF_LENGTH,
    )
    schema = require_mapping(body, "schema")
    policy = require_mapping(body, "policy")
    include_debug_material = require_optional_bool(body, "include_debug_material")

    canonicalization_profile = validate_schema_context(schema)
    validate_policy_context(policy, "batch")
    validate_kyc_context(policy, body)

    items = require_list(body, "items")
    if len(items) > MAX_BATCH_ITEMS:
        raise ValueError("items exceeds maximum batch size")
    manifest_leafs: List[Dict[str, Any]] = []
    response_leafs: List[Dict[str, Any]] = []
    leaf_hashes: List[str] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError("each batch item must be an object")
        payload = item.get("payload") if isinstance(item, dict) else item
        validate_json_payload(payload, f"items[{index}].payload")
        canonical_form = canonicalize_json(payload)
        validate_canonical_size(canonical_form, f"items[{index}].canonical_form", MAX_CANONICAL_FORM_BYTES)
        leaf_hash = sha256_hex_text(canonical_form)
        leaf_ref = item.get("external_leaf_ref") if isinstance(item, dict) else None
        manifest_leaf = {
            "index": index,
            "leaf_hash": leaf_hash,
            "canonical_form": canonical_form,
        }
        response_leaf = {
            "index": index,
            "leaf_hash": leaf_hash,
        }
        if isinstance(leaf_ref, str) and leaf_ref:
            validate_limited_text(leaf_ref, "external_leaf_ref", MAX_EXTERNAL_LEAF_REF_LENGTH)
            manifest_leaf["external_leaf_ref"] = leaf_ref
            response_leaf["external_leaf_ref"] = leaf_ref
        if include_debug_material:
            response_leaf["canonical_form"] = canonical_form
        manifest_leafs.append(manifest_leaf)
        response_leafs.append(response_leaf)
        leaf_hashes.append(leaf_hash)

    root_hash = merkle_root_hex(leaf_hashes)
    external_ref_hash = sha256_hex_text(external_ref)
    manifest = build_batch_manifest(submitter, schema, policy, external_ref_hash, manifest_leafs, root_hash)
    manifest_canonical_form = canonicalize_json(manifest)
    validate_canonical_size(manifest_canonical_form, "manifest_canonical_form", MAX_BATCH_MANIFEST_BYTES)
    manifest_hash = sha256_hex_text(manifest_canonical_form)
    metadata = build_trace_metadata(submitter, external_ref_hash, root_hash, "batch")

    response = {
        **metadata,
        "mode": "batch",
        "canonicalization_profile": canonicalization_profile,
        "leaf_count": len(manifest_leafs),
        "root_hash": root_hash,
        "external_ref_hash": external_ref_hash,
        "manifest_hash": manifest_hash,
        "prepared_action": {
            "contract": contract_account,
            "action": "submitroot",
            "data": {
                "submitter": submitter,
                "schema_id": schema["id"],
                "policy_id": policy["id"],
                "root_hash": root_hash,
                "leaf_count": len(manifest_leafs),
                "external_ref": external_ref_hash,
            },
        },
    }
    if include_debug_material:
        response["leaf_hashes"] = leaf_hashes
        response["manifest"] = {
            **manifest,
            "leafs": response_leafs,
        }
        response["manifest_canonical_form"] = manifest_canonical_form
    return response


class IngressApiHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryIngress/0.1"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.write_json(HTTPStatus.OK, {"status": "ok", "service": "ingress-api"})
            return

        if self.path == "/openapi.json":
            self.write_json(HTTPStatus.OK, build_openapi_spec(self.server.contract_account))
            return

        if self.path == "/docs":
            self.write_html(HTTPStatus.OK, swagger_ui_html("DeNotary Ingress API", "/openapi.json"))
            return

        if self.path != "/healthz":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0 or content_length > MAX_REQUEST_BODY_BYTES:
                self.write_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request body is too large"})
                return
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8")) if body else {}
            watcher_config = resolve_watcher_handoff(payload, self.server)

            if self.path == "/v1/single/prepare":
                response = build_single_response(payload, self.server.contract_account)
            elif self.path == "/v1/batch/prepare":
                response = build_batch_response(payload, self.server.contract_account)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return

            if watcher_config is not None:
                attach_watcher_handoff(response, watcher_config)

            self.write_json(HTTPStatus.OK, response)
        except json.JSONDecodeError:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": "request body must be valid JSON"})
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def write_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def write_html(self, status: HTTPStatus, payload: str) -> None:
        encoded = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class IngressHttpServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        contract_account: str,
        watcher_url: str = "",
        watcher_auth_token: str = "",
        watcher_rpc_url: str = "",
    ):
        super().__init__(server_address, handler)
        self.contract_account = contract_account
        self.watcher_url = watcher_url
        self.watcher_auth_token = watcher_auth_token
        self.watcher_rpc_url = watcher_rpc_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeNotary ingestion API scaffold.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--contract-account", default="verification")
    parser.add_argument("--watcher-url", default="")
    parser.add_argument("--watcher-auth-token", default="")
    parser.add_argument("--watcher-rpc-url", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = IngressHttpServer(
        (args.host, args.port),
        IngressApiHandler,
        args.contract_account,
        args.watcher_url,
        args.watcher_auth_token,
        args.watcher_rpc_url,
    )
    print(f"Ingress API listening on http://{args.host}:{args.port} for contract '{args.contract_account}'")
    server.serve_forever()


if __name__ == "__main__":
    main()
