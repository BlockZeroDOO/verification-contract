from __future__ import annotations

import argparse
import json
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from finality_store import FinalityStore

MAX_REQUEST_BODY_BYTES = 256 * 1024
HEX_64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
TRACE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
ACCOUNT_NAME_RE = re.compile(r"^[a-z1-5.]{1,12}$")


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


def read_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    if content_length < 0 or content_length > MAX_REQUEST_BODY_BYTES:
        raise ValueError("request body is too large")
    body = handler.rfile.read(content_length)
    try:
        return json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError as exc:
        raise ValueError("request body must be valid JSON") from exc


def rpc_post_json(url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    request = urllib.request.Request(
        f"{url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_chain_info(rpc_url: str) -> Dict[str, Any]:
    return rpc_post_json(rpc_url, "/v1/chain/get_info", {})


def normalize_watch_request(body: Dict[str, Any], default_rpc_url: str) -> Dict[str, Any]:
    request_id = require_hex_64(body, "request_id")
    trace_id = require_trace_id(body, "trace_id")
    mode = require_string(body, "mode")
    if mode not in {"single", "batch"}:
        raise ValueError("mode must be either 'single' or 'batch'")

    submitter = require_account_name(body, "submitter")
    contract = require_account_name(body, "contract")
    anchor = validate_anchor_metadata(require_mapping(body, "anchor"), mode)

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

    rpc_url = body.get("rpc_url", default_rpc_url)
    if not isinstance(rpc_url, str) or not rpc_url:
        raise ValueError("rpc_url must be a non-empty string")

    status = "included" if tx_id and block_num else "submitted"
    timestamp = iso_now()

    return {
        "request_id": request_id,
        "trace_id": trace_id,
        "mode": mode,
        "submitter": submitter,
        "contract": contract,
        "rpc_url": rpc_url,
        "anchor": anchor,
        "tx_id": tx_id,
        "block_num": block_num,
        "status": status,
        "registered_at": timestamp,
        "updated_at": timestamp,
        "finalized_at": None,
        "chain_state": {
            "head_block_num": None,
            "last_irreversible_block_num": None,
        },
    }


def update_to_included(existing: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    tx_id = require_hex_64(body, "tx_id")
    block_num = require_int(body, "block_num")
    if block_num <= 0:
        raise ValueError("block_num must be positive integer")
    rpc_url = body.get("rpc_url", existing.get("rpc_url"))
    if not isinstance(rpc_url, str) or not rpc_url:
        raise ValueError("rpc_url must be a non-empty string")

    if existing.get("tx_id") and existing["tx_id"] != tx_id:
        raise ValueError("tx_id cannot be changed once recorded")
    if existing.get("block_num") and existing["block_num"] != block_num:
        raise ValueError("block_num cannot be changed once recorded")

    existing["tx_id"] = tx_id
    existing["block_num"] = block_num
    existing["rpc_url"] = rpc_url
    if existing.get("status") != "finalized":
        existing["status"] = "included"
    existing["updated_at"] = iso_now()
    return existing


def update_anchor_metadata(existing: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    anchor_updates = require_mapping(body, "anchor")
    mode = existing.get("mode")
    validated_updates = validate_anchor_metadata(anchor_updates, mode)

    anchor = dict(existing.get("anchor", {}))
    for key, value in validated_updates.items():
        if key in anchor and anchor[key] != value:
            raise ValueError(f"{key} cannot be changed once recorded")
    anchor.update(validated_updates)
    existing["anchor"] = anchor
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

    return existing


def poll_request(existing: Dict[str, Any]) -> Dict[str, Any]:
    block_num = existing.get("block_num")
    rpc_url = existing.get("rpc_url")
    if not block_num or not rpc_url:
        existing["updated_at"] = iso_now()
        return existing

    chain_info = fetch_chain_info(rpc_url)
    head_block_num = chain_info.get("head_block_num")
    last_irreversible_block_num = chain_info.get("last_irreversible_block_num")

    existing["chain_state"] = {
        "head_block_num": head_block_num,
        "last_irreversible_block_num": last_irreversible_block_num,
    }
    existing["updated_at"] = iso_now()

    if isinstance(last_irreversible_block_num, int) and last_irreversible_block_num >= block_num:
        existing["status"] = "finalized"
        if not existing.get("finalized_at"):
            existing["finalized_at"] = iso_now()
    elif existing.get("tx_id"):
        existing["status"] = "included"

    return existing


class FinalityWatcherHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryFinalityWatcher/0.1"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.write_json(HTTPStatus.OK, {"status": "ok", "service": "finality-watcher"})
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
            if self.path == "/v1/watch/register":
                body = read_json_body(self)
                payload = normalize_watch_request(body, self.server.default_rpc_url)
                try:
                    existing = self.server.store.get_request(payload["request_id"])
                except KeyError:
                    self.server.store.upsert_request(payload["request_id"], payload)
                    self.write_json(HTTPStatus.OK, payload)
                    return

                self.write_json(HTTPStatus.OK, ensure_registration_compatible(existing, payload))
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
        store: FinalityStore,
        default_rpc_url: str,
        poll_interval_sec: int,
    ):
        super().__init__(server_address, handler)
        self.store = store
        self.default_rpc_url = default_rpc_url
        self.poll_interval_sec = poll_interval_sec
        self._stop_event = threading.Event()
        self._poller = threading.Thread(target=self._poll_loop, daemon=True)

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
    parser.add_argument("--state-file", default="runtime/finality-state.json")
    parser.add_argument("--poll-interval-sec", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = FinalityStore(args.state_file)
    server = FinalityWatcherServer(
        (args.host, args.port),
        FinalityWatcherHandler,
        store,
        args.rpc_url,
        args.poll_interval_sec,
    )
    server.start_background_polling()
    print(f"Finality watcher listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
