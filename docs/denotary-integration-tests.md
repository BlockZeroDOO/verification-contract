# DeNotary Integration Tests

## Purpose

This document describes the current integration-testing baseline for the off-chain DeNotary pipeline.

Implementation:

- [tests/test_service_integration.py](/c:/projects/verification-contract/tests/test_service_integration.py:1)
- [scripts/run-integration-tests.sh](/c:/projects/verification-contract/scripts/run-integration-tests.sh:1)
- [scripts/run-integration-tests.ps1](/c:/projects/verification-contract/scripts/run-integration-tests.ps1:1)

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

## Run

Linux / WSL:

```bash
./scripts/run-integration-tests.sh
```

PowerShell:

```powershell
./scripts/run-integration-tests.ps1
```

## Next step

The natural follow-up after this baseline is:

- add live-chain integration tests for `verification`
- add finality failure-path tests
- connect integration assertions to rollout gates
