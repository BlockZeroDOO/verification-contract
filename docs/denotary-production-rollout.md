# Production Rollout

This runbook is the practical Sprint 1 rollout path for the current deNotary off-chain stack.

It assumes:

- `verification` is already deployed on the target chain
- the current remediation and live validation work is already merged
- production will use:
  - `SQLite` watcher state
  - at least two history/RPC providers
  - private watcher exposure
  - `public` privacy mode for internet-facing receipt and audit APIs

See also:

- [docs/security-production-checklist.md](/c:/projects/verification-contract/docs/security-production-checklist.md:1)
- [docs/denotary-offchain-deploy.md](/c:/projects/verification-contract/docs/denotary-offchain-deploy.md:1)
- [docs/denotary-public-exposure.md](/c:/projects/verification-contract/docs/denotary-public-exposure.md:1)

## 1. Choose the production trust profile

Recommended:

- `WATCHER_VERIFICATION_POLICY=quorum`
- `WATCHER_VERIFICATION_MIN_SUCCESS=2`
- two independent history/RPC providers

Only fall back to `single-provider` if:

- you have one trusted backend only
- this is documented as an operational tradeoff

## 2. Prepare the environment

For native service deployment:

```bash
cp config/offchain.production.env.example /etc/denotary/offchain.env
```

For Docker Compose deployment:

```bash
cp config/offchain.compose.production.env.example .env.offchain
```

Replace at minimum:

- `WATCHER_AUTH_TOKEN`
- `INGRESS_WATCHER_AUTH_TOKEN`
- `WATCHER_RPC_URLS`
- `INGRESS_WATCHER_RPC_URLS`

Recommended provider pattern:

- one primary internal or preferred backend
- one independent backup backend

## 3. Prepare the runtime storage

Native path:

```bash
sudo mkdir -p /var/lib/denotary /var/log/denotary /var/run/denotary
sudo chown -R "$USER":"$USER" /var/lib/denotary /var/log/denotary /var/run/denotary
```

If migrating from JSON state:

```bash
python scripts/migrate-finality-state.py \
  --source-backend file \
  --source-file /var/lib/denotary/finality-state.json \
  --target-backend sqlite \
  --target-db /var/lib/denotary/finality-state.sqlite3
```

## 4. Start the off-chain stack

### Native

```bash
export OFFCHAIN_ENV_FILE=/etc/denotary/offchain.env
./scripts/offchain-stack.sh start
./scripts/offchain-healthcheck.sh
```

### Docker Compose

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml up -d --build
docker compose --env-file .env.offchain -f docker-compose.offchain.yml ps
```

## 5. Verify the watcher security posture

Check:

- watcher is bound privately
- watcher is not exposed through reverse proxy
- `healthz` shows:
  - `auth_required: true`
  - `insecure_dev_mode: false`
  - expected `verification_policy`
  - expected `verification_min_success`
  - `store.backend: sqlite`

Example:

```bash
curl http://127.0.0.1:8081/healthz
```

## 6. Apply public exposure policy

Recommended public exposure:

- `Ingress API`: optional
- `Receipt Service`: public via reverse proxy only
- `Audit API`: public via reverse proxy only
- `Finality Watcher`: private only

Apply one of:

- [deploy/nginx/denotary-public.conf](/c:/projects/verification-contract/deploy/nginx/denotary-public.conf:1)
- [deploy/caddy/Caddyfile.public](/c:/projects/verification-contract/deploy/caddy/Caddyfile.public:1)

For internet-facing deployments, confirm:

- `RECEIPT_PRIVACY_MODE=public`
- `AUDIT_PRIVACY_MODE=public`
- TLS termination is enabled
- rate limiting is enabled
- request logging is enabled

## 7. Validate the runtime before go-live

Minimum validation:

```bash
./scripts/run-integration-tests.sh
```

If the stack is already running externally:

```bash
./scripts/run-live-offchain-services.sh --use-external-services ...
```

If you are using the local in-process stack:

```bash
./scripts/run-live-offchain-services.sh ...
```

Recommended production-adjacent gate:

- run the live off-chain suite against the real target chain environment
- run restart/recovery validation
- confirm degraded-provider behavior in `quorum`

## 8. Final go-live decision

Treat the deployment as ready only when:

- watcher is private
- watcher auth is enabled
- `SQLite` is the runtime backend
- the database path is persistent
- the selected provider policy is intentional
- at least two providers are configured for the intended trust model
- reverse proxy and TLS are in place
- privacy mode is intentional
- live validation has passed
- restart/recovery has been verified

## 9. Post-launch monitoring

Watch for:

- watcher provider fallback or disagreement
- receipt issuance failures
- audit API trust-state anomalies
- restart/recovery problems after deploys
- unusual ingress request volume if ingress is public

## Summary

Sprint 1 is considered complete when the off-chain stack is running with:

- durable `SQLite` state
- private watcher
- deliberate multi-provider verification
- public proxy controls
- public/privacy policy applied intentionally
- successful live validation in the target environment
