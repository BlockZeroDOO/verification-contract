# DeNotary L1 Backlog

## Status Snapshot (2026-04-14)

Completed epics:

- Epic 0: discovery baseline
- Epic 1: contract core refactor
- Epic 2: access registries
- Epic 3: single anchoring
- Epic 4: batch anchoring
- Epic 5: ingestion baseline
- Epic 6: finality and receipts baseline
- Epic 7: audit API baseline

Current active next epic:

- Epic 9: rollout and orchestration depth

Recently completed hardening items:

- Phase 1: watcher auth by default, canonical `request_id` validation, inclusion verification gating
- Phase 2: zero-hash rejection, legacy proof-path disablement, DFS quote-gated storage payments
- Phase 3: explicit trust-state exposure in receipt and audit read paths
- Phase 4: negative security regression coverage in smoke and live-chain tests
- Phase 5: hardened off-chain deploy defaults and remediation reporting

Deferred:

- Epic 10: optional proof layer and ZKP

## Epic 0. Discovery baseline

Status:

- completed

Delivered:

- entity map
- auth matrix
- lifecycle model
- ADR baseline
- MVP test outline

## Epic 1. Contract core refactor

Status:

- completed

Delivered:

- table and action matrix
- monotonic ID strategy
- clean deployment assumption
- updated contract baseline

## Epic 2. Access registries

Status:

- completed

Delivered:

- `issuekyc`
- `renewkyc`
- `revokekyc`
- `suspendkyc`
- `addschema`
- `updateschema`
- `deprecate`
- `setpolicy`
- `enablezk`
- `disablezk`

## Epic 3. Single anchoring

Status:

- completed

Delivered:

- `commitments` storage
- `submit`
- `supersede`
- `revokecmmt`
- `expirecmmt`
- replay and duplicate protection

## Epic 4. Batch anchoring

Status:

- completed

Delivered:

- `batches` storage
- `submitroot`
- `linkmanifest`
- `closebatch`
- batch lifecycle guards

## Epic 5. Ingestion services

Status:

- completed as baseline

Delivered:

- deterministic canonicalization profile `json-sorted-v1`
- single and batch prepare endpoints
- Merkle root and manifest generation
- trace metadata generation

Open follow-ups:

- on-chain or indexed lookup for schema, policy, and KYC
- tx assembly, signing, and broadcasting

## Epic 6. Finality and receipts

Status:

- completed as baseline

Delivered:

- finality watcher
- request registration
- inclusion updates
- irreversible polling
- single and batch finalized receipts

Open follow-ups:

- broadcaster integration
- automatic handoff from ingress into watcher

## Epic 7. Audit API

Status:

- completed as baseline

Delivered:

- lookup by `request_id`
- lookup by `external_ref_hash`
- lookup by `tx_id`
- lookup by `commitment_id`
- lookup by `batch_id`
- paginated search
- `jsonl` export
- `record + receipt + proof_chain` response shape

Open follow-ups:

- direct chain-table indexer
- batch inclusion-proof retrieval
- read model beyond file-based state

## Epic 8. Security hardening

Status:

- completed as current baseline

Planned work:

- replay and idempotency review
- canonicalization and schema enforcement review
- metadata leakage review
- governance and permission boundary review
- receipt ambiguity review

Already added in the current pass:

- stricter ingress validation and size limits
- safer ingress defaults without raw canonical material
- watcher conflict protection for request re-registration
- watcher protection against conflicting `tx_id`, `block_num`, and anchor-ID rewrites
- watcher mutation auth by default
- explicit failed-request tracking for dropped or rejected tx paths
- trust-state signaling in receipt and audit paths
- negative security regressions in smoke and live-chain validation
- hardened off-chain deploy defaults and remediation report

## Epic 9. Testnet rollout

Status:

- in progress as active next epic

Planned work:

- contract integration tests
- API integration tests
- finality tests
- dry run on testnet
- deploy and operations runbooks

Already added in the current pass:

- local service integration suite
- mock-chain finality tests
- end-to-end single and batch off-chain pipeline coverage
- live-chain integration runner for real `verification` broadcasts
- receipt and audit verification against live `tx_id`, `commitment_id`, and `batch_id`
- rollout dry-run runner that can combine build, local integration, live-chain integration, and smoke gates
- optional ingress-to-watcher auto-registration handoff

## Epic 10. Optional proof layer

Status:

- deferred

Planned work:

- separate `ProofRegistry`
- optional ZKP verification path

## Release slices

### Release A. On-chain foundation

- contract core refactor
- access registries
- single anchoring baseline

### Release B. End-to-end anchoring

- batch anchoring
- ingress baseline
- lifecycle model

### Release C. Verification pipeline

- finality watcher
- receipt service
- audit API
- security hardening
- rollout readiness
