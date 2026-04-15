from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, Optional

from finality_store import FinalityStore, build_finality_store
from finality_store_base import FinalityStoreBase

MAX_REQUEST_BODY_BYTES = 256 * 1024
HEX_64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
TRACE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
ACCOUNT_NAME_RE = re.compile(r"^[a-z1-5.]{1,12}$")


class TransactionLookupPending(Exception):
    pass


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require_int(mapping: Dict[str, Any], field_name: str) -> int:
    value = mapping.get(field_name)
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be integer")
    return value


def require_optional_positive_int(mapping: Dict[str, Any], field_name: str) -> Optional[int]:
    value = mapping.get(field_name)
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be positive integer when provided")
    return value


def require_string(mapping: Dict[str, Any], field_name: str) -> str:
    value = mapping.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty string")
    return value


def require_mapping(mapping: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    value = mapping.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be object")
    return value


def require_optional_reason(mapping: Dict[str, Any], field_name: str) -> Optional[str]:
    value = mapping.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty string when provided")
    if len(value) > 256:
        raise ValueError(f"{field_name} is too long")
    return value


def require_hex_64(mapping: Dict[str, Any], field_name: str) -> str:
    value = require_string(mapping, field_name)
    if not HEX_64_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a 64-character hex string")
    return value.lower()


def require_trace_id(mapping: Dict[str, Any], field_name: str) -> str:
    value = require_string(mapping, field_name)
    if not TRACE_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} contains unsupported characters")
    return value


def require_account_name(mapping: Dict[str, Any], field_name: str) -> str:
    value = require_string(mapping, field_name)
    if not ACCOUNT_NAME_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a valid Antelope account name")
    return value


def normalize_rpc_urls(value: Any, fallback: str) -> list[str]:
    if isinstance(value, list):
        raw_values = value
    elif isinstance(value, str):
        raw_values = value.split(",")
    elif value is None:
        raw_values = fallback.split(",")
    else:
        raise ValueError("rpc_url or rpc_urls must be string or list of strings")

    normalized: list[str] = []
    for item in raw_values:
        if not isinstance(item, str):
            raise ValueError("rpc_urls entries must be strings")
        candidate = item.strip()
        if candidate:
            normalized.append(candidate)

    if not normalized:
        raise ValueError("at least one rpc url must be configured")
    return normalized


def read_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    if content_length < 0 or content_length > MAX_REQUEST_BODY_BYTES:
        raise ValueError("request body is too large")
    body = handler.rfile.read(content_length)
    try:
        return json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError as exc:
        raise ValueError("request body must be valid JSON") from exc


def get_request_auth_token(handler: BaseHTTPRequestHandler) -> str:
    direct = handler.headers.get("X-DeNotary-Token")
    if direct:
        return direct

    authorization = handler.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return ""


def require_mutation_auth(handler: BaseHTTPRequestHandler) -> None:
    configured_token = getattr(handler.server, "auth_token", "") or ""
    if not configured_token:
        raise PermissionError("watcher mutation endpoint requires valid auth token")

    presented_token = get_request_auth_token(handler)
    if not presented_token or not hmac.compare_digest(presented_token, configured_token):
        raise PermissionError("watcher mutation endpoint requires valid auth token")


def rpc_post_json(url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    request = urllib.request.Request(
        f"{url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except OSError as exc:
        raise urllib.error.URLError(str(exc)) from exc


def rpc_get_json(url: str, path: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    query_string = ""
    if query:
        query_string = "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(
        f"{url.rstrip('/')}{path}{query_string}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except OSError as exc:
        raise urllib.error.URLError(str(exc)) from exc


def fetch_chain_info(rpc_url: str) -> Dict[str, Any]:
    return rpc_post_json(rpc_url, "/v1/chain/get_info", {})


def fetch_chain_info_any(rpc_urls: list[str]) -> tuple[str, Dict[str, Any]]:
    last_error: Optional[Exception] = None
    for rpc_url in rpc_urls:
        try:
            return rpc_url, fetch_chain_info(rpc_url)
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise urllib.error.URLError(str(last_error))
    raise urllib.error.URLError("no rpc urls configured")


def sha256_hex_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def derive_request_id(submitter: str, external_ref_hash: str, content_hash: str, mode: str) -> str:
    return sha256_hex_text(f"{submitter}:{external_ref_hash}:{content_hash}:{mode}")


def extract_request_content_hash(mode: str, anchor: Dict[str, Any]) -> str:
    if mode == "single":
        object_hash = anchor.get("object_hash")
        if not isinstance(object_hash, str) or not HEX_64_RE.fullmatch(object_hash):
            raise ValueError("single mode requires anchor.object_hash")
        return object_hash.lower()

    root_hash = anchor.get("root_hash")
    if not isinstance(root_hash, str) or not HEX_64_RE.fullmatch(root_hash):
        raise ValueError("batch mode requires anchor.root_hash")
    return root_hash.lower()


def validate_anchor_metadata(anchor: Dict[str, Any], mode: str) -> Dict[str, Any]:
    external_ref_hash = anchor.get("external_ref_hash")
    if external_ref_hash is not None:
        anchor["external_ref_hash"] = require_hex_64(anchor, "external_ref_hash")

    object_hash = anchor.get("object_hash")
    if object_hash is not None:
        if mode != "single":
            raise ValueError("object_hash is only valid for single mode")
        anchor["object_hash"] = require_hex_64(anchor, "object_hash")

    root_hash = anchor.get("root_hash")
    if root_hash is not None:
        if mode != "batch":
            raise ValueError("root_hash is only valid for batch mode")
        anchor["root_hash"] = require_hex_64(anchor, "root_hash")

    manifest_hash = anchor.get("manifest_hash")
    if manifest_hash is not None:
        if mode != "batch":
            raise ValueError("manifest_hash is only valid for batch mode")
        anchor["manifest_hash"] = require_hex_64(anchor, "manifest_hash")

    leaf_count = anchor.get("leaf_count")
    if leaf_count is not None:
        if mode != "batch":
            raise ValueError("leaf_count is only valid for batch mode")
        if not isinstance(leaf_count, int) or leaf_count <= 0:
            raise ValueError("leaf_count must be positive integer when provided")

    if "commitment_id" in anchor:
        commitment_id = require_optional_positive_int(anchor, "commitment_id")
        if mode != "single":
            raise ValueError("commitment_id is only valid for single mode")
        if commitment_id is not None:
            anchor["commitment_id"] = commitment_id

    if "batch_id" in anchor:
        batch_id = require_optional_positive_int(anchor, "batch_id")
        if mode != "batch":
            raise ValueError("batch_id is only valid for batch mode")
        if batch_id is not None:
            anchor["batch_id"] = batch_id

    return anchor


def normalize_watch_request(body: Dict[str, Any], default_rpc_url: str) -> Dict[str, Any]:
    request_id = require_hex_64(body, "request_id")
    trace_id = require_trace_id(body, "trace_id")
    mode = require_string(body, "mode")
    if mode not in {"single", "batch"}:
        raise ValueError("mode must be either 'single' or 'batch'")

    submitter = require_account_name(body, "submitter")
    contract = require_account_name(body, "contract")
    anchor = validate_anchor_metadata(require_mapping(body, "anchor"), mode)
    external_ref_hash = require_hex_64(anchor, "external_ref_hash")
    content_hash = extract_request_content_hash(mode, anchor)
    expected_request_id = derive_request_id(submitter, external_ref_hash, content_hash, mode)
    if request_id != expected_request_id:
        raise ValueError("request_id does not match derived canonical request id")

    tx_id = body.get("tx_id")
    if tx_id is not None:
        if not isinstance(tx_id, str) or not HEX_64_RE.fullmatch(tx_id):
            raise ValueError("tx_id must be a 64-character hex string when provided")
        tx_id = tx_id.lower()

    block_num = body.get("block_num")
    if block_num is not None and (not isinstance(block_num, int) or block_num <= 0):
        raise ValueError("block_num must be integer when provided")
    if tx_id is None and block_num is not None:
        raise ValueError("block_num requires tx_id")

    rpc_urls = normalize_rpc_urls(body.get("rpc_urls", body.get("rpc_url")), default_rpc_url)
    rpc_url = rpc_urls[0]

    status = "included" if tx_id and block_num else "submitted"
    timestamp = iso_now()

    return {
        "request_id": request_id,
        "trace_id": trace_id,
        "mode": mode,
        "submitter": submitter,
        "contract": contract,
        "rpc_url": rpc_url,
        "rpc_urls": rpc_urls,
        "anchor": anchor,
        "tx_id": tx_id,
        "block_num": block_num,
        "status": status,
        "registered_at": timestamp,
        "included_at": timestamp if status == "included" else None,
        "updated_at": timestamp,
        "finalized_at": None,
        "failed_at": None,
        "failure_reason": None,
        "failure_details": None,
        "inclusion_verified": False,
        "inclusion_verified_at": None,
        "inclusion_verification_error": None,
        "verified_action": None,
        "verification_policy": "single-provider",
        "verification_min_success": 1,
        "verification_state": None,
        "provider_disagreement": False,
        "chain_state": {
            "head_block_num": None,
            "last_irreversible_block_num": None,
        },
    }


def extract_transaction_block_num(payload: Dict[str, Any]) -> Optional[int]:
    candidate = payload.get("block_num")
    if isinstance(candidate, int) and candidate > 0:
        return candidate

    traces = payload.get("actions")
    if isinstance(traces, list):
        for action in traces:
            if isinstance(action, dict):
                action_block_num = action.get("block_num")
                if isinstance(action_block_num, int) and action_block_num > 0:
                    return action_block_num
    return None


def extract_action_data(container: Dict[str, Any]) -> Dict[str, Any]:
    data = container.get("data")
    return data if isinstance(data, dict) else {}


def iter_transaction_actions(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    traces = payload.get("actions")
    if isinstance(traces, list):
        for action in traces:
            if not isinstance(action, dict):
                continue
            act = action.get("act")
            if isinstance(act, dict):
                yield {
                    "account": act.get("account"),
                    "name": act.get("name"),
                    "data": extract_action_data(act),
                    "block_num": action.get("block_num"),
                }
                continue

            yield {
                "account": action.get("account"),
                "name": action.get("name"),
                "data": extract_action_data(action),
                "block_num": action.get("block_num"),
            }
        return

    trx = payload.get("trx")
    if not isinstance(trx, dict):
        return
    nested_trx = trx.get("trx")
    if not isinstance(nested_trx, dict):
        return
    actions = nested_trx.get("actions")
    if not isinstance(actions, list):
        return
    for action in actions:
        if not isinstance(action, dict):
            continue
        yield {
            "account": action.get("account"),
            "name": action.get("name"),
            "data": extract_action_data(action),
            "block_num": payload.get("block_num"),
        }


def fetch_transaction_details(rpc_url: str, tx_id: str, block_num: Optional[int]) -> Dict[str, Any]:
    candidates = [
        ("GET", "/v2/history/get_transaction", {"id": tx_id, "block_hint": block_num} if block_num else {"id": tx_id}),
        ("POST", "/v1/history/get_transaction", {"id": tx_id, "block_num_hint": block_num} if block_num else {"id": tx_id}),
    ]
    pending_messages: list[str] = []

    for method, path, payload in candidates:
        try:
            if method == "GET":
                response = rpc_get_json(rpc_url, path, payload)
            else:
                response = rpc_post_json(rpc_url, path, payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            if exc.code in {404, 410}:
                pending_messages.append(body or f"{path} returned HTTP {exc.code}")
                continue
            raise

        if isinstance(response, dict):
            if response.get("executed") is False:
                pending_messages.append("transaction is not yet indexed in history")
                continue
            if response.get("code") in {404, 410}:
                pending_messages.append(str(response.get("message") or f"{path} returned {response['code']}"))
                continue
            if response.get("statusCode") in {404, 410}:
                pending_messages.append(str(response.get("message") or f"{path} returned {response['statusCode']}"))
                continue
        return response

    if pending_messages:
        raise TransactionLookupPending(pending_messages[-1])
    raise TransactionLookupPending("transaction is not yet verifiable")


def coerce_positive_int(value: Any) -> Optional[int]:
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdigit():
        parsed = int(value)
        if parsed > 0:
            return parsed
    return None


def matches_single_action(request_payload: Dict[str, Any], action: Dict[str, Any]) -> bool:
    if action.get("account") != request_payload.get("contract"):
        return False
    if action.get("name") != "submit":
        return False

    data = action.get("data", {})
    anchor = request_payload.get("anchor", {})
    return (
        str(data.get("submitter")) == request_payload.get("submitter")
        and str(data.get("object_hash", "")).lower() == anchor.get("object_hash")
        and str(data.get("external_ref", "")).lower() == anchor.get("external_ref_hash")
    )


def matches_batch_action(request_payload: Dict[str, Any], action: Dict[str, Any]) -> bool:
    if action.get("account") != request_payload.get("contract"):
        return False

    data = action.get("data", {})
    anchor = request_payload.get("anchor", {})
    action_name = action.get("name")

    if action_name == "submitroot":
        return (
            str(data.get("submitter")) == request_payload.get("submitter")
            and str(data.get("root_hash", "")).lower() == anchor.get("root_hash")
            and str(data.get("external_ref", "")).lower() == anchor.get("external_ref_hash")
            and coerce_positive_int(data.get("leaf_count")) == anchor.get("leaf_count")
        )

    batch_id = anchor.get("batch_id")
    if batch_id is None:
        return False

    if action_name == "linkmanifest":
        return (
            coerce_positive_int(data.get("id")) == batch_id
            and str(data.get("manifest_hash", "")).lower() == anchor.get("manifest_hash")
        )

    if action_name == "closebatch":
        return coerce_positive_int(data.get("id")) == batch_id

    return False


def verify_inclusion(request_payload: Dict[str, Any]) -> Dict[str, Any]:
    tx_id = request_payload.get("tx_id")
    block_num = request_payload.get("block_num")
    rpc_urls = normalize_rpc_urls(request_payload.get("rpc_urls", request_payload.get("rpc_url")), "")
    if not tx_id or not block_num or not rpc_urls:
        raise TransactionLookupPending("transaction metadata is incomplete")

    matcher = matches_single_action if request_payload.get("mode") == "single" else matches_batch_action
    providers_checked: list[Dict[str, Any]] = []
    matched_results: list[Dict[str, Any]] = []
    had_mismatch = False
    pending_messages: list[str] = []

    for rpc_url in rpc_urls:
        provider_result = {
            "rpc_url": rpc_url,
            "ok": False,
            "block_num": None,
            "action_name": None,
            "verified_at": iso_now(),
            "error": None,
        }
        try:
            tx_payload = fetch_transaction_details(rpc_url, tx_id, block_num)
            actual_block_num = extract_transaction_block_num(tx_payload)
            matched_action = None
            for action in iter_transaction_actions(tx_payload):
                if matcher(request_payload, action):
                    matched_action = action
                    break

            if matched_action is None:
                had_mismatch = True
                provider_result["error"] = "indexed transaction does not match request anchor"
                providers_checked.append(provider_result)
                continue

            provider_result["ok"] = True
            provider_result["block_num"] = actual_block_num or block_num
            provider_result["action_name"] = matched_action.get("name")
            providers_checked.append(provider_result)
            matched_results.append(
                {
                    "rpc_url": rpc_url,
                    "verified_block_num": actual_block_num or block_num,
                    "verified_action": {
                        "account": matched_action.get("account"),
                        "name": matched_action.get("name"),
                        "data": matched_action.get("data", {}),
                    },
                }
            )
        except TransactionLookupPending as exc:
            pending_messages.append(str(exc))
            provider_result["error"] = str(exc)
            providers_checked.append(provider_result)
        except ValueError as exc:
            had_mismatch = True
            provider_result["error"] = str(exc)
            providers_checked.append(provider_result)
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            provider_result["error"] = str(exc)
            providers_checked.append(provider_result)

    if matched_results:
        primary_match = matched_results[0]
        return {
            "verified_at": iso_now(),
            "verified_block_num": primary_match["verified_block_num"],
            "verified_action": primary_match["verified_action"],
            "verification_state": {
                "policy": request_payload.get("verification_policy", "single-provider"),
                "providers_checked": providers_checked,
                "consensus": {
                    "verified": True,
                    "provider_count_ok": len(matched_results),
                    "provider_count_total": len(providers_checked),
                    "provider_disagreement": had_mismatch,
                },
            },
            "provider_disagreement": had_mismatch,
        }

    if pending_messages and not had_mismatch:
        raise TransactionLookupPending(pending_messages[-1])
    raise ValueError("indexed transaction does not match request anchor")


def refresh_inclusion_verification(existing: Dict[str, Any], strict: bool = False) -> Dict[str, Any]:
    if not existing.get("tx_id") or not existing.get("block_num"):
        existing["inclusion_verified"] = False
        existing["verified_action"] = None
        existing["verification_state"] = None
        existing["provider_disagreement"] = False
        return existing

    try:
        verification = verify_inclusion(existing)
    except TransactionLookupPending as exc:
        existing["inclusion_verified"] = False
        existing["inclusion_verification_error"] = str(exc)
        existing["verified_action"] = None
        existing["verification_state"] = None
        existing["provider_disagreement"] = False
        return existing
    except ValueError:
        existing["inclusion_verified"] = False
        existing["verified_action"] = None
        existing["inclusion_verification_error"] = "indexed transaction does not match request anchor"
        existing["verification_state"] = None
        existing["provider_disagreement"] = False
        if strict:
            raise
        return existing

    existing["inclusion_verified"] = True
    if not existing.get("inclusion_verified_at"):
        existing["inclusion_verified_at"] = verification["verified_at"]
    verified_block_num = verification.get("verified_block_num")
    if isinstance(verified_block_num, int) and verified_block_num > 0:
        existing["block_num"] = verified_block_num
    existing["inclusion_verification_error"] = None
    existing["verified_action"] = verification["verified_action"]
    existing["verification_state"] = verification.get("verification_state")
    existing["provider_disagreement"] = verification.get("provider_disagreement", False)
    return existing


def update_to_included(existing: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    if existing.get("status") == "failed":
        raise ValueError("failed request cannot move to included")

    tx_id = require_hex_64(body, "tx_id")
    block_num = require_int(body, "block_num")
    if block_num <= 0:
        raise ValueError("block_num must be positive integer")
    existing_rpc_config = existing.get("rpc_urls", existing.get("rpc_url"))
    rpc_url = body.get("rpc_url", existing.get("rpc_url"))
    rpc_urls = normalize_rpc_urls(body.get("rpc_urls", existing_rpc_config), existing.get("rpc_url") or "")
    rpc_url = rpc_urls[0]

    if existing.get("tx_id") and existing["tx_id"] != tx_id:
        raise ValueError("tx_id cannot be changed once recorded")
    if existing.get("block_num") and existing["block_num"] != block_num:
        raise ValueError("block_num cannot be changed once recorded")

    existing["tx_id"] = tx_id
    existing["block_num"] = block_num
    existing["rpc_url"] = rpc_url
    existing["rpc_urls"] = rpc_urls
    if not existing.get("included_at"):
        existing["included_at"] = iso_now()
    if existing.get("status") != "finalized":
        existing["status"] = "included"

    refresh_inclusion_verification(existing, strict=True)
    existing["updated_at"] = iso_now()
    return existing


def update_anchor_metadata(existing: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    anchor_updates = require_mapping(body, "anchor")
    mode = existing.get("mode")
    validated_updates = validate_anchor_metadata(anchor_updates, mode)

    anchor = dict(existing.get("anchor", {}))
    if existing.get("status") in {"failed", "finalized"}:
        for key, value in validated_updates.items():
            if key not in anchor or anchor[key] != value:
                raise ValueError("terminal request cannot accept new anchor mutations")

    for key, value in validated_updates.items():
        if key in anchor and anchor[key] != value:
            raise ValueError(f"{key} cannot be changed once recorded")
    anchor.update(validated_updates)
    existing["anchor"] = anchor
    existing["updated_at"] = iso_now()
    if existing.get("tx_id") and existing.get("block_num"):
        refresh_inclusion_verification(existing, strict=False)
    return existing


def mark_failed(existing: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    if existing.get("status") == "finalized":
        raise ValueError("finalized request cannot be marked failed")

    reason = require_optional_reason(body, "reason")
    if reason is None:
        raise ValueError("reason must be provided")

    details = body.get("details")
    if existing.get("status") == "failed":
        if existing.get("failure_reason") != reason or existing.get("failure_details") != details:
            raise ValueError("failed request metadata cannot be changed once recorded")
        existing["updated_at"] = iso_now()
        return existing

    existing["status"] = "failed"
    existing["failed_at"] = iso_now()
    existing["failure_reason"] = reason
    existing["failure_details"] = details
    existing["updated_at"] = iso_now()
    return existing


def ensure_registration_compatible(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    immutable_fields = (
        "request_id",
        "trace_id",
        "mode",
        "submitter",
        "contract",
    )
    for field_name in immutable_fields:
        if existing.get(field_name) != incoming.get(field_name):
            raise ValueError(f"{field_name} does not match existing request")

    existing_anchor = existing.get("anchor", {})
    incoming_anchor = incoming.get("anchor", {})
    for key, value in incoming_anchor.items():
        if key in existing_anchor and existing_anchor[key] != value:
            raise ValueError(f"anchor.{key} does not match existing request")

    if existing.get("rpc_url") != incoming.get("rpc_url"):
        raise ValueError("rpc_url does not match existing request")
    if existing.get("rpc_urls") != incoming.get("rpc_urls"):
        raise ValueError("rpc_urls do not match existing request")

    return existing


def poll_request(existing: Dict[str, Any]) -> Dict[str, Any]:
    if existing.get("status") == "failed":
        return existing

    block_num = existing.get("block_num")
    rpc_urls = normalize_rpc_urls(existing.get("rpc_urls", existing.get("rpc_url")), "")
    if not block_num or not rpc_urls:
        existing["updated_at"] = iso_now()
        return existing

    refresh_inclusion_verification(existing, strict=False)

    rpc_url, chain_info = fetch_chain_info_any(rpc_urls)
    head_block_num = chain_info.get("head_block_num")
    last_irreversible_block_num = chain_info.get("last_irreversible_block_num")

    existing["chain_state"] = {
        "provider": rpc_url,
        "head_block_num": head_block_num,
        "last_irreversible_block_num": last_irreversible_block_num,
    }
    existing["updated_at"] = iso_now()

    if (
        existing.get("inclusion_verified")
        and isinstance(last_irreversible_block_num, int)
        and last_irreversible_block_num >= block_num
    ):
        existing["status"] = "finalized"
        if not existing.get("finalized_at"):
            existing["finalized_at"] = iso_now()
    elif existing.get("tx_id"):
        existing["status"] = "included"

    return existing


def should_attempt_startup_recovery(payload: Dict[str, Any]) -> bool:
    if payload.get("status") == "failed":
        return False
    if payload.get("tx_id") and payload.get("block_num"):
        return True
    return False


class FinalityWatcherHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryFinalityWatcher/0.2"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.write_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": "finality-watcher",
                    "auth_required": bool(self.server.auth_token),
                    "insecure_dev_mode": self.server.insecure_dev_mode,
                    "store": self.server.store.describe(),
                    "startup_checks": self.server.startup_checks,
                    "startup_recovery": self.server.startup_recovery,
                },
            )
            return

        prefix = "/v1/watch/"
        if self.path.startswith(prefix):
            request_id = self.path[len(prefix):]
            if not request_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self.server.store.get_request(request_id)
            except KeyError:
                self.send_error(HTTPStatus.NOT_FOUND, "Request not found")
                return

            self.write_json(HTTPStatus.OK, payload)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        try:
            require_mutation_auth(self)

            if self.path == "/v1/watch/register":
                body = read_json_body(self)
                payload = normalize_watch_request(body, self.server.default_rpc_url)
                if payload.get("tx_id") and payload.get("block_num"):
                    refresh_inclusion_verification(payload, strict=False)
                try:
                    existing = self.server.store.get_request(payload["request_id"])
                except KeyError:
                    self.server.store.upsert_request(payload["request_id"], payload)
                    self.write_json(HTTPStatus.OK, payload)
                    return

                ensure_registration_compatible(existing, payload)
                if existing.get("tx_id") and existing.get("block_num"):
                    refresh_inclusion_verification(existing, strict=False)
                self.write_json(HTTPStatus.OK, existing)
                return

            if self.path == "/v1/watch/poll":
                results = self.server.poll_all_once()
                self.write_json(HTTPStatus.OK, {"updated": results})
                return

            if self.path.startswith("/v1/watch/") and self.path.endswith("/included"):
                request_id = self.path[len("/v1/watch/"):-len("/included")]
                body = read_json_body(self)
                existing = self.server.store.get_request(request_id)
                updated = update_to_included(existing, body)
                self.server.store.upsert_request(request_id, updated)
                self.write_json(HTTPStatus.OK, updated)
                return

            if self.path.startswith("/v1/watch/") and self.path.endswith("/anchor"):
                request_id = self.path[len("/v1/watch/"):-len("/anchor")]
                body = read_json_body(self)
                existing = self.server.store.get_request(request_id)
                updated = update_anchor_metadata(existing, body)
                self.server.store.upsert_request(request_id, updated)
                self.write_json(HTTPStatus.OK, updated)
                return

            if self.path.startswith("/v1/watch/") and self.path.endswith("/failed"):
                request_id = self.path[len("/v1/watch/"):-len("/failed")]
                body = read_json_body(self)
                existing = self.server.store.get_request(request_id)
                updated = mark_failed(existing, body)
                self.server.store.upsert_request(request_id, updated)
                self.write_json(HTTPStatus.OK, updated)
                return

            if self.path.startswith("/v1/watch/") and self.path.endswith("/poll"):
                request_id = self.path[len("/v1/watch/"):-len("/poll")]
                existing = self.server.store.get_request(request_id)
                updated = poll_request(existing)
                self.server.store.upsert_request(request_id, updated)
                self.write_json(HTTPStatus.OK, updated)
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Request not found")
        except PermissionError as exc:
            self.write_json(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except urllib.error.URLError as exc:
            self.write_json(HTTPStatus.BAD_GATEWAY, {"error": f"rpc call failed: {exc.reason}"})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def write_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class FinalityWatcherServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        store: FinalityStoreBase,
        default_rpc_url: str,
        poll_interval_sec: int,
        auth_token: str = "",
        insecure_dev_mode: bool = False,
    ):
        if not auth_token and not insecure_dev_mode:
            raise ValueError("finality watcher requires --auth-token unless --insecure-dev-mode is enabled")
        super().__init__(server_address, handler)
        self.store = store
        self.default_rpc_url = default_rpc_url
        self.poll_interval_sec = poll_interval_sec
        self.auth_token = auth_token
        self.insecure_dev_mode = insecure_dev_mode
        self._stop_event = threading.Event()
        self._poller = threading.Thread(target=self._poll_loop, daemon=True)
        self.startup_checks = self.run_startup_checks()
        self.startup_recovery = self.recover_requests_once()

    def start_background_polling(self) -> None:
        self._poller.start()

    def stop_background_polling(self) -> None:
        self._stop_event.set()

    def poll_all_once(self) -> Dict[str, str]:
        results: Dict[str, str] = {}
        for request_id, payload in self.store.list_requests().items():
            updated = poll_request(payload)
            self.store.upsert_request(request_id, updated)
            results[request_id] = updated["status"]
        return results

    def run_startup_checks(self) -> Dict[str, Any]:
        requests = self.store.list_requests()
        status_counts: Dict[str, int] = {}
        recoverable = 0
        for payload in requests.values():
            status = str(payload.get("status") or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            if should_attempt_startup_recovery(payload):
                recoverable += 1
        return {
            "checked_at": iso_now(),
            "request_count": len(requests),
            "recoverable_request_count": recoverable,
            "status_counts": status_counts,
        }

    def recover_requests_once(self) -> Dict[str, Any]:
        summary = {
            "started_at": iso_now(),
            "attempted": 0,
            "updated": 0,
            "finalized": 0,
            "failed": 0,
            "errors": [],
        }
        for request_id, payload in self.store.list_requests().items():
            if not should_attempt_startup_recovery(payload):
                continue
            summary["attempted"] += 1
            before_status = payload.get("status")
            try:
                updated = poll_request(payload)
                self.store.upsert_request(request_id, updated)
                if updated != payload:
                    summary["updated"] += 1
                if before_status != "finalized" and updated.get("status") == "finalized":
                    summary["finalized"] += 1
            except Exception as exc:
                summary["failed"] += 1
                summary["errors"].append(
                    {
                        "request_id": request_id,
                        "error": str(exc),
                    }
                )
        summary["completed_at"] = iso_now()
        return summary

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(self.poll_interval_sec):
            try:
                self.poll_all_once()
            except Exception:
                continue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeNotary finality watcher.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--rpc-url", default="https://history.denotary.io")
    parser.add_argument("--state-backend", default="file")
    parser.add_argument("--state-file", default="runtime/finality-state.json")
    parser.add_argument("--state-db", default="runtime/finality-state.sqlite3")
    parser.add_argument("--poll-interval-sec", type=int, default=10)
    parser.add_argument("--auth-token", default="")
    parser.add_argument("--insecure-dev-mode", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = build_finality_store(
        state_backend=args.state_backend,
        state_file=args.state_file,
        state_db=args.state_db,
    )
    server = FinalityWatcherServer(
        (args.host, args.port),
        FinalityWatcherHandler,
        store,
        args.rpc_url,
        args.poll_interval_sec,
        args.auth_token,
        args.insecure_dev_mode,
    )
    server.start_background_polling()
    print(f"Finality watcher listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
