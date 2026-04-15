# Security Next Steps

## Purpose

This document captures the remaining security-oriented follow-up work after the remediation phases recorded in:

- `docs/security-remediation-report.md`
- `corrections_roadmap.md`

These items are not treated as currently open critical vulnerabilities. They are the next maturity steps for hardening durability, trust boundaries, privacy, and operational resilience.

## P1. Highest Priority

Status:

- durable watcher state is now implemented with `SQLite` as the recommended runtime backend
- file backend remains only as compatibility/dev mode
- migration tooling and startup recovery are already in place
- multi-backend verification, provider fallback, and provider-policy support are already implemented

Remaining follow-up:

- production deployments should use at least two independent history/RPC providers
- provider policy should be reviewed per environment instead of relying on the default everywhere

### 1. Replace file-based watcher state with a durable backend

Current state:

- `Finality Watcher`, `Receipt Service`, and `Audit API` support `SQLite` and use it as the recommended runtime backend.
- file-backed JSON state remains only for compatibility and local/dev scenarios.

Risk:

- loss or corruption of local state
- weak recovery after restart
- limited concurrency guarantees
- higher operational risk for receipts and audit traces

Recommended direction:

- keep `SQLite` as the baseline durable backend for current deployments
- use migration/export tooling during upgrades and environment moves
- keep restart-safe recovery and replay validation in the release gate

Success criteria:

- state survives restarts cleanly
- receipt and audit data remain consistent after recovery
- deployments no longer rely on file-only state for normal production runtime

### 2. Add multi-backend chain verification

Current state:

- watcher supports multiple history/RPC providers
- provider fallback, disagreement tracking, and policy-level verification are implemented

Risk:

- incorrect or incomplete data from one backend can degrade trust
- backend outages can block finality verification

Recommended direction:

- configure at least two independent chain/history backends in production
- use explicit provider policy per environment:
  - `single-provider`
  - `quorum`
- monitor provider disagreement and fallback behavior in operations

Success criteria:

- watcher can fail over between providers
- mismatch between providers is surfaced explicitly
- production verification does not rely on one backend only

## P2. Important

Status:

- reverse proxy templates are available
- `Receipt Service` and `Audit API` support `full` and `public` privacy modes
- remaining follow-up is operational rollout and field-level policy tuning per deployment

### 3. Harden public API exposure through reverse proxy patterns

Current state:

- deploy-time guidance and proxy templates exist, but enforcement still depends on real environment configuration

Risk:

- brute-force or abusive traffic
- metadata scraping
- noisy public exposure without traffic controls

Recommended direction:

- add production-ready reverse proxy templates
- require TLS termination, rate limiting, and request logging
- define private/public exposure rules per service

Success criteria:

- `Finality Watcher` remains private
- `Receipt Service` and `Audit API` can be exposed behind explicit controls
- public deployment has repeatable proxy configuration

### 4. Review privacy and metadata leakage policy

Current state:

- `Audit API` and `Receipt Service` intentionally expose correlation metadata in `full` mode
- `public` mode already redacts the most correlation-heavy fields

Risk:

- linkage between requests, hashes, and transactions may reveal usage patterns

Recommended direction:

- review whether current `public` mode is sufficient for your production posture
- decide whether some fields should be further redacted, delayed, or role-gated
- document deployment-specific privacy tradeoffs explicitly

Success criteria:

- metadata exposure is intentional and documented
- public deployments can reduce visible correlation data if needed

## P3. Strategic

### 5. Revisit `dfs::settle(...)` trust model

Current state:

- settlement still relies on `settlement_authority`

Risk:

- central operational authority remains a trust concentration point

Recommended direction:

- either keep this model and document it clearly
- or evolve toward stronger on-chain validation of payout eligibility

Success criteria:

- trust boundary is explicit
- authority role is operationally controlled and monitored
- future decentralization path is documented if desired

### 6. Expand resilience and adversarial live testing

Current state:

- core negative security regressions are covered

Risk:

- operational failure modes are still under-tested

Recommended direction:

- add tests for flaky history endpoints
- add restart/recovery tests for watcher state
- add partial-service failure tests in compose deployments
- add replay and recovery validation after interrupted runs

Success criteria:

- live validation covers degraded conditions, not only healthy paths
- restart and recovery behavior is predictable

Status:

- restart/recovery coverage is implemented for the local live off-chain suite with `SQLite` watcher state
- compose-level restart/recovery validation is now available in the external live off-chain suite
- remaining work is mostly provider-flake scenarios and broader partial-failure matrices against public testnets

## Suggested Execution Order

1. Durable watcher backend
2. Multi-backend chain verification
3. Reverse proxy rollout in the target environment
4. Privacy policy tuning for public deployments
5. DFS settlement trust review
6. Expanded resilience testing against degraded live providers

## Summary

The main code-level vulnerabilities from the earlier audit are closed. The next security work is mostly about:

- stronger durability
- less trust in a single backend
- safer public deployment
- clearer privacy boundaries
- better resilience under failure conditions
