# DeNotary L1 Test Matrix

## Purpose

Этот документ фиксирует минимальную тестовую матрицу для MVP по TSD v2.

Он покрывает:

- on-chain registry invariants
- single anchoring flow
- batch anchoring flow
- finality and receipt pipeline
- audit/read model

## Test Layers

### 1. Contract action tests

Проверяют инварианты таблиц, actions и permission boundaries.

### 2. Service integration tests

Проверяют взаимодействие `Ingress API`, `Canonicalization Service`, `Batch Builder`, `Finality Watcher`, `Receipt Service`.

Current baseline artifact:

- [tests/test_service_integration.py](/c:/projects/verification-contract/tests/test_service_integration.py:1)
- [tests/live_chain_integration.py](/c:/projects/verification-contract/tests/live_chain_integration.py:1)

### 3. End-to-end verification tests

Проверяют пользовательский путь от submit до receipt и Audit API.

### 4. Security and negative tests

Проверяют replay, invalid transitions, metadata leakage и ошибочные сценарии.

## Required Test Cases

### KYC registry

- issue KYC for existing account
- renew active KYC
- suspend active KYC
- revoke active KYC
- reject KYC action from unauthorized account
- reject expired or inactive KYC for policy that requires KYC

### Schema registry

- add schema with valid hashes
- update schema with valid admin auth
- deprecate schema
- reject submit against inactive schema
- reject schema mutation from unauthorized account

### Policy registry

- create policy with `allow_single=true`
- create policy with `allow_batch=true`
- reject policy mutation from unauthorized account
- reject single submit when policy disallows single
- reject batch submit when policy disallows batch
- reject submit when `min_kyc_level` is not met

### Single anchoring

- accept valid single submit
- persist `submitter`, `schema_id`, `policy_id`, `hash`, `created_at`
- reject duplicate idempotency key
- reject submit with invalid hash shape
- reject submit when KYC is required and absent
- supersede active record
- revoke active record through governance path
- expire active record through maintenance/governance path
- reject invalid lifecycle transition from terminal state

### Batch anchoring

- accept valid `submitroot`
- persist `root_hash`, `leaf_count`, `manifest_hash`, `schema_id`, `policy_id`
- reject batch submit when policy disallows batch
- reject malformed manifest hash
- link manifest to open batch
- close finalized batch
- reject mutation of closed batch

### Canonicalization service

- identical input yields identical canonical form
- canonical output changes when schema version changes
- hash derived from canonical form is deterministic
- invalid input shape is rejected before tx submission

### Ingress API

- API rejects submit when schema is inactive
- API rejects submit when policy/KYC prechecks fail
- API creates traceable request id for single flow
- API creates traceable batch id for batch flow
- API rejects oversized request bodies
- API rejects overlarge batch manifests or canonicalized payloads
- API hides raw canonical material unless debug mode is explicitly enabled

### Batch builder

- identical ordered leaf set yields identical root
- inclusion proof reconstructs root correctly
- manifest hash matches stored manifest bytes
- batch manifest is immutable after finalization

### Finality watcher

- watcher observes submitted tx
- watcher marks tx as included after block inclusion
- watcher marks tx as finalized only after irreversible
- watcher handles delayed finality without false positives
- watcher handles tx failure/rejection path
- watcher rejects conflicting re-registration of the same `request_id`
- watcher rejects rewriting `tx_id` or `block_num` after they are recorded
- watcher rejects conflicting `commitment_id` or `batch_id` anchor rewrites

### Service integration baseline

- local mock-chain test can drive `submitted -> included -> finalized`
- single request can move from ingress prepare to receipt and audit lookup
- batch request can move from ingress prepare to receipt and audit lookup
- audit API can resolve by `commitment_id` and `batch_id` after watcher anchor updates

### Live-chain integration baseline

- local services can prepare requests while targeting a real Antelope RPC
- `submit` can be broadcast on-chain and reconciled into watcher finality state
- `submitroot`, `linkmanifest`, and `closebatch` can be broadcast on-chain and reconciled into watcher finality state
- finalized receipt matches the real live-chain `tx_id` and `block_num`
- audit API can resolve live requests by `tx_id`, `commitment_id`, `batch_id`, and `external_ref_hash`

### Receipt service

- single receipt contains `hash`, `tx_id`, `block_num`, `finality_flag`
- batch receipt contains `root`, `inclusion_proof`, `tx_id`, `finality_flag`
- receipt is not issued before finality
- receipt verification fails for mismatched inclusion proof

### Indexer and Audit API

- can query commitment by `commitment_id`
- can query record by `external_ref`
- can query batch by `batch_id`
- returns business status separately from technical finality state
- returns receipt chain with linked chain metadata

### Security and negative scenarios

- replay of same single request is rejected or handled idempotently
- replay of same batch request is rejected or handled idempotently
- unauthorized governance action is rejected
- generic status mutation path is not exposed
- metadata fields do not leak raw source document
- malformed manifest or inclusion proof is rejected by verification path

## Read Model Assertions

Внешний клиент должен стабильно получить из системы:

- KYC state по account
- schema status и version
- policy constraints по `policy_id`
- commitment record по `id`
- batch record по `id`
- business status отдельно от finality status
- receipt для finalized single/batch flow

## Release Gates

MVP не готов к testnet rollout, пока не выполнены все условия:

- contract model для `KYC`, `Schema`, `Policy`, `Commitment`, `Batch` покрыт тестами
- single anchoring работает end-to-end
- batch anchoring работает end-to-end
- receipt не выдается до irreversible finality
- Audit API возвращает корректную verification chain
- replay path закрыт для single и batch потоков
- недопустимые lifecycle transitions запрещены

## Nice-to-Have After MVP

- нагрузочные тесты batch builder на большие manifest
- тесты устойчивости finality watcher к node failover
- миграционные тесты для эволюции schema/policy versioning
- optional proof layer tests для `ProofRegistry` и ZKP workers
