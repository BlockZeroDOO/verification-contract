from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from finality_store import FinalityStore
from openapi_docs import swagger_ui_html


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def derive_trust_state(payload: Dict[str, Any]) -> str:
    status = payload.get("status")
    inclusion_verified = payload.get("inclusion_verified", False)

    if status == "failed":
        return "failed"
    if status == "finalized":
        return "finalized_verified" if inclusion_verified else "finalized_unverified"
    if status == "included":
        return "included_verified" if inclusion_verified else "included_unverified"
    if status == "submitted":
        return "submitted"
    return "unknown"


def receipt_available(payload: Dict[str, Any]) -> bool:
    return payload.get("status") == "finalized" and payload.get("inclusion_verified", False)


def build_openapi_spec() -> Dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "DeNotary Receipt Service",
            "version": "1.0.0",
            "description": "Public receipt surface for finalized and inclusion-verified DeNotary requests.",
        },
        "servers": [{"url": "http://127.0.0.1:8082", "description": "Local default"}],
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
            "/v1/receipts/{request_id}": {
                "get": {
                    "summary": "Fetch receipt by request ID",
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
                            "description": "Receipt is available",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "oneOf": [
                                            {"$ref": "#/components/schemas/SingleReceipt"},
                                            {"$ref": "#/components/schemas/BatchReceipt"},
                                        ]
                                    }
                                }
                            },
                        },
                        "404": {"description": "Request not found"},
                        "409": {
                            "description": "Receipt not yet available",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ReceiptUnavailable"}
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
                        "service": {"type": "string", "example": "receipt-service"},
                    },
                    "required": ["status", "service"],
                },
                "ReceiptBase": {
                    "type": "object",
                    "properties": {
                        "issued_at": {"type": "string", "format": "date-time"},
                        "request_id": {"type": "string"},
                        "trace_id": {"type": "string"},
                        "mode": {"type": "string"},
                        "submitter": {"type": "string"},
                        "contract": {"type": "string"},
                        "tx_id": {"type": "string"},
                        "block_num": {"type": "integer"},
                        "finality_flag": {"type": "boolean"},
                        "finalized_at": {"type": "string", "format": "date-time"},
                        "trust_state": {"type": "string"},
                        "receipt_available": {"type": "boolean"},
                        "inclusion_verified": {"type": "boolean"},
                    },
                    "required": [
                        "issued_at",
                        "request_id",
                        "trace_id",
                        "mode",
                        "submitter",
                        "contract",
                        "tx_id",
                        "block_num",
                        "finality_flag",
                        "finalized_at",
                        "trust_state",
                        "receipt_available",
                        "inclusion_verified",
                    ],
                },
                "SingleReceipt": {
                    "allOf": [
                        {"$ref": "#/components/schemas/ReceiptBase"},
                        {
                            "type": "object",
                            "properties": {
                                "object_hash": {"type": "string"},
                                "external_ref_hash": {"type": "string"},
                            },
                            "required": ["object_hash", "external_ref_hash"],
                        },
                    ]
                },
                "BatchReceipt": {
                    "allOf": [
                        {"$ref": "#/components/schemas/ReceiptBase"},
                        {
                            "type": "object",
                            "properties": {
                                "root_hash": {"type": "string"},
                                "manifest_hash": {"type": "string"},
                                "external_ref_hash": {"type": "string"},
                                "leaf_count": {"type": "integer"},
                            },
                            "required": ["root_hash", "manifest_hash", "external_ref_hash", "leaf_count"],
                        },
                    ]
                },
                "ReceiptUnavailable": {
                    "type": "object",
                    "properties": {
                        "request_id": {"type": "string"},
                        "status": {"type": "string"},
                        "trust_state": {"type": "string"},
                        "receipt_available": {"type": "boolean"},
                        "inclusion_verified": {"type": "boolean"},
                        "error": {"type": "string"},
                        "failed_at": {"type": "string", "format": "date-time"},
                        "failure_reason": {"type": "string"},
                        "inclusion_verification_error": {"type": "string"},
                    },
                    "required": [
                        "request_id",
                        "status",
                        "trust_state",
                        "receipt_available",
                        "inclusion_verified",
                        "error",
                    ],
                },
            }
        },
    }


def build_single_receipt(payload: Dict[str, Any]) -> Dict[str, Any]:
    anchor = payload["anchor"]
    return {
        "issued_at": iso_now(),
        "request_id": payload["request_id"],
        "trace_id": payload["trace_id"],
        "mode": "single",
        "submitter": payload["submitter"],
        "contract": payload["contract"],
        "object_hash": anchor["object_hash"],
        "external_ref_hash": anchor["external_ref_hash"],
        "tx_id": payload["tx_id"],
        "block_num": payload["block_num"],
        "finality_flag": True,
        "finalized_at": payload["finalized_at"],
        "trust_state": derive_trust_state(payload),
        "receipt_available": True,
        "inclusion_verified": payload.get("inclusion_verified", False),
        "inclusion_verified_at": payload.get("inclusion_verified_at"),
        "verified_action": payload.get("verified_action"),
        "chain_state": payload.get("chain_state", {}),
    }


def build_batch_receipt(payload: Dict[str, Any]) -> Dict[str, Any]:
    anchor = payload["anchor"]
    return {
        "issued_at": iso_now(),
        "request_id": payload["request_id"],
        "trace_id": payload["trace_id"],
        "mode": "batch",
        "submitter": payload["submitter"],
        "contract": payload["contract"],
        "root_hash": anchor["root_hash"],
        "manifest_hash": anchor["manifest_hash"],
        "external_ref_hash": anchor["external_ref_hash"],
        "leaf_count": anchor["leaf_count"],
        "tx_id": payload["tx_id"],
        "block_num": payload["block_num"],
        "finality_flag": True,
        "finalized_at": payload["finalized_at"],
        "trust_state": derive_trust_state(payload),
        "receipt_available": True,
        "inclusion_verified": payload.get("inclusion_verified", False),
        "inclusion_verified_at": payload.get("inclusion_verified_at"),
        "verified_action": payload.get("verified_action"),
        "chain_state": payload.get("chain_state", {}),
    }


class ReceiptServiceHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryReceiptService/0.1"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.write_json(HTTPStatus.OK, {"status": "ok", "service": "receipt-service"})
            return

        if self.path == "/openapi.json":
            self.write_json(HTTPStatus.OK, build_openapi_spec())
            return

        if self.path == "/docs":
            self.write_html(HTTPStatus.OK, swagger_ui_html("DeNotary Receipt Service", "/openapi.json"))
            return

        prefix = "/v1/receipts/"
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

            if not receipt_available(payload):
                response = {
                    "request_id": request_id,
                    "status": payload.get("status"),
                    "trust_state": derive_trust_state(payload),
                    "receipt_available": False,
                    "inclusion_verified": payload.get("inclusion_verified", False),
                }
                if payload.get("status") == "failed":
                    response.update(
                        {
                            "error": "receipt is not available for failed request",
                            "failed_at": payload.get("failed_at"),
                            "failure_reason": payload.get("failure_reason"),
                        }
                    )
                elif payload.get("status") == "finalized":
                    response["error"] = "receipt is not available before inclusion verification"
                    response["inclusion_verification_error"] = payload.get("inclusion_verification_error")
                else:
                    response["error"] = "receipt is not available before finality"
                    response["inclusion_verification_error"] = payload.get("inclusion_verification_error")

                self.write_json(HTTPStatus.CONFLICT, response)
                return

            mode = payload.get("mode")
            if mode == "single":
                receipt = build_single_receipt(payload)
            elif mode == "batch":
                receipt = build_batch_receipt(payload)
            else:
                self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "unsupported request mode"})
                return

            self.write_json(HTTPStatus.OK, receipt)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

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


class ReceiptServiceServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], store: FinalityStore):
        super().__init__(server_address, handler)
        self.store = store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeNotary receipt service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8082)
    parser.add_argument("--state-file", default="runtime/finality-state.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = FinalityStore(args.state_file)
    server = ReceiptServiceServer((args.host, args.port), ReceiptServiceHandler, store)
    print(f"Receipt service listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
