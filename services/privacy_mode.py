from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

SUPPORTED_PRIVACY_MODES = {"full", "public"}


def require_privacy_mode(value: str | None, default: str = "full") -> str:
    mode = str(value or default).strip().lower()
    if mode not in SUPPORTED_PRIVACY_MODES:
        raise ValueError(f"unsupported privacy mode: {mode}")
    return mode


def redact_receipt_payload(payload: Dict[str, Any], privacy_mode: str) -> Dict[str, Any]:
    if require_privacy_mode(privacy_mode) == "full":
        return deepcopy(payload)

    sanitized = deepcopy(payload)
    for key in (
        "trace_id",
        "submitter",
        "tx_id",
        "block_num",
        "external_ref_hash",
        "inclusion_verified_at",
        "verified_action",
        "verification_state",
        "chain_state",
    ):
        sanitized.pop(key, None)
    return sanitized


def redact_receipt_unavailable_payload(payload: Dict[str, Any], privacy_mode: str) -> Dict[str, Any]:
    if require_privacy_mode(privacy_mode) == "full":
        return deepcopy(payload)

    sanitized = deepcopy(payload)
    sanitized.pop("failed_at", None)
    sanitized.pop("failure_reason", None)
    sanitized.pop("inclusion_verification_error", None)
    return sanitized


def redact_audit_record(payload: Dict[str, Any], privacy_mode: str) -> Dict[str, Any]:
    if require_privacy_mode(privacy_mode) == "full":
        return deepcopy(payload)

    sanitized = deepcopy(payload)
    for key in (
        "trace_id",
        "submitter",
        "commitment_id",
        "batch_id",
        "external_ref_hash",
        "tx_id",
        "block_num",
        "failure_reason",
        "failure_details",
        "inclusion_verified_at",
        "inclusion_verification_error",
        "verification_state",
        "verified_action",
        "anchor",
        "chain_state",
    ):
        sanitized.pop(key, None)
    return sanitized


def redact_proof_chain(payload: List[Dict[str, Any]], privacy_mode: str) -> List[Dict[str, Any]]:
    if require_privacy_mode(privacy_mode) == "full":
        return deepcopy(payload)

    sanitized_chain = deepcopy(payload)
    for entry in sanitized_chain:
        stage = entry.get("stage")
        details = dict(entry.get("details", {}))
        if stage == "request_registered":
            details.pop("trace_id", None)
            details.pop("submitter", None)
        elif stage == "transaction_included":
            details = {
                "included": True,
            }
        elif stage == "transaction_verified":
            details.pop("verified_action", None)
            details.pop("verification_state", None)
            details.pop("verification_error", None)
        elif stage == "block_finalized":
            details.pop("head_block_num", None)
            details.pop("last_irreversible_block_num", None)
        entry["details"] = details
    return sanitized_chain
