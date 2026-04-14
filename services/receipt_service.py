from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from finality_store import FinalityStore


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        "chain_state": payload.get("chain_state", {}),
    }


class ReceiptServiceHandler(BaseHTTPRequestHandler):
    server_version = "DeNotaryReceiptService/0.1"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.write_json(HTTPStatus.OK, {"status": "ok", "service": "receipt-service"})
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

            if payload.get("status") != "finalized":
                self.write_json(
                    HTTPStatus.CONFLICT,
                    {
                        "error": "receipt is not available before finality",
                        "request_id": request_id,
                        "status": payload.get("status"),
                    },
                )
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
