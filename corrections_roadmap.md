# Security Corrections Roadmap

## Phase 1: Critical Integrity

### 1. Require watcher auth by default
- Files:
  - `services/finality_watcher.py`
  - `config/offchain.compose.env.example`
  - `config/offchain.env.example`
  - `docker-compose.offchain.yml`
  - `docs/denotary-offchain-deploy.md`
- Work:
  - require an auth token for normal startup
  - allow startup without a token only in explicit insecure dev mode
  - protect all mutation endpoints
- Commit:
  - `security: require watcher auth by default`

### 2. Verify real on-chain inclusion
- Files:
  - `services/finality_watcher.py`
  - `services/receipt_service.py`
  - `services/audit_api.py`
- Work:
  - fetch transaction details by `tx_id`
  - verify `block_num`
  - verify contract/action relevance
  - verify action payload against `anchor`
  - add `inclusion_verified`
  - block finalized receipts without verified inclusion
- Commit:
  - `security: verify on-chain inclusion before finality`

### 3. Validate derived `request_id`
- Files:
  - `services/finality_watcher.py`
  - `services/ingress_api.py`
- Work:
  - share one request-id derivation formula
  - recompute `request_id` during registration
  - reject mismatches
- Commit:
  - `security: validate derived request ids`

## Phase 2: On-Chain Hardening

### 4. Reject zero `object_hash` in `submit`
- Files:
  - `src/verification.cpp`
- Work:
  - add `validate_nonzero_checksum(object_hash, "object_hash")`
- Commit:
  - `security: reject zero object hash commitments`

### 5. Disable legacy `proofs` flow
- Files:
  - `include/verification.hpp`
  - `src/verification.cpp`
- Work:
  - remove or production-disable `record`
  - remove or production-disable legacy `ontransfer` proof path
- Commit:
  - `security: disable legacy proof payment flow`

### 6. Protect DFS storage payment references
- Files:
  - `include/dfs.hpp`
  - `src/dfs.cpp`
- Work:
  - introduce a quote/intention registry
  - accept storage payments only for registered quotes
  - bind quote to payer, manifest, token, and amount
- Commit:
  - `security: require storage payment quotes in dfs`

## Phase 3: Service Trust Model

### 7. Harden `Receipt Service`
- Files:
  - `services/receipt_service.py`
- Work:
  - issue receipts only for `finalized + inclusion_verified`
  - expose trust-state for non-finalized and failed requests
- Commit:
  - `security: gate receipts on verified finality`

### 8. Harden `Audit API`
- Files:
  - `services/audit_api.py`
- Work:
  - expose verification status and trust level explicitly
  - avoid presenting unverified inclusion as trusted final proof
- Commit:
  - `security: expose verification status in audit api`

## Phase 4: Test Coverage

### 9. Add security regression tests
- Files:
  - `tests/test_service_integration.py`
  - `tests/live_chain_integration.py`
  - `tests/live_offchain_services.py`
- Work:
  - watcher without token
  - mismatched `request_id`
  - fake or mismatched `tx_id`
  - zero `object_hash`
  - legacy proof path disabled
  - DFS `payment_reference` replay/front-running
- Commit:
  - `test: add security regression coverage`

## Phase 5: Deployment And Ops

### 10. Harden deploy defaults
- Files:
  - `docker-compose.offchain.yml`
  - `docs/denotary-offchain-docker-compose.md`
  - `docs/denotary-offchain-deploy.md`
  - `README.md`
- Work:
  - require `WATCHER_AUTH_TOKEN`
  - document internal bind or reverse-proxy requirements
  - document exposure rules for `audit` and `receipt`
- Commit:
  - `docs: harden off-chain deployment defaults`

### 11. Publish post-remediation report
- Files:
  - `docs/security-remediation-report.md`
- Work:
  - record closed risks
  - record remaining trust assumptions
  - record operational recommendations
- Commit:
  - `docs: add post-remediation security report`

## Recommended Commit Order
1. `security: require watcher auth by default`
2. `security: verify on-chain inclusion before finality`
3. `security: validate derived request ids`
4. `security: reject zero object hash commitments`
5. `security: disable legacy proof payment flow`
6. `security: require storage payment quotes in dfs`
7. `security: gate receipts on verified finality`
8. `security: expose verification status in audit api`
9. `test: add security regression coverage`
10. `docs: harden off-chain deployment defaults`
11. `docs: add post-remediation security report`
