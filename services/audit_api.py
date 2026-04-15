from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from finality_store import build_finality_store
from finality_store_base import FinalityStoreBase
from openapi_docs import swagger_ui_html
from privacy_mode import redact_audit_record, redact_proof_chain, redact_receipt_payload, require_privacy_mode
from receipt_service import build_batch_receipt, build_single_receipt, derive_trust_state, receipt_available


def select_requests(store: FinalityStoreBase, predicate) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for payload in store.list_requests().values():
        if predicate(payload):
            matches.append(payload)
    matches.sort(key=lambda item: item.get("updated_at") or item.get("registered_at") or "", reverse=True)
    return matches


def maybe_build_receipt(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not receipt_available(payload):
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
        verification_status = "pending"
        if payload.get("inclusion_verified"):
            verification_status = "completed"
        elif payload.get("inclusion_verification_error"):
            verification_status = "failed"

        chain.append(
            {
                "stage": "transaction_verified",
                "status": verification_status,
                "timestamp": payload.get("inclusion_verified_at"),
                "details": {
                    "verified_action": payload.get("verified_action"),
                    "verification_error": payload.get("inclusion_verification_error"),
                    "verification_policy": payload.get("verification_policy"),
                    "verification_min_success": payload.get("verification_min_success"),
                    "provider_disagreement": payload.get("provider_disagreement", False),
                    "verification_state": payload.get("verification_state"),
                },
            }
        )

    if payload.get("status") == "finalized":
        chain.append(
            {
                "stage": "block_finalized",
                "status": "completed",
                "timestamp": payload.get("finalized_at"),
                "details": {
                    **payload.get("chain_state", {}),
                    "verification_gate_satisfied": payload.get("inclusion_verified", False),
                    "trust_state": derive_trust_state(payload),
                    "receipt_available": receipt_available(payload),
                },
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
        "trust_state": derive_trust_state(payload),
        "receipt_available": receipt_available(payload),
        "inclusion_verified": payload.get("inclusion_verified", False),
        "inclusion_verified_at": payload.get("inclusion_verified_at"),
        "inclusion_verification_error": payload.get("inclusion_verification_error"),
        "verification_policy": payload.get("verification_policy"),
        "verification_min_success": payload.get("verification_min_success"),
        "provider_disagreement": payload.get("provider_disagreement", False),
        "verification_state": payload.get("verification_state"),
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


def build_openapi_spec() -> Dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "DeNotary Audit API",
            "version": "1.0.0",
            "description": "Read-only audit surface for request, receipt, and proof-chain lookups.",
        },
        "servers": [{"url": "http://127.0.0.1:8083", "description": "Local default"}],
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
            "/v1/audit/requests/{request_id}": {
                "get": {
                    "summary": "Get audit record by request ID",
                    "parameters": [
                        {
                            "name": "request_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Audit record",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditRecord"}
                                }
                            },
                        },
                        "404": {"description": "Record not found"},
                    },
                }
            },
            "/v1/audit/chain/{request_id}": {
                "get": {
                    "summary": "Get audit chain by request ID",
                    "parameters": [
                        {
                            "name": "request_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Audit chain",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditChain"}
                                }
                            },
                        },
                        "404": {"description": "Record not found"},
                    },
                }
            },
            "/v1/audit/search": {
                "get": {
                    "summary": "Search audit records",
                    "parameters": [
                        {"name": "mode", "in": "query", "schema": {"type": "string"}},
                        {"name": "status", "in": "query", "schema": {"type": "string"}},
                        {"name": "trust_state", "in": "query", "schema": {"type": "string"}},
                        {"name": "submitter", "in": "query", "schema": {"type": "string"}},
                        {"name": "contract", "in": "query", "schema": {"type": "string"}},
                        {"name": "external_ref_hash", "in": "query", "schema": {"type": "string"}},
                        {"name": "commitment_id", "in": "query", "schema": {"type": "integer"}},
                        {"name": "batch_id", "in": "query", "schema": {"type": "integer"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer"}},
                        {"name": "format", "in": "query", "schema": {"type": "string", "enum": ["json", "jsonl"]}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditSearchResponse"}
                                },
                                "application/x-ndjson": {
                                    "schema": {"type": "string"}
                                },
                            },
                        },
                        "400": {"description": "Validation error"},
                    },
                }
            },
            "/v1/audit/by-external-ref/{external_ref_hash}": {
                "get": {
                    "summary": "Lookup by external_ref_hash",
                    "parameters": [
                        {
                            "name": "external_ref_hash",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Audit chain",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditChain"}
                                }
                            },
                        },
                        "404": {"description": "Record not found"},
                    },
                }
            },
            "/v1/audit/by-tx/{tx_id}": {
                "get": {
                    "summary": "Lookup by transaction ID",
                    "parameters": [
                        {
                            "name": "tx_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Audit chain",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditChain"}
                                }
                            },
                        },
                        "404": {"description": "Record not found"},
                    },
                }
            },
            "/v1/audit/by-commitment/{commitment_id}": {
                "get": {
                    "summary": "Lookup by commitment ID",
                    "parameters": [
                        {
                            "name": "commitment_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Audit chain",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditChain"}
                                }
                            },
                        },
                        "404": {"description": "Record not found"},
                    },
                }
            },
            "/v1/audit/by-batch/{batch_id}": {
                "get": {
                    "summary": "Lookup by batch ID",
                    "parameters": [
                        {
                            "name": "batch_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Audit chain",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuditChain"}
                                }
                            },
                        },
                        "404": {"description": "Record not found"},
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
                        "service": {"type": "string", "example": "audit-api"},
                        "privacy_mode": {"type": "string", "example": "full"},
                    },
                    "required": ["status", "service", "privacy_mode"],
                },
                "AuditRecord": {
                    "type": "object",
                    "properties": {
                        "request_id": {"type": "string"},
                        "trace_id": {"type": "string"},
                        "mode": {"type": "string"},
                        "submitter": {"type": "string"},
                        "contract": {"type": "string"},
                        "status": {"type": "string"},
                        "trust_state": {"type": "string"},
                        "receipt_available": {"type": "boolean"},
                        "commitment_id": {"type": "integer"},
                        "batch_id": {"type": "integer"},
                        "external_ref_hash": {"type": "string"},
                        "tx_id": {"type": "string"},
                        "block_num": {"type": "integer"},
                        "registered_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                        "finalized_at": {"type": "string", "format": "date-time"},
                        "failed_at": {"type": "string", "format": "date-time"},
                        "failure_reason": {"type": "string"},
                        "failure_details": {"type": "object", "additionalProperties": True},
                        "inclusion_verified": {"type": "boolean"},
                        "inclusion_verified_at": {"type": "string", "format": "date-time"},
                        "inclusion_verification_error": {"type": "string"},
                        "verification_policy": {"type": "string"},
                        "verification_min_success": {"type": "integer"},
                        "provider_disagreement": {"type": "boolean"},
                        "verification_state": {"type": "object", "additionalProperties": True},
                        "verified_action": {"type": "object", "additionalProperties": True},
                        "anchor": {"type": "object", "additionalProperties": True},
                        "chain_state": {"type": "object", "additionalProperties": True},
                    },
                    "required": [
                        "request_id",
                        "mode",
                        "submitter",
                        "contract",
                        "status",
                        "trust_state",
                        "receipt_available",
                        "anchor",
                        "chain_state",
                    ],
                },
                "AuditChainStage": {
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string"},
                        "status": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "details": {"type": "object", "additionalProperties": True},
                    },
                    "required": ["stage", "status", "details"],
                },
                "AuditChain": {
                    "type": "object",
                    "properties": {
                        "record": {"$ref": "#/components/schemas/AuditRecord"},
                        "receipt": {
                            "oneOf": [
                                {"$ref": "#/components/schemas/AuditReceipt"},
                                {"type": "null"},
                            ]
                        },
                        "proof_chain": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/AuditChainStage"},
                        },
                    },
                    "required": ["record", "receipt", "proof_chain"],
                },
                "AuditReceipt": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "AuditSearchResponse": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "total": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"},
                        "results": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/AuditRecord"},
                        },
                    },
                    "required": ["count", "total", "limit", "offset", "results"],
                },
            }
        },
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
                self.write_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "service": "audit-api",
                        "privacy_mode": self.server.privacy_mode,
                    },
                )
                return

            if parsed.path == "/openapi.json":
                self.write_json(HTTPStatus.OK, build_openapi_spec())
                return

            if parsed.path == "/docs":
                self.write_html(HTTPStatus.OK, swagger_ui_html("DeNotary Audit API", "/openapi.json"))
                return

            if parsed.path == "/v1/audit/search":
                query = parse_qs(parsed.query)
                payloads = select_requests(self.server.store, lambda item: self.matches_query(item, query))
                paged = apply_pagination(payloads, query)
                record_items = [redact_audit_record(build_audit_record(item), self.server.privacy_mode) for item in paged["items"]]
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
                self.write_json(HTTPStatus.OK, redact_audit_record(build_audit_record(payload), self.server.privacy_mode))
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
                self.write_json(HTTPStatus.OK, self.apply_privacy(build_audit_chain(payload)))
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
                self.write_json(HTTPStatus.OK, self.apply_privacy(build_audit_chain(payload)))
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
                self.write_json(HTTPStatus.OK, self.apply_privacy(build_audit_chain(payload)))
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
                self.write_json(HTTPStatus.OK, self.apply_privacy(build_audit_chain(payload)))
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
                self.write_json(HTTPStatus.OK, self.apply_privacy(build_audit_chain(payload)))
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def matches_query(self, payload: Dict[str, Any], query: Dict[str, List[str]]) -> bool:
        mode = query.get("mode", [None])[0]
        status = query.get("status", [None])[0]
        submitter = query.get("submitter", [None])[0]
        contract = query.get("contract", [None])[0]
        trust_state = query.get("trust_state", [None])[0]
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
        if trust_state and derive_trust_state(payload) != trust_state:
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

    def apply_privacy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "record": redact_audit_record(payload["record"], self.server.privacy_mode),
            "receipt": redact_receipt_payload(payload["receipt"], self.server.privacy_mode) if payload["receipt"] else None,
            "proof_chain": redact_proof_chain(payload["proof_chain"], self.server.privacy_mode),
        }

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

    def write_html(self, status: HTTPStatus, payload: str) -> None:
        encoded = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class AuditApiServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: Tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        store: FinalityStoreBase,
        privacy_mode: str = "full",
    ):
        super().__init__(server_address, handler)
        self.store = store
        self.privacy_mode = require_privacy_mode(privacy_mode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeNotary audit API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8083)
    parser.add_argument("--state-backend", default="sqlite")
    parser.add_argument("--state-file", default="runtime/finality-state.json")
    parser.add_argument("--state-db", default="runtime/finality-state.sqlite3")
    parser.add_argument("--privacy-mode", default="full", choices=["full", "public"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = build_finality_store(
        state_backend=args.state_backend,
        state_file=args.state_file,
        state_db=args.state_db,
    )
    server = AuditApiServer((args.host, args.port), AuditApiHandler, store, args.privacy_mode)
    print(f"Audit API listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
