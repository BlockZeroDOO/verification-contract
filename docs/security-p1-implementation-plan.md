# Security P1 Implementation Plan

## Scope

This plan expands the two `P1` follow-up items from `docs/security-next-steps.md` into an implementation-ready technical roadmap:

1. replace file-based watcher state with a durable backend
2. add multi-backend chain verification for inclusion and finality

The plan is intentionally incremental so the current system can keep working while the new backend and verification model are introduced behind stable APIs.

## Current State

Current implementation:

- `services/finality_store.py`
  - JSON file storage
  - whole-state read/write model
- `services/finality_watcher.py`
  - directly depends on `FinalityStore`
  - directly calls chain/history endpoints via `rpc_post_json()` and `rpc_get_json()`
- `services/receipt_service.py`
  - reads watcher state through the same file-backed store
- `services/audit_api.py`
  - reads watcher state through the same file-backed store

Current limitations:

- no durable indexed store
- no structured migration path
- no backend failover
- no explicit provider trust model
- no detection of provider disagreement

## Target Architecture

### A. Durable state layer

Recommended first durable backend:

- `SQLite`

Why SQLite first:

- available in Python stdlib
- simple deployment story
- transactional updates
- much safer than whole-file overwrite
- good enough for the current single-node service topology

Future-compatible direction:

- keep storage behind an interface so a later PostgreSQL backend can be added without rewriting service handlers

### B. Multi-backend verification layer

Introduce a separate verification component that:

- queries multiple chain/history providers
- normalizes transaction data
- applies request/action matching once on normalized data
- records provider-level verification outcomes
- derives a final verification decision from a policy

Recommended first policy:

- one provider is sufficient for normal progression
- disagreement between providers is recorded explicitly
- optional strict mode can require agreement from at least two providers

This keeps the current system practical while allowing stronger production settings later.

## Deliverable 1: Storage Abstraction

### Goal

Remove direct coupling between service handlers and the file-backed store.

### New files

- `services/finality_store_base.py`
- `services/finality_store_file.py`
- `services/finality_store_sqlite.py`

### Existing files to update

- `services/finality_store.py`
- `services/finality_watcher.py`
- `services/receipt_service.py`
- `services/audit_api.py`

### Design

Create a store interface with the operations already used by the system:

- `get_request(request_id)`
- `list_requests()`
- `upsert_request(request_id, payload)`
- `patch_request(request_id, updates)`
- `read()` only if still needed for compatibility
- `export_state()`
- `import_state()`

Recommended shape:

- `FinalityStoreBase` abstract class
- `FileFinalityStore`
- `SQLiteFinalityStore`

### Implementation steps

#### Step 1. Extract the interface

Create `services/finality_store_base.py` with a minimal abstract API.

Refactor:

- current JSON implementation becomes `FileFinalityStore`
- `services/finality_store.py` becomes a small compatibility loader/factory

#### Step 2. Add backend selection

Support runtime configuration like:

- `--state-backend file`
- `--state-backend sqlite`
- `--state-file runtime/finality-state.json`
- `--state-db runtime/finality-state.sqlite3`

Factory helper:

- `build_finality_store(args)`

#### Step 3. Implement SQLite schema

Recommended initial schema:

Table: `requests`

- `request_id TEXT PRIMARY KEY`
- `trace_id TEXT NOT NULL`
- `mode TEXT NOT NULL`
- `submitter TEXT NOT NULL`
- `contract TEXT NOT NULL`
- `status TEXT NOT NULL`
- `rpc_url TEXT NOT NULL`
- `tx_id TEXT NULL`
- `block_num INTEGER NULL`
- `registered_at TEXT NOT NULL`
- `included_at TEXT NULL`
- `finalized_at TEXT NULL`
- `failed_at TEXT NULL`
- `updated_at TEXT NOT NULL`
- `failure_reason TEXT NULL`
- `failure_details TEXT NULL`
- `inclusion_verified INTEGER NOT NULL`
- `inclusion_verified_at TEXT NULL`
- `inclusion_verification_error TEXT NULL`
- `anchor_json TEXT NOT NULL`
- `chain_state_json TEXT NOT NULL`
- `verified_action_json TEXT NULL`
- `verification_state_json TEXT NULL`

Indexes:

- `idx_requests_status`
- `idx_requests_tx_id`
- `idx_requests_submitter`

Optional future split:

- move anchor and verification details into dedicated tables only after the first migration is stable

#### Step 4. Add migration and export tooling

New script:

- `scripts/migrate-finality-state.py`

Capabilities:

- import JSON file state into SQLite
- export SQLite state back to JSON
- dry-run row count and schema validation

#### Step 5. Update watcher, receipt, and audit startup

All three services should accept shared backend config and construct the same backend type.

Compose/env additions:

- `FINALITY_STATE_BACKEND=sqlite`
- `FINALITY_STATE_DB=/data/finality-state.sqlite3`

Compatibility path:

- keep file backend as explicit dev/test mode
- use SQLite as the default production recommendation

## Deliverable 2: Recovery And Durability Behavior

### Goal

Make restarts and recovery predictable.

### Implementation steps

#### Step 6. Add startup consistency checks

On startup, watcher should:

- validate schema version
- verify database accessibility
- optionally log request counts by status

Add a small metadata table:

Table: `store_meta`

- `key TEXT PRIMARY KEY`
- `value TEXT NOT NULL`

Useful entries:

- `schema_version`
- `created_at`
- `last_migration_at`

#### Step 7. Add safe replay and recovery support

Add a watcher maintenance mode:

- scan requests in `submitted` and `included`
- re-run inclusion verification
- re-run finality polling

This can happen:

- automatically at startup
- or via explicit maintenance endpoint/CLI command

#### Step 8. Add retention and backup guidance

Update docs and deploy templates with:

- volume mounting for SQLite file
- backup recommendations
- restore instructions

## Deliverable 3: Multi-Backend Verification Abstraction

### Goal

Stop coupling verification logic to one RPC/history provider.

### New files

- `services/chain_backend.py`
- `services/chain_backends/default_backend.py`
- `services/chain_verifier.py`

Optional:

- `services/chain_backends/hyperion_backend.py`
- `services/chain_backends/nodeos_backend.py`

### Existing files to update

- `services/finality_watcher.py`
- `tests/test_service_integration.py`
- `tests/live_chain_integration.py`
- `tests/live_offchain_services.py`

### Design

Split provider access from verification logic.

#### Backend responsibility

A backend adapter should:

- fetch chain info
- fetch transaction details
- normalize actions
- normalize `block_num`
- expose provider name and endpoint

#### Verifier responsibility

The verifier should:

- query one or more providers
- compare normalized outputs
- match actions against request anchor
- produce structured verification result

## Deliverable 4: Verification Result Model

### Goal

Make provider trust explicit in stored state.

### New verification payload

Recommended structure:

```json
{
  "policy": "single-provider",
  "providers_checked": [
    {
      "name": "jungle4-cryptolions",
      "rpc_url": "https://jungle4.cryptolions.io",
      "ok": true,
      "block_num": 260000000,
      "action_name": "submit",
      "verified_at": "2026-04-15T07:00:00Z",
      "error": null
    },
    {
      "name": "jungle4-eosnation",
      "rpc_url": "https://jungle4.api.eosnation.io",
      "ok": false,
      "block_num": null,
      "action_name": null,
      "verified_at": "2026-04-15T07:00:01Z",
      "error": "history backend returned 410"
    }
  ],
  "consensus": {
    "verified": true,
    "provider_count_ok": 1,
    "provider_count_total": 2,
    "provider_disagreement": false
  }
}
```

### State additions

Add fields to request payload:

- `verification_policy`
- `verification_state`
- `provider_disagreement`

These fields should be available to:

- watcher
- receipt service
- audit API

## Deliverable 5: Provider Policy

### Goal

Make verification strictness configurable.

### Recommended configuration

- `--verification-policy single-provider`
- `--verification-policy quorum`
- `--verification-min-success 1`
- `--verification-min-success 2`

Suggested semantics:

- `single-provider`
  - any one valid provider is enough
- `quorum`
  - at least `N` providers must independently verify the same request

### First production-ready default

Recommended default for current stack:

- policy: `single-provider`
- at least two configured providers
- disagreement recorded but not immediately blocking

Recommended stricter production option later:

- policy: `quorum`
- minimum success: `2`

## Deliverable 6: Service Behavior Changes

### Finality Watcher

Update:

- `fetch_chain_info()` should use a backend abstraction
- `verify_inclusion()` should move into `chain_verifier.py`
- `poll_request()` should read consensus verification result, not only one raw response

### Receipt Service

No trust downgrade should happen silently.

Receipt should continue to require:

- `status == finalized`
- `inclusion_verified == true`

Potential extension:

- surface `verification_policy`
- surface `provider_count_ok`

### Audit API

Expose provider trust details explicitly.

Useful additions:

- `verification_policy`
- `provider_disagreement`
- per-provider verification summaries

## Deliverable 7: Tests

### Unit tests

Add:

- file store parity tests
- SQLite store CRUD tests
- JSON-to-SQLite migration tests
- provider normalization tests
- provider disagreement tests

### Integration tests

Add:

- restart with SQLite state preserved
- recovery after watcher restart
- verification with one provider down
- verification with conflicting provider responses

### Live tests

Add:

- compose deployment using SQLite-backed watcher state
- multi-provider config smoke
- failover where primary provider is unavailable

## Deliverable 8: Deployment Changes

### Compose and env

Add variables:

- `FINALITY_STATE_BACKEND`
- `FINALITY_STATE_DB`
- `WATCHER_RPC_URLS`
- `WATCHER_RPC_PROVIDER_POLICY`
- `WATCHER_RPC_MIN_SUCCESS`

Example:

```env
FINALITY_STATE_BACKEND=sqlite
FINALITY_STATE_DB=/data/finality-state.sqlite3
WATCHER_RPC_URLS=https://history.denotary.io,https://backup-history.denotary.io
WATCHER_RPC_PROVIDER_POLICY=single-provider
WATCHER_RPC_MIN_SUCCESS=1
```

### Docker

Add persistent volume for watcher state:

- named volume or bind mount for `/data`

### Docs

Update:

- `docs/denotary-offchain-docker-compose.md`
- `docs/denotary-offchain-deploy.md`
- `docs/denotary-finality-services.md`
- `README.md`

## Recommended Implementation Order

### Phase A. Storage abstraction

1. add store interface
2. rename current file backend
3. update services to use store factory

### Phase B. SQLite backend

4. implement SQLite schema and CRUD
5. add migration/export tool
6. run store parity tests

### Phase C. Recovery behavior

7. add startup checks
8. add replay/recovery pass
9. validate compose persistence

### Phase D. Provider abstraction

10. add backend adapters
11. add chain verifier
12. move watcher verification onto the abstraction

### Phase E. Multi-provider policy

13. add provider policy config
14. persist provider verification summaries
15. expose trust details in audit/receipt

### Phase F. Deployment and tests

16. add SQLite compose defaults
17. add failover tests
18. document migration and rollback

## Suggested Commit Sequence

1. `refactor: extract finality store interface`
2. `feat: add sqlite finality store backend`
3. `feat: add finality state migration tooling`
4. `feat: add watcher startup recovery pass`
5. `refactor: extract chain backend adapters`
6. `feat: add multi-backend chain verifier`
7. `feat: persist provider verification state`
8. `test: add sqlite and provider failover coverage`
9. `docs: document durable state and multi-backend verification`

## Definition Of Done

P1 can be considered complete when all of the following are true:

- watcher, receipt, and audit can run against SQLite state
- restart does not lose request state
- migration from JSON file state to SQLite is documented and tested
- watcher can query multiple providers
- provider disagreement is recorded explicitly
- verification policy is configurable
- live tests pass with persistent state and at least two providers configured
