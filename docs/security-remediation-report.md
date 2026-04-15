# Security Remediation Report

## Scope

This report summarizes the security remediation work completed after the audit of:

- `verification`
- `dfs`
- `Finality Watcher`
- `Receipt Service`
- `Audit API`

## Closed Findings

### 1. Forged finalized receipts through unverified watcher state

Status:

- closed

Remediation:

- `Finality Watcher` now verifies indexed transaction data against:
  - `tx_id`
  - `block_num`
  - expected contract and action
  - expected anchor payload
- `Receipt Service` only issues receipts for `finalized + inclusion_verified`
- `Audit API` exposes verification state explicitly instead of implicitly treating finality as trust

### 2. Unauthenticated watcher mutation endpoints

Status:

- closed

Remediation:

- watcher mutation auth is required by default
- off-chain deployment defaults now require `WATCHER_AUTH_TOKEN`
- compose and runner defaults fail fast if the token is missing

### 3. Request ID tampering

Status:

- closed

Remediation:

- watcher recomputes the canonical `request_id`
- mismatched request registration is rejected

### 4. Zero-hash commitments

Status:

- closed

Remediation:

- `verification.submit(...)` now rejects zero `object_hash`
- smoke and live-chain regression coverage now includes this negative path

### 5. Legacy proof-payment bypass path

Status:

- closed for production use

Remediation:

- legacy `record`, `setpaytoken`, `rmpaytoken`, and proof-payment intake are disabled
- smoke and live-chain regression coverage asserts they stay disabled

### 6. DFS storage payment reference capture

Status:

- closed for the current payment model

Remediation:

- storage payments now require an explicit open quote
- quotes are bound to:
  - payer
  - manifest hash
  - token contract
  - quantity
  - expiry
- duplicate and mismatched quote use is rejected

### 7. DFS settlement authority over-broad payout surface

Status:

- reduced

Remediation:

- settlement payouts are now constrained to unique payout owners
- each payout owner must map to an eligible active storage-capable node
- eligible payout owners must satisfy:
  - active node status
  - storage-capable role
  - sufficient active stake
  - fresh matching price offer
- the payout set must satisfy `min_eligible_price_nodes`

## Additional Hardening Added

- `Receipt Service` now exposes `trust_state` and `receipt_available`
- `Audit API` exposes the same trust model and includes a separate `transaction_verified` proof-chain stage
- smoke and live-chain suites now cover more negative security paths
- local live off-chain validation now covers restart/recovery of watcher-backed state over `SQLite`

## Remaining Trust Assumptions

These are not treated as open vulnerabilities, but they remain explicit operational assumptions:

- `Finality Watcher`, `Receipt Service`, and `Audit API` still rely on an off-chain state layer, with `SQLite` as the recommended runtime backend
- chain-history correctness still depends on the configured RPC/history backend set
- `Audit API` and `Receipt Service` intentionally expose request/transaction correlation metadata in `full` privacy mode
- `dfs::settle(...)` still relies on the configured settlement authority role

## Operational Recommendations

- keep `Finality Watcher` private
- bind off-chain services to `127.0.0.1` unless there is a clear reason not to
- place public services behind a reverse proxy with rate limiting and logging
- use at least two independent history/RPC backends in production where possible
- use `RECEIPT_PRIVACY_MODE=public` and `AUDIT_PRIVACY_MODE=public` for internet-facing deployments
- rotate `WATCHER_AUTH_TOKEN` if it is shared across environments
- keep separate tokens for local, testnet, and production deployments
- retain and back up `FINALITY_STATE_DB` if receipts and audit traces are operationally important

## Validation Completed

- Python service integration tests
- shell smoke script syntax checks
- clean contract builds for `verification` and `dfs`
- local live off-chain restart/recovery validation over `SQLite`
- Jungle4 validation for:
  - `verification` deployment and smoke
  - live-chain single and batch flows
  - `dfs` quote-based storage payment smoke
  - compose-backed live off-chain flow validation

## Suggested Next Follow-Up

- roll out multi-provider verification in real deployment environments
- apply reverse proxy templates and privacy modes in public environments
- expand live-chain and compose failure-injection coverage across more degraded scenarios
