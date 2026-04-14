# DeNotary Security Hardening

## Purpose

This document records the current hardening work for stage 9 and the controls already enforced in the repository.

## Current hardening goals

- prevent replay and conflicting re-registration paths
- tighten deterministic input validation
- reduce metadata leakage in default service responses
- make request and anchor identities safer to consume downstream

## Implemented controls

### On-chain idempotency and lifecycle controls

Already enforced in `verification`:

- duplicate single requests are rejected by deterministic request keys
- duplicate batch requests are rejected by deterministic request keys
- business lifecycle transitions are explicit, not generic
- no generic `setstatus` mutation path exists
- supersede flow requires a valid active successor
- finality is not mixed into on-chain business status

### Ingress API controls

Implemented in [services/ingress_api.py](/c:/projects/verification-contract/services/ingress_api.py:1):

- request body size limit
- maximum `external_ref` length
- maximum `external_leaf_ref` length
- maximum batch size
- maximum canonicalized material size
- Antelope account-name validation for `submitter`
- rejection of `null` payloads
- rejection of control characters in external references

Default response behavior is now safer:

- single responses do not return `canonical_form` unless `include_debug_material=true`
- batch responses do not return raw manifest and per-leaf canonical material unless `include_debug_material=true`

This keeps hashes and prepared actions available by default while reducing accidental raw-data exposure.

### Finality watcher controls

Implemented in [services/finality_watcher.py](/c:/projects/verification-contract/services/finality_watcher.py:1):

- request body size limit
- strict `request_id` validation as 64-char hex
- strict `tx_id` validation as 64-char hex
- limited-character validation for `trace_id`
- Antelope account-name validation for `submitter` and `contract`
- shape validation for anchor metadata
- positive integer enforcement for `block_num`, `commitment_id`, `batch_id`, `leaf_count`

Conflict-prevention rules:

- `register` is idempotent for identical requests
- `register` rejects conflicting reuse of an existing `request_id`
- `included` rejects attempts to change an already recorded `tx_id`
- `included` rejects attempts to change an already recorded `block_num`
- `anchor` rejects attempts to overwrite existing anchor IDs or hashes with different values
- finalized requests do not regress back to `included`

### Audit API controls

The current Audit API remains read-only and supports:

- bounded pagination
- search by request, tx, external ref, commitment ID, and batch ID
- optional `jsonl` export for downstream processing

The Audit API currently returns hashes and anchor metadata only. It does not expose raw source payloads.

## Remaining hardening work

Still recommended before rollout:

- add service-level auth or trusted network boundary for watcher mutation endpoints
- integrate direct indexed reads from on-chain tables instead of file-only state
- add negative integration tests for all hardening constraints
- review whether `external_ref` should support optional salted or HMAC-derived modes
- add explicit failure-state handling for rejected or dropped transactions
- add operational alerting for stuck requests and finality lag

## Related documents

- [docs/denotary-l1-development-plan.md](/c:/projects/verification-contract/docs/denotary-l1-development-plan.md:1)
- [docs/denotary-l1-test-matrix.md](/c:/projects/verification-contract/docs/denotary-l1-test-matrix.md:1)
- [docs/denotary-ingress-api.md](/c:/projects/verification-contract/docs/denotary-ingress-api.md:1)
- [docs/denotary-finality-services.md](/c:/projects/verification-contract/docs/denotary-finality-services.md:1)
