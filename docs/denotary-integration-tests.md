# DeNotary Integration Tests

## Purpose

This document describes the current integration-testing baseline for the DeNotary services layer and its adjacent live-chain follow-up.

Implementation:

- [tests/test_service_integration.py](/c:/projects/verification-contract/tests/test_service_integration.py:1)
- [scripts/run-integration-tests.sh](/c:/projects/verification-contract/scripts/run-integration-tests.sh:1)
- [scripts/run-integration-tests.ps1](/c:/projects/verification-contract/scripts/run-integration-tests.ps1:1)
- [tests/live_chain_integration.py](/c:/projects/verification-contract/tests/live_chain_integration.py:1)
- [scripts/run-live-chain-integration.sh](/c:/projects/verification-contract/scripts/run-live-chain-integration.sh:1)
- [scripts/run-live-chain-integration.ps1](/c:/projects/verification-contract/scripts/run-live-chain-integration.ps1:1)

## Current coverage

The integration suite starts local in-process servers for:

- `Ingress API`
- `Finality Watcher`
- `Receipt Service`
- `Audit API`
- a mock chain RPC for `/v1/chain/get_info`

## Covered scenarios

### Ingress behavior

- single prepare redacts raw canonical material by default
- batch prepare redacts raw manifest material by default

### Single end-to-end pipeline

- prepare single request
- register request in watcher
- attach `commitment_id`
- attach inclusion metadata
- poll until irreversible finality
- fetch finalized receipt
- verify audit lookup by `commitment_id`

### Batch end-to-end pipeline

- prepare batch request
- register batch request
- attach `batch_id`
- attach inclusion metadata
- poll until irreversible finality
- verify audit lookup by `batch_id`

### Hardening integration

- conflicting re-registration of the same `request_id` is rejected

## What this suite does not cover yet

- real chain broadcasting
- real on-chain table reads
- real contract execution against a live Antelope node
- batch inclusion-proof generation and verification
- tx failure and dropped-tx recovery paths

Those items are now partially addressed by the separate live-chain suite documented in:

- [docs/denotary-live-chain-integration.md](/c:/projects/verification-contract/docs/denotary-live-chain-integration.md:1)

## Run

Linux / WSL:

```bash
./scripts/run-integration-tests.sh
```

PowerShell:

```powershell
./scripts/run-integration-tests.ps1
```

## Live-chain follow-up

When you want a real-chain end-to-end check instead of the in-process mock RPC, run:

Linux / WSL:

```bash
./scripts/run-live-chain-integration.sh --owner-account verification --submitter-account someuser
```

PowerShell:

```powershell
./scripts/run-live-chain-integration.ps1 --owner-account verification --submitter-account someuser
```

The live-chain suite:

- starts the local DeNotary services in-process
- prepares requests through `Ingress API`
- broadcasts real `verification` actions with `cleos`
- waits for irreversible finality against the target RPC
- verifies `Receipt Service` and `Audit API` against actual `tx_id`, `commitment_id`, and `batch_id`

Current hardening coverage in integration tests also includes:

- watcher mutation auth when a shared token is configured
- explicit failed-request handling in receipt and audit reads
