# Security Next Steps

## Purpose

This document captures the remaining security-oriented follow-up work after the remediation phases recorded in:

- `docs/security-remediation-report.md`
- `corrections_roadmap.md`

These items are not treated as currently open critical vulnerabilities. They are the next maturity steps for hardening durability, trust boundaries, privacy, and operational resilience.

## P1. Highest Priority

### 1. Replace file-based watcher state with a durable backend

Current state:

- `Finality Watcher`, `Receipt Service`, and `Audit API` still depend on file-based state.

Risk:

- loss or corruption of local state
- weak recovery after restart
- limited concurrency guarantees
- higher operational risk for receipts and audit traces

Recommended direction:

- move watcher state to a durable indexed backend
- add explicit migration/export tooling
- support restart-safe recovery and replay

Success criteria:

- state survives restarts cleanly
- receipt and audit data remain consistent after recovery
- concurrent updates do not risk state corruption

### 2. Add multi-backend chain verification

Current state:

- inclusion verification depends on a single configured history/RPC backend

Risk:

- incorrect or incomplete data from one backend can degrade trust
- backend outages can block finality verification

Recommended direction:

- support at least two independent chain/history backends
- cross-check critical transaction metadata
- define fallback and mismatch policy

Success criteria:

- watcher can fail over between providers
- mismatch between providers is surfaced explicitly
- verified finality does not depend on one backend only

## P2. Important

Status:

- reverse proxy templates and public privacy modes are now available for `Receipt Service` and `Audit API`
- remaining follow-up is operational rollout and field-level policy tuning per deployment

### 3. Harden public API exposure through reverse proxy patterns

Current state:

- docs require cautious deployment, but enforcement is mostly operational

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

- `Audit API` and `Receipt Service` intentionally expose correlation metadata

Risk:

- linkage between requests, hashes, and transactions may reveal usage patterns

Recommended direction:

- define public mode vs restricted mode response policy
- review whether some fields should be redacted, delayed, or role-gated
- document privacy tradeoffs explicitly

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

- restart/recovery coverage is now implemented for the local live off-chain suite with `SQLite` watcher state
- remaining work is mostly compose-level failure injection and provider-flake scenarios against public testnets

## Suggested Execution Order

1. Durable watcher backend
2. Multi-backend chain verification
3. Reverse proxy and public deployment templates
4. Privacy and metadata policy
5. DFS settlement trust review
6. Expanded resilience testing

## Summary

The main code-level vulnerabilities from the earlier audit are closed. The next security work is mostly about:

- stronger durability
- less trust in a single backend
- safer public deployment
- clearer privacy boundaries
- better resilience under failure conditions
