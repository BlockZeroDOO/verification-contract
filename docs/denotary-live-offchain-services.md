# DeNotary Live Off-Chain Service Tests

## Purpose

This runbook covers the live test suite for the full off-chain service surface:

- `Ingress API`
- `Finality Watcher`
- `Receipt Service`
- `Audit API`

Unlike the smaller live-chain integration gate, this suite checks both:

- real single and batch reconciliation against a live chain
- service-level behavior such as auth, failed-request handling, audit search, and debug-material redaction

Implementation:

- [tests/live_offchain_services.py](/c:/projects/verification-contract/tests/live_offchain_services.py:1)
- [scripts/run-live-offchain-services.sh](/c:/projects/verification-contract/scripts/run-live-offchain-services.sh:1)
- [scripts/run-live-offchain-services.ps1](/c:/projects/verification-contract/scripts/run-live-offchain-services.ps1:1)

## Covered functionality

The suite verifies:

- `healthz` for all four off-chain services
- `Ingress API` single and batch preparation
- default redaction of debug material in ingress responses
- explicit debug-material responses with `include_debug_material=true`
- optional watcher auto-registration handoff from ingress
- ingress validation rejection for invalid payloads
- `Finality Watcher` auth enforcement when mutation token is enabled
- watcher provider-policy behavior for both `single-provider` and `quorum`
- idempotent watcher registration
- conflicting watcher re-registration rejection
- watcher request lookup by `request_id`
- watcher failed-request flow through `POST /v1/watch/<request_id>/failed`
- rejection of illegal `included` and `anchor` mutations after failure
- pending and failed receipt behavior
- finalized single receipt behavior
- finalized batch receipt behavior
- `Audit API` request lookup, chain lookup, and lookup by:
  - `external_ref_hash`
  - `tx_id`
  - `commitment_id`
  - `batch_id`
- `Audit API` search in both JSON and `jsonl` output modes
- watcher global poll endpoint
- real-chain finality for both single and batch requests
- live degraded-provider behavior where `quorum` intentionally remains `included_unverified`
- local restart/recovery behavior across watcher, receipt, and audit with shared `SQLite` state

## Prerequisites

- `cleos` is installed and available in `PATH`
- Python is available
- keys are imported for the `verification` governance account
- keys are imported for the submitter account
- the target `verification` contract is already deployed

Windows notes:

- `cleos.exe` must be available in `PATH`
- the PowerShell launcher supports both `.venv\\Scripts\\python.exe` and the standard Windows `py -3` launcher
- run the suite from PowerShell with the provided `.ps1` wrapper

## deNotary.io run

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/run-live-offchain-services.sh \
  --owner-account "${OWNER_ACCOUNT}" \
  --submitter-account "${SUBMITTER_ACCOUNT}"
```

Default network values:

- `rpc-url=https://history.denotary.io`
- `expected-chain-id=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`
- `network-label=deNotary.io`

## Jungle4 run

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/run-live-offchain-services.sh \
  --rpc-url https://jungle4.api.eosnation.io \
  --expected-chain-id 73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d \
  --network-label Jungle4 \
  --owner-account "${OWNER_ACCOUNT}" \
  --submitter-account "${SUBMITTER_ACCOUNT}"
```

## PowerShell run

```powershell
./scripts/run-live-offchain-services.ps1 --owner-account verification --submitter-account youruser
```

PowerShell run with full artifact dump:

```powershell
./scripts/run-live-offchain-services.ps1 `
  --rpc-url https://jungle4.api.eosnation.io `
  --expected-chain-id 73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d `
  --network-label Jungle4 `
  --owner-account verification `
  --submitter-account vadim1111111 `
  --dump-dir runtime/live-offchain-logs
```

## Useful options

Available options:

- `--rpc-url`
- `--expected-chain-id`
- `--skip-chain-id-check`
- `--network-label`
- `--verification-account`
- `--owner-account`
- `--submitter-account`
- `--watcher-auth-token`
- `--wait-timeout-sec`
- `--poll-interval-sec`
- `--dump-dir`
- `--print-json-events`
- `--use-external-services`
- `--ingress-base-url`
- `--watcher-base-url`
- `--receipt-base-url`
- `--audit-base-url`

## Full logs

If `--dump-dir` is provided, the suite writes one JSON file per major step plus `summary.json`.

Typical contents:

- ingress requests and responses
- watcher register, anchor, included, failed, and poll responses
- receipts before and after finality
- audit request, chain, lookup, search, and `jsonl` responses
- live transaction metadata for `submit`, `submitroot`, `linkmanifest`, and `closebatch`
- rows fetched from on-chain `commitments` and `batches`

If `--print-json-events` is also enabled, the same structured events are printed directly to stdout.

## Notes

- this suite is intentionally broader than [docs/denotary-live-chain-integration.md](/c:/projects/verification-contract/docs/denotary-live-chain-integration.md:1)
- use `run-live-chain-integration` as the compact end-to-end gate
- use `run-live-offchain-services` when you want service-surface confidence before rollout or environment changes
- when `--use-external-services` is set, the suite targets an already running Docker Compose stack
- this external-services path now validates both normal finalized flow and a live degraded-provider `quorum` scenario
- restart/recovery validation runs only in the local in-process stack because it needs direct lifecycle control over services
