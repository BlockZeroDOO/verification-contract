from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from finality_store import build_finality_store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate DeNotary finality state between backends.")
    parser.add_argument("--source-backend", required=True, choices=["file", "sqlite"])
    parser.add_argument("--source-file", default="runtime/finality-state.json")
    parser.add_argument("--source-db", default="runtime/finality-state.sqlite3")
    parser.add_argument("--target-backend", required=True, choices=["file", "sqlite"])
    parser.add_argument("--target-file", default="runtime/finality-state.migrated.json")
    parser.add_argument("--target-db", default="runtime/finality-state.migrated.sqlite3")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = build_finality_store(
        state_backend=args.source_backend,
        state_file=args.source_file,
        state_db=args.source_db,
    )
    payload = source.export_state()
    request_count = len(payload.get("requests", {}))

    if args.dry_run:
        print(
            json.dumps(
                {
                    "source_backend": args.source_backend,
                    "target_backend": args.target_backend,
                    "request_count": request_count,
                },
                indent=2,
            )
        )
        return 0

    target = build_finality_store(
        state_backend=args.target_backend,
        state_file=args.target_file,
        state_db=args.target_db,
    )
    target.import_state(payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "source_backend": args.source_backend,
                "target_backend": args.target_backend,
                "request_count": request_count,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
