from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from finality_store import FinalityStore
from receipt_service import build_batch_receipt, build_single_receipt


def select_requests(store: FinalityStore, predicate) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for payload in store.list_requests().values():
        if predicate(payload):
            matches.append(payload)
    matches.sort(key=lambda item: item.get("updated_at") or item.get("registered_at") or "", reverse=True)
    return matches


def maybe_build_receipt(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if payload.get("status") != "finalized" or not payload.get("inclusion_verified", False):
        return None

    mode = payload.get("mode")
    if mode == "single":
        return build_single_receipt(payload)
    if mode == "batch":
        return build_batch_receipt(payload)
    return None


def build_proof_chain(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    chain = [
        {
            "stage": "request_registered",
            "status": "completed",
            "timestamp": payload.get("registered_at"),
            "details": {
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
                "mode": payload.get("mode"),
                "submitter": payload.get("submitter"),
            },
        }
    ]

    if payload.get("tx_id") and payload.get("block_num"):
        chain.append(
            {
                "stage": "transaction_included",
                "status": "completed",
                "timestamp": payload.get("updated_at"),
                "details": {
                    "tx_id": payload.get("tx_id"),
                    "block_num": payload.get("block_num"),
                },
            }
        )

    if payload.get("tx_id"):
        chain.append(
            {
                "stage": "transaction_verified",
                "status": "completed" if payload.get("inclusion_verified") else "pending",
                "timestamp": payload.get("inclusion_verified_at"),
                "details": {
                    "verified_action": payload.get("verified_action"),
                    "verification_error": payload.get("inclusion_verification_error"),
                },
            }
        )

    if payload.get("status") == "finalized":
        chain.append(
            {
                "stage": "block_finalized",
                "status": "completed" if payload.get("inclusion_verified") else "pending",
                "timestamp": payload.get("finalized_at"),
                "details": payload.get("chain_state", {}),
            }
        )
    else:
        chain.append(
            {
                "stage": "block_finalized",
                "status": "pending",
                "timestamp": None,
                "details": payload.get("chain_state", {}),
            }
        )

    return chain


def build_audit_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    anchor = payload.get("anchor", {})
    return {
        "request_id": payload.get("request_id"),
        "trace_id": payload.get("trace_id"),
        "mode": payload.get("mode"),
        "submitter": payload.get("submitter"),
        "contract": payload.get("contract"),
        "status": payload.get("status"),
        "commitment_id": anchor.get("commitment_id"),
        "batch_id": anchor.get("batch_id"),
        "external_ref_hash": anchor.get("external_ref_hash"),
        "tx_id": payload.get("tx_id"),
        "block_num": payload.get("block_num"),
        "registered_at": payload.get("registered_at"),
        "updated_at": payload.get("updated_at"),
        "finalized_at": payload.get("finalized_at"),
        "failed_at": payload.get("failed_at"),
        "failure_reason": payload.get("failure_reason"),
        "failure_details": payload.get("failure_details"),
        "inclusion_verified": payload.get("inclusion_verified", False),
        "inclusion_verified_at": payload.get("inclusion_verified_at"),
        "inclusion_verification_error": payload.get("inclusion_verification_error"),
        "verified_action": payload.get("verified_action"),
        "anchor": anchor,
        "chain_state": payload.get("chain_state", {}),
    }


def build_audit_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "record": build_audit_record(payload),
        "receipt": maybe_build_receipt(payload),
        "proof_chain": build_proof_chain(payload),
    }


def first_or_404(handler: BaseHTTPRequestHandler, payloads: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not payloads:
        handler.send_error(HTTPStatus.NOT_FOUND, "Record not found")
        return None
    return payloads[0]


def parse_positive_int(value: Optional[str], field_name: str) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be integer") from exc
    if parsed < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return parsed


def apply_pagination(payloads: List[Dict[str, Any]], query: Dict[str, List[str]]) -> Dict[str, Any]:
    limit = parse_positive_int(query.get("limit", [None])[0], "limit")
    offset = parse_positive_int(query.get("offset", [None])[0], "offset")

    effective_limit = 50 if limit is None else min(limit, 200)
    effective_offset = 0 if offset is None else offset
    paged_items = payloads[effective_offset:effective_offset + effective_limit]

    return {
        "limit": effective_limit,
        "offset": effective_offset,
        "total": len(payloads),
        "items": paged_items,
    }


class AuditApiHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryAuditApi/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        try:
            if parsed.path == "/healthz":
                self.write_json(HTTPStatus.OK, {"status": "ok", "service": "audit-api"})
                return

            if parsed.path == "/v1/audit/search":
                query = parse_qs(parsed.query)
                payloads = select_requests(self.server.store, lambda item: self.matches_query(item, query))
                paged = apply_pagination(payloads, query)
                record_items = [build_audit_record(item) for item in paged["items"]]
                response = {
                    "count": len(record_items),
                    "total": paged["total"],
                    "limit": paged["limit"],
                    "offset": paged["offset"],
                    "results": record_items,
                }
                if query.get("format", ["json"])[0] == "jsonl":
                    self.write_jsonl(HTTPStatus.OK, record_items)
                else:
                    self.write_json(HTTPStatus.OK, response)
                return

            prefix = "/v1/audit/requests/"
            if parsed.path.startswith(prefix):
                request_id = parsed.path[len(prefix):]
                if not request_id:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                try:
                    payload = self.server.store.get_request(request_id)
                except KeyError:
                    self.send_error(HTTPStatus.NOT_FOUND, "Record not found")
                    return
                self.write_json(HTTPStatus.OK, build_audit_record(payload))
                return

            prefix = "/v1/audit/chain/"
            if parsed.path.startswith(prefix):
                request_id = parsed.path[len(prefix):]
                if not request_id:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                try:
                    payload = self.server.store.get_request(request_id)
                except KeyError:
                    self.send_error(HTTPStatus.NOT_FOUND, "Record not found")
                    return
                self.write_json(HTTPStatus.OK, build_audit_chain(payload))
                return

            prefix = "/v1/audit/by-external-ref/"
            if parsed.path.startswith(prefix):
                external_ref_hash = parsed.path[len(prefix):]
                payload = first_or_404(
                    self,
                    select_requests(
                        self.server.store,
                        lambda item: item.get("anchor", {}).get("external_ref_hash") == external_ref_hash,
                    ),
                )
                if payload is None:
                    return
                self.write_json(HTTPStatus.OK, build_audit_chain(payload))
                return

            prefix = "/v1/audit/by-tx/"
            if parsed.path.startswith(prefix):
                tx_id = parsed.path[len(prefix):]
                payload = first_or_404(
                    self,
                    select_requests(self.server.store, lambda item: item.get("tx_id") == tx_id),
                )
                if payload is None:
                    return
                self.write_json(HTTPStatus.OK, build_audit_chain(payload))
                return

            prefix = "/v1/audit/by-commitment/"
            if parsed.path.startswith(prefix):
                commitment_id = parse_positive_int(parsed.path[len(prefix):], "commitment_id")
                if commitment_id is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                payload = first_or_404(
                    self,
                    select_requests(
                        self.server.store,
                        lambda item: item.get("anchor", {}).get("commitment_id") == commitment_id,
                    ),
                )
                if payload is None:
                    return
                self.write_json(HTTPStatus.OK, build_audit_chain(payload))
                return

            prefix = "/v1/audit/by-batch/"
            if parsed.path.startswith(prefix):
                batch_id = parse_positive_int(parsed.path[len(prefix):], "batch_id")
                if batch_id is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                payload = first_or_404(
                    self,
                    select_requests(
                        self.server.store,
                        lambda item: item.get("anchor", {}).get("batch_id") == batch_id,
                    ),
                )
                if payload is None:
                    return
                self.write_json(HTTPStatus.OK, build_audit_chain(payload))
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def matches_query(self, payload: Dict[str, Any], query: Dict[str, List[str]]) -> bool:
        mode = query.get("mode", [None])[0]
        status = query.get("status", [None])[0]
        submitter = query.get("submitter", [None])[0]
        contract = query.get("contract", [None])[0]
        external_ref_hash = query.get("external_ref_hash", [None])[0]
        commitment_id = parse_positive_int(query.get("commitment_id", [None])[0], "commitment_id")
        batch_id = parse_positive_int(query.get("batch_id", [None])[0], "batch_id")
        anchor = payload.get("anchor", {})

        if mode and payload.get("mode") != mode:
            return False
        if status and payload.get("status") != status:
            return False
        if submitter and payload.get("submitter") != submitter:
            return False
        if contract and payload.get("contract") != contract:
            return False
        if external_ref_hash and anchor.get("external_ref_hash") != external_ref_hash:
            return False
        if commitment_id is not None and anchor.get("commitment_id") != commitment_id:
            return False
        if batch_id is not None and anchor.get("batch_id") != batch_id:
            return False
        return True

    def log_message(self, format: str, *args: Any) -> None:
        return

    def write_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def write_jsonl(self, status: HTTPStatus, items: List[Dict[str, Any]]) -> None:
        lines = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items)
        encoded = lines.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class AuditApiServer(ThreadingHTTPServer):
    def __init__(self, server_address: Tuple[str, int], handler: type[BaseHTTPRequestHandler], store: FinalityStore):
        super().__init__(server_address, handler)
        self.store = store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeNotary audit API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8083)
    parser.add_argument("--state-file", default="runtime/finality-state.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = FinalityStore(args.state_file)
    server = AuditApiServer((args.host, args.port), AuditApiHandler, store)
    print(f"Audit API listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
