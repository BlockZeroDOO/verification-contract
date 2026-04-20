#!/usr/bin/env python3
"""Derive a verification hash from an auditor-supplied payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Derive object_hash, leaf_hash, or manifest_hash from a prepared auditor payload."
        )
    )
    parser.add_argument(
        "--kind",
        choices=("object", "leaf", "manifest"),
        required=True,
        help="Hash kind label for the output. The hashing algorithm is always SHA-256.",
    )
    parser.add_argument("--text", help="Literal UTF-8 text payload to hash.")
    parser.add_argument("--text-file", help="Path to a UTF-8 text file to hash.")
    parser.add_argument(
        "--json",
        help="Inline JSON payload to hash after stable canonical JSON serialization.",
    )
    parser.add_argument(
        "--json-file",
        help="Path to a JSON file to hash after stable canonical JSON serialization.",
    )
    parser.add_argument("--hex", help="Hex-encoded bytes to hash directly.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the result JSON.")
    return parser.parse_args()


def choose_input(args: argparse.Namespace) -> tuple[str, bytes, Any]:
    supplied = [
        ("text", args.text),
        ("text-file", args.text_file),
        ("json", args.json),
        ("json-file", args.json_file),
        ("hex", args.hex),
    ]
    used = [(name, value) for name, value in supplied if value is not None]
    if len(used) != 1:
        raise ValueError(
            "exactly one of --text, --text-file, --json, --json-file, or --hex must be supplied"
        )

    name, value = used[0]
    if name == "text":
        return name, value.encode("utf-8"), value
    if name == "text-file":
        text = Path(value).read_text(encoding="utf-8")
        return name, text.encode("utf-8"), {"path": value, "text_length": len(text)}
    if name == "json":
        parsed = json.loads(value)
        canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return name, canonical.encode("utf-8"), parsed
    if name == "json-file":
        parsed = json.loads(Path(value).read_text(encoding="utf-8"))
        canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return name, canonical.encode("utf-8"), {"path": value, "json": parsed}
    if name == "hex":
        normalized = value.lower()
        if len(normalized) % 2 != 0:
            raise ValueError("--hex must contain an even number of hex characters")
        try:
            payload_bytes = bytes.fromhex(normalized)
        except ValueError as exc:
            raise ValueError("--hex must contain valid hex") from exc
        return name, payload_bytes, {"hex_length": len(normalized)}
    raise ValueError(f"unsupported input type {name}")


def main() -> int:
    try:
        args = parse_args()
        input_type, payload_bytes, source_metadata = choose_input(args)
        digest = hashlib.sha256(payload_bytes).hexdigest()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    result = {
        "ok": True,
        "kind": args.kind,
        "algorithm": "sha256",
        "input_type": input_type,
        "payload_bytes": len(payload_bytes),
        "hash_hex": digest,
        "source": source_metadata,
        "notes": [
            "This helper hashes the auditor-supplied payload exactly as provided after the selected normalization step.",
            "It does not infer database canonicalization rules on its own.",
            "To match verif object_hash or batch leaf_hash, the auditor must use the same canonical payload shape as the submitter runtime.",
        ],
    }
    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
