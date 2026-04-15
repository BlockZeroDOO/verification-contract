# DeNotary L1 Development Plan

## Status Snapshot (2026-04-14)

Already implemented in this repository:

- Stage 0: discovery, ADRs, backlog, test matrix
- Stage 1: contract-core refactor and clean deployment baseline
- Stage 2: `KYC`, `Schema`, and `Policy` registries
- Stage 3: single-record commitment flow
- Stage 4: batch anchoring flow
- Stage 5: lifecycle tracking for commitments and batches
- Stage 6: deterministic ingress API baseline
- Stage 7: finality watcher and receipt service baseline
- Stage 8: audit API baseline

Current next step:

- Stage 9: security hardening in progress
- Stage 11 live-chain integration and rollout depth in progress

## Initial gap against TSD v2

The original gap between the legacy repository state and the target DeNotary model was:

- no `KYCRegistry`, `SchemaRegistry`, or `PolicyRegistry`
- no `CommitmentRegistry` or `BatchRegistry`
- no batch anchoring and Merkle-based flow
- no finality watcher, receipt service, or audit API
- legacy `verification.proofs` only covered paid proof insertion, not the full schema/policy/finality lifecycle

Most of that gap is now closed for the MVP baseline.

## MVP scope

Included in the current MVP track:

- `KYCRegistry`
- `SchemaRegistry`
- `PolicyRegistry`
- `CommitmentRegistry`
- `BatchRegistry`
- lifecycle tracking for commitments and batches
- `Ingress API` as an optional helper service
- direct client-side canonicalization and submission path
- canonicalization baseline
- `Finality Watcher`
- `Receipt Service`
- `Audit API`

Deferred from MVP:

- separate `ProofRegistry`
- ZKP flow
- fully indexed chain-native audit backend

## Architectural decisions

### Finality truth

- on-chain stores record data and business status
- off-chain tracks inclusion and finality
- receipts are issued only after irreversible finality

### Batch proof storage

- on-chain stores `root_hash`, `manifest_hash`, and batch metadata
- off-chain stores the manifest and future inclusion-proof material

### Deployment model

- current plan assumes fresh deployment on clean accounts
- no migration from legacy `proofs` is required for the DeNotary rollout

### Contract boundary

- current core remains inside a single `verification` contract
- `dfs` is kept separate and not coupled into the DeNotary MVP flow

## Implemented stages

### Stage 0. Discovery and decomposition

Delivered:

- discovery pack
- ADRs
- backlog
- test matrix

Artifacts:

- [docs/denotary-l1-discovery.md](/c:/projects/verification-contract/docs/denotary-l1-discovery.md:1)
- [docs/denotary-l1-backlog.md](/c:/projects/verification-contract/docs/denotary-l1-backlog.md:1)
- [docs/denotary-l1-test-matrix.md](/c:/projects/verification-contract/docs/denotary-l1-test-matrix.md:1)

### Stage 1. Contract core baseline

Delivered:

- domain model baseline
- table and action matrix
- fresh deploy assumption

Artifacts:

- [docs/denotary-l1-contract-core.md](/c:/projects/verification-contract/docs/denotary-l1-contract-core.md:1)
- [docs/adr/0003-clean-deployment-cutover.md](/c:/projects/verification-contract/docs/adr/0003-clean-deployment-cutover.md:1)

### Stage 2. Access registries

Delivered:

- `issuekyc`, `renewkyc`, `revokekyc`, `suspendkyc`
- `addschema`, `updateschema`, `deprecate`
- `setpolicy`, `enablezk`, `disablezk`

### Stage 3. Single-record flow

Delivered:

- `commitments` table
- `submit`
- `supersede`
- `revokecmmt`
- `expirecmmt`
- duplicate protection through deterministic request keys

### Stage 4. Batch flow

Delivered:

- `batches` table
- `submitroot`
- `linkmanifest`
- `closebatch`

### Stage 5. Lifecycle tracking

Delivered:

- explicit lifecycle timestamps
- `superseded_by` linkage
- clearer separation between business lifecycle and finality lifecycle

### Stage 6. Canonicalization baseline and optional Ingress API

Delivered:

- deterministic canonicalization profile `json-sorted-v1`
- `POST /v1/single/prepare`
- `POST /v1/batch/prepare`
- generated `trace_id`, `request_id`, hashes, root, and manifest
- architectural support for direct client-side preparation as an equivalent mode

Artifact:

- [docs/denotary-ingress-api.md](/c:/projects/verification-contract/docs/denotary-ingress-api.md:1)
- [docs/adr/0004-direct-client-canonicalization.md](/c:/projects/verification-contract/docs/adr/0004-direct-client-canonicalization.md:1)

### Stage 7. Finality watcher and receipts

Delivered:

- request registration
- inclusion updates with `tx_id` and `block_num`
- finality polling against `/v1/chain/get_info`
- finalized single and batch receipts

Artifact:

- [docs/denotary-finality-services.md](/c:/projects/verification-contract/docs/denotary-finality-services.md:1)

### Stage 8. Audit API

Delivered:

- audit read path over the file-based finality state
- lookup by `request_id`
- lookup by `external_ref_hash`
- lookup by `tx_id`
- lookup by `commitment_id`
- lookup by `batch_id`
- paginated search
- `jsonl` export
- combined `record + receipt + proof_chain` response

Artifact:

- [docs/denotary-audit-api.md](/c:/projects/verification-contract/docs/denotary-audit-api.md:1)

## Remaining stages

### Stage 9. Security hardening

Goals:

- review replay protection and idempotency
- tighten canonicalization and schema enforcement boundaries
- review metadata leakage in `external_ref`, manifests, and receipts
- verify governance and submitter permission boundaries
- prevent ambiguous or weakly verifiable receipts

Current baseline already added:

- stricter ingress request validation and payload-size limits
- safer default ingress responses without raw canonical material
- watcher-side conflict protection for request re-registration and anchor mutation
- strict request and transaction identifier validation
- watcher auth required by default, with explicit insecure dev mode only for local development
- canonical `request_id` validation against anchor data
- inclusion verification before finality-based receipts are issued
- explicit failed-request handling for dropped or rejected transactions
- zero-hash rejection for `verification.submit(...)`
- legacy `verification` proof-payment path disabled
- DFS storage payments gated by explicit quotes

### Stage 10. Optional proof layer and ZKP

Goals:

- design `ProofRegistry` separately from the MVP path
- keep ZKP independent from the core single and batch anchoring flow

### Stage 11. Integration testing and rollout

Goals:

- contract integration tests
- API integration tests
- finality watcher tests
- batch and inclusion-proof tests
- testnet dry run
- deployment and operations runbooks

Current baseline already added:

- stdlib-based service integration suite
- in-process tests for ingress, watcher, receipt, and audit services
- mock chain finality simulation
- end-to-end single and batch off-chain verification paths
- live-chain integration runner for real `cleos` broadcasts and irreversible-finality checks
- receipt and audit assertions against real `tx_id`, `commitment_id`, `batch_id`, and `external_ref_hash`
- rollout dry-run runner for build, local integration, live-chain integration, and smoke gates

Artifact:

- [docs/denotary-integration-tests.md](/c:/projects/verification-contract/docs/denotary-integration-tests.md:1)
- [docs/denotary-live-chain-integration.md](/c:/projects/verification-contract/docs/denotary-live-chain-integration.md:1)
- [docs/denotary-rollout-dry-run.md](/c:/projects/verification-contract/docs/denotary-rollout-dry-run.md:1)

## Recommended implementation order

1. Stabilize the on-chain model.
2. Maintain deterministic canonicalization regardless of whether preparation happens in ingress or in the client.
3. Keep finality off-chain and explicit.
4. Build receipts and audit reads on top of that.
5. Only then move into security hardening and rollout.
6. Leave ZKP as a separate release track.

## Practical outcome

The repository now already contains a working MVP-shaped contour for:

- proof of existence
- single anchoring
- batch anchoring
- irreversible finality verification
- receipt issuance
- audit-oriented verification reads

The main remaining work is hardening, integration depth, and rollout readiness.
