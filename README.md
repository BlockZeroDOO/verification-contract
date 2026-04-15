# DeNotary Contracts And Services

This repository contains the current DeNotary MVP baseline:

- `verification`: the main Antelope on-chain registry and anchoring contract
- `dfs`: DFS-related economic and settlement scaffold
- off-chain baseline services for ingestion, finality, receipts, and audit reads

## Current status

Implemented roadmap stages:

- Stage 0: discovery, ADRs, backlog, and test matrix
- Stage 1: contract-core refactor and clean deployment baseline
- Stage 2: `KYC`, `Schema`, and `Policy` registries
- Stage 3: single-record commitment flow
- Stage 4: batch anchoring flow
- Stage 5: lifecycle tracking for commitments and batches
- Stage 6: deterministic ingress API baseline
- Stage 7: finality watcher and receipt service baseline
- Stage 8: audit API baseline

Current next step:

- Stage 9: security hardening
- Stage 11: live-chain integration depth and rollout gates

## `verification` scope

The `verification` contract currently covers:

- KYC access control
- schema registry
- policy registry
- single-record anchoring
- batch anchoring
- business lifecycle tracking for commitments and batches
- explicit disablement of the legacy paid proof path

## On-chain tables

Core tables:

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`
- `counters`

Legacy/payment tables:

- `proofs`
- `paytokens`

## On-chain actions

Registry governance:

- `issuekyc(name account, uint8_t level, string provider, string jurisdiction, time_point_sec expires_at)`
- `renewkyc(name account, time_point_sec expires_at)`
- `revokekyc(name account)`
- `suspendkyc(name account)`
- `addschema(uint64_t id, string version, checksum256 canonicalization_hash, checksum256 hash_policy)`
- `updateschema(uint64_t id, string version, checksum256 canonicalization_hash, checksum256 hash_policy)`
- `deprecate(uint64_t id)`
- `setpolicy(uint64_t id, bool allow_single, bool allow_batch, bool require_kyc, uint8_t min_kyc_level, bool active)`
- `enablezk(uint64_t id)`
- `disablezk(uint64_t id)`

Anchoring core:

- `submit(name submitter, uint64_t schema_id, uint64_t policy_id, checksum256 object_hash, checksum256 external_ref)`
- `supersede(uint64_t id, uint64_t successor_id)`
- `revokecmmt(uint64_t id)`
- `expirecmmt(uint64_t id)`
- `submitroot(name submitter, uint64_t schema_id, uint64_t policy_id, checksum256 root_hash, uint32_t leaf_count, checksum256 external_ref)`
- `linkmanifest(uint64_t id, checksum256 manifest_hash)`
- `closebatch(uint64_t id)`

Legacy compatibility actions retained only as disabled stubs:

- `record(name submitter, checksum256 object_hash, string canonicalization_profile, string client_reference)`
- `setpaytoken(name token_contract, asset price)`
- `rmpaytoken(name token_contract, symbol token_symbol)`

Operational action:

- `withdraw(name token_contract, name to, asset quantity, string memo)`

## Model notes

- `commitments.status` and `batches.status` are business statuses, not finality statuses
- irreversible finality is intentionally kept off-chain
- `supersede(...)` links the original commitment to a successor through `superseded_by`
- batch closure requires a linked `manifest_hash`
- batch proof material remains off-chain; on-chain stores `root_hash`, `manifest_hash`, and batch metadata
- the legacy `proofs` and proof-payment path are disabled for production use

## `dfs` scope

The `dfs` contract currently covers:

- node registry
- stake lifecycle
- accepted token configuration
- price offers
- quote-based storage payment intake
- settlement and claimable balances

Key DFS actions:

- `regnode(...)`
- `updatenode(...)`
- `requestunstk(...)`
- `withdrawstk(...)`
- `setprice(...)`
- `settoken(...)`
- `setpolicy(...)`
- `mkstorquote(string payment_reference, name source_account, string manifest_hash, name token_contract, asset quantity, time_point_sec expires_at)`
- `cancelquote(string payment_reference)`
- `settle(...)`
- `claimrevenue(...)`

## Off-chain services

### Ingress API

- [services/ingress_api.py](/c:/projects/verification-contract/services/ingress_api.py:1)
- [docs/denotary-ingress-api.md](/c:/projects/verification-contract/docs/denotary-ingress-api.md:1)

Capabilities:

- deterministic canonicalization profile `json-sorted-v1`
- single request preparation for `submit`
- batch request preparation for `submitroot`
- generated `trace_id`, `request_id`, and content hashes

### Finality Watcher

- [services/finality_watcher.py](/c:/projects/verification-contract/services/finality_watcher.py:1)
- [docs/denotary-finality-services.md](/c:/projects/verification-contract/docs/denotary-finality-services.md:1)

Capabilities:

- register a request for watching
- attach `tx_id` and `block_num` after inclusion
- attach `commitment_id` or `batch_id` into anchor metadata
- require a shared auth token on mutation endpoints by default
- explicitly mark requests as failed when broadcasting or reconciliation fails
- verify inclusion against chain history before finalized trust is granted
- poll chain finality until irreversible
- expose explicit trust states across `submitted`, `included_unverified`, `included_verified`, `finalized_verified`, and `failed`

### Receipt Service

- [services/receipt_service.py](/c:/projects/verification-contract/services/receipt_service.py:1)
- [docs/denotary-finality-services.md](/c:/projects/verification-contract/docs/denotary-finality-services.md:1)

Capabilities:

- issue receipts only for `finalized_verified` requests
- reject receipt reads before finality or before inclusion verification
- expose `trust_state` and `receipt_available` for non-receiptable requests
- surface failure metadata for explicitly failed requests

### Audit API

- [services/audit_api.py](/c:/projects/verification-contract/services/audit_api.py:1)
- [docs/denotary-audit-api.md](/c:/projects/verification-contract/docs/denotary-audit-api.md:1)

Capabilities:

- lookup by `request_id`
- lookup by `external_ref_hash`
- lookup by `tx_id`
- lookup by `commitment_id`
- lookup by `batch_id`
- expose `trust_state` and `receipt_available` on audit records
- paginated search and `jsonl` export
- read path returning `record + receipt + proof_chain`

## Build

Linux / WSL:

```bash
./scripts/build-testnet.sh
./scripts/build-release.sh
```

PowerShell:

```powershell
./scripts/build-testnet.ps1
./scripts/build-release.ps1
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## Smoke test

On-chain smoke coverage:

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-dfs.sh](/c:/projects/verification-contract/scripts/smoke-test-dfs.sh:1)
- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)

Typical run:

```bash
export RPC_URL=https://your-rpc
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export SUBMITTER_ACCOUNT=someuser
./scripts/smoke-test-onchain.sh
```

The smoke test covers:

- KYC issuance and renewal
- schema and policy setup
- single commitment submit
- duplicate single rejection
- supersede, revoke, and expire transitions
- batch submit
- duplicate batch rejection
- manifest linking and close guards

DFS quote smoke coverage:

```bash
export DFS_SETTLEMENT_ACCOUNT=settleauth1
export DFS_PAYER_ACCOUNT=someuser
./scripts/smoke-test-dfs.sh
```

## Integration tests

Local mock-chain integration baseline:

- [tests/test_service_integration.py](/c:/projects/verification-contract/tests/test_service_integration.py:1)
- [scripts/run-integration-tests.sh](/c:/projects/verification-contract/scripts/run-integration-tests.sh:1)
- [docs/denotary-integration-tests.md](/c:/projects/verification-contract/docs/denotary-integration-tests.md:1)

Live-chain integration baseline:

- [tests/live_chain_integration.py](/c:/projects/verification-contract/tests/live_chain_integration.py:1)
- [scripts/run-live-chain-integration.sh](/c:/projects/verification-contract/scripts/run-live-chain-integration.sh:1)
- [scripts/run-live-chain-integration.ps1](/c:/projects/verification-contract/scripts/run-live-chain-integration.ps1:1)
- [docs/denotary-live-chain-integration.md](/c:/projects/verification-contract/docs/denotary-live-chain-integration.md:1)

Live off-chain service coverage:

- [tests/live_offchain_services.py](/c:/projects/verification-contract/tests/live_offchain_services.py:1)
- [scripts/run-live-offchain-services.sh](/c:/projects/verification-contract/scripts/run-live-offchain-services.sh:1)
- [scripts/run-live-offchain-services.ps1](/c:/projects/verification-contract/scripts/run-live-offchain-services.ps1:1)
- [docs/denotary-live-offchain-services.md](/c:/projects/verification-contract/docs/denotary-live-offchain-services.md:1)

Example with full artifact dump:

```powershell
./scripts/run-live-offchain-services.ps1 --owner-account verification --submitter-account vadim1111111 --dump-dir runtime/live-offchain-logs
```

Rollout dry-run baseline:

- [scripts/run-rollout-dry-run.sh](/c:/projects/verification-contract/scripts/run-rollout-dry-run.sh:1)
- [scripts/run-rollout-dry-run.ps1](/c:/projects/verification-contract/scripts/run-rollout-dry-run.ps1:1)
- [docs/denotary-rollout-dry-run.md](/c:/projects/verification-contract/docs/denotary-rollout-dry-run.md:1)

Typical `deNotary.io` run:

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=someuser
./scripts/run-live-chain-integration.sh --owner-account "${OWNER_ACCOUNT}" --submitter-account "${SUBMITTER_ACCOUNT}"
```

Typical Jungle4 run:

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=someuser
./scripts/run-live-chain-integration.sh \
  --rpc-url https://jungle4.api.eosnation.io \
  --expected-chain-id 73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d \
  --network-label Jungle4 \
  --owner-account "${OWNER_ACCOUNT}" \
  --submitter-account "${SUBMITTER_ACCOUNT}"
```

This live suite:

- starts local `Ingress API`, `Finality Watcher`, `Receipt Service`, and `Audit API`
- prepares real single and batch requests through the local services
- pushes actual `submit`, `submitroot`, `linkmanifest`, and `closebatch` transactions with `cleos`
- waits for irreversible finality on the live chain
- verifies finalized receipts and audit lookups by `tx_id`, `commitment_id`, `batch_id`, and `external_ref_hash`

## Documentation map

Architecture and roadmap:

- [docs/denotary-l1-development-plan.md](/c:/projects/verification-contract/docs/denotary-l1-development-plan.md:1)
- [docs/denotary-l1-discovery.md](/c:/projects/verification-contract/docs/denotary-l1-discovery.md:1)
- [docs/denotary-l1-contract-core.md](/c:/projects/verification-contract/docs/denotary-l1-contract-core.md:1)
- [docs/denotary-l1-backlog.md](/c:/projects/verification-contract/docs/denotary-l1-backlog.md:1)
- [docs/denotary-l1-test-matrix.md](/c:/projects/verification-contract/docs/denotary-l1-test-matrix.md:1)

Service docs:

- [docs/denotary-deploy.md](/c:/projects/verification-contract/docs/denotary-deploy.md:1)
- [docs/denotary-offchain-deploy.md](/c:/projects/verification-contract/docs/denotary-offchain-deploy.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [docs/denotary-ingress-api.md](/c:/projects/verification-contract/docs/denotary-ingress-api.md:1)
- [docs/denotary-finality-services.md](/c:/projects/verification-contract/docs/denotary-finality-services.md:1)
- [docs/denotary-audit-api.md](/c:/projects/verification-contract/docs/denotary-audit-api.md:1)
- [docs/denotary-integration-tests.md](/c:/projects/verification-contract/docs/denotary-integration-tests.md:1)
- [docs/denotary-live-chain-integration.md](/c:/projects/verification-contract/docs/denotary-live-chain-integration.md:1)
- [docs/denotary-live-offchain-services.md](/c:/projects/verification-contract/docs/denotary-live-offchain-services.md:1)
- [docs/denotary-rollout-dry-run.md](/c:/projects/verification-contract/docs/denotary-rollout-dry-run.md:1)
- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- [docs/denotary-security-hardening.md](/c:/projects/verification-contract/docs/denotary-security-hardening.md:1)

Operational helpers:

- [config/offchain.env.example](/c:/projects/verification-contract/config/offchain.env.example:1)
- [config/offchain.compose.env.example](/c:/projects/verification-contract/config/offchain.compose.env.example:1)
- [Dockerfile.offchain](/c:/projects/verification-contract/Dockerfile.offchain:1)
- [docker-compose.offchain.yml](/c:/projects/verification-contract/docker-compose.offchain.yml:1)
- [scripts/run-offchain-service.sh](/c:/projects/verification-contract/scripts/run-offchain-service.sh:1)
- [scripts/offchain-stack.sh](/c:/projects/verification-contract/scripts/offchain-stack.sh:1)
- [scripts/offchain-healthcheck.sh](/c:/projects/verification-contract/scripts/offchain-healthcheck.sh:1)
- [deploy/systemd/denotary-ingress.service](/c:/projects/verification-contract/deploy/systemd/denotary-ingress.service:1)
- [deploy/systemd/denotary-finality-watcher.service](/c:/projects/verification-contract/deploy/systemd/denotary-finality-watcher.service:1)
- [deploy/systemd/denotary-receipt.service](/c:/projects/verification-contract/deploy/systemd/denotary-receipt.service:1)
- [deploy/systemd/denotary-audit.service](/c:/projects/verification-contract/deploy/systemd/denotary-audit.service:1)
- [docs/denotary-offchain-docker-compose.md](/c:/projects/verification-contract/docs/denotary-offchain-docker-compose.md:1)

ADRs:

- [docs/adr/0001-finality-model.md](/c:/projects/verification-contract/docs/adr/0001-finality-model.md:1)
- [docs/adr/0002-batch-proof-storage.md](/c:/projects/verification-contract/docs/adr/0002-batch-proof-storage.md:1)
- [docs/adr/0003-clean-deployment-cutover.md](/c:/projects/verification-contract/docs/adr/0003-clean-deployment-cutover.md:1)

## Notes

- `verification` is the current source of truth for the DeNotary on-chain model
- the primary network target is `deNotary.io`, with Jungle4 retained as an optional external testnet
- newer `denotary-*` docs and updated scripts should be preferred over older deployment notes that describe legacy flows

## License

This project is licensed under the MIT License. See `LICENSE`.
