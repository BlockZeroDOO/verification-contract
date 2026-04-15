# Production Security Checklist

This checklist is the practical production follow-up after the remediation and hardening work recorded in:

- `docs/security-remediation-report.md`
- `docs/security-next-steps.md`
- `docs/denotary-offchain-deploy.md`
- `docs/denotary-public-exposure.md`

It is intended as a deployment-time checklist for the deNotary off-chain services and the current on-chain trust model.

## 1. Finality Watcher

- keep `Finality Watcher` private
- do not publish `/v1/watch/*` through a public reverse proxy
- bind watcher to `127.0.0.1` or a private container network only
- set a non-default `WATCHER_AUTH_TOKEN`
- do not reuse the same watcher token between local, testnet, and production
- rotate `WATCHER_AUTH_TOKEN` when environments are rebuilt or credentials are shared too widely
- confirm `healthz` shows:
  - `auth_required: true`
  - `insecure_dev_mode: false`

Recommended:

- `WATCHER_VERIFICATION_POLICY=quorum`
- `WATCHER_VERIFICATION_MIN_SUCCESS=2`

Minimum acceptable fallback:

- `WATCHER_VERIFICATION_POLICY=single-provider`
- only if at least one trusted provider is available and operational constraints are documented

## 2. Chain Backends

- configure at least two independent history/RPC providers in production
- avoid relying on a single provider for long-term receipt trust
- verify provider diversity:
  - different operators
  - different infrastructure paths
  - not just two domains fronting the same backend
- monitor disagreement and fallback behavior from watcher state and logs

Recommended pattern:

- primary provider: your preferred production backend
- secondary provider: independent external backend

Before go-live:

- test one-provider outage behavior
- test provider mismatch visibility
- test receipt behavior under degraded `quorum`

## 3. State Durability

- use `FINALITY_STATE_BACKEND=sqlite`
- use a dedicated persistent path for `FINALITY_STATE_DB`
- back up the SQLite database if receipts and audit traces matter operationally
- do not run production on file-backed JSON state except as temporary compatibility mode
- confirm restart recovery works in your environment

Before go-live:

- restart `Finality Watcher`
- restart `Receipt Service`
- restart `Audit API`
- confirm finalized records remain accessible after restart

## 4. Public Service Exposure

Recommended public exposure model:

- `Ingress API`: optional public exposure
- `Receipt Service`: public only behind reverse proxy
- `Audit API`: public only behind reverse proxy
- `Finality Watcher`: private only

Checklist:

- TLS termination enabled
- request logging enabled
- rate limiting enabled
- service binds kept on `127.0.0.1` or private network
- firewall or security-group policy restricts direct service access

Reference templates:

- `deploy/nginx/denotary-public.conf`
- `deploy/caddy/Caddyfile.public`

## 5. Privacy Modes

For internet-facing deployments:

- set `RECEIPT_PRIVACY_MODE=public`
- set `AUDIT_PRIVACY_MODE=public`

For trusted internal environments only:

- `RECEIPT_PRIVACY_MODE=full`
- `AUDIT_PRIVACY_MODE=full`

Before go-live:

- verify which fields remain visible in `public` mode
- confirm the exposed metadata matches your product/privacy policy

## 6. Ingress API Exposure

- decide explicitly whether public `Ingress API` is part of your product
- if yes, treat it as an abuse surface
- if no, keep it internal and use direct-client canonicalization instead

If exposed publicly:

- keep reverse proxy in front
- enable rate limiting
- review request body size limits
- review logging policy for prepared request metadata
- confirm `watcher` auto-registration uses the correct internal watcher URL/token

## 7. DFS Operational Trust

Current trust assumption:

- `dfs::settle(...)` still depends on `settlement_authority`

Checklist:

- keep `settlement_authority` on a dedicated operational account
- do not reuse the DFS contract account for settlement authority
- protect settlement keys separately from deploy keys
- review who can trigger settlement in your organization
- monitor settlement transactions and payout recipients

## 8. Secrets And Environment Separation

- separate secrets per environment:
  - local
  - Jungle4
  - production
- do not reuse watcher tokens across environments
- keep `.env` files out of public repositories and backups where possible
- review compose and systemd environment files for accidental secret reuse

## 9. Validation Before Go-Live

Minimum recommended validation:

- run integration tests
- run live off-chain suite
- run compose-backed live suite
- run restart/recovery validation
- validate degraded-provider `quorum` behavior

Recommended commands:

```bash
./scripts/run-integration-tests.sh
./scripts/run-live-chain-integration.sh ...
./scripts/run-live-offchain-services.sh ...
```

If using Docker Compose:

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml up -d --build
./scripts/run-live-offchain-services.sh --use-external-services ...
```

## 10. Final Go-Live Gate

Treat deployment as security-ready only when all of the following are true:

- watcher is private
- watcher auth is enabled
- `insecure_dev_mode` is off
- runtime state uses `SQLite`
- database path is persistent
- at least two providers are configured for the intended production trust model
- reverse proxy is in place for public endpoints
- privacy mode is chosen intentionally
- restart/recovery has been tested in the target environment
- live validation has passed against the target chain environment

## Summary

The main code-level security issues are closed. The remaining production work is mostly operational:

- trustworthy provider configuration
- safe public exposure
- durable state handling
- clear privacy posture
- controlled use of the DFS settlement authority
