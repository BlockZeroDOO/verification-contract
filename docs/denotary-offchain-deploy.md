# Off-Chain Deployment

This document describes the practical deployment of the deNotary off-chain services:

- `Ingress API`
- `Finality Watcher`
- `Receipt Service`
- `Audit API`

For local development and the fastest all-in-one launch, prefer Docker Compose:

- [docs/denotary-offchain-docker-compose.md](/c:/projects/verification-contract/docs/denotary-offchain-docker-compose.md:1)

## Services and ports

Default binding:

- `Ingress API`: `127.0.0.1:8080`
- `Finality Watcher`: `127.0.0.1:8081`
- `Receipt Service`: `127.0.0.1:8082`
- `Audit API`: `127.0.0.1:8083`

Shared runtime state:

- `STATE_FILE=/var/lib/denotary/finality-state.json`

Default deNotary chain settings:

- `RPC_URL=https://history.denotary.io`
- `CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`

## 1. Prepare the server

Install the minimal runtime dependencies:

```bash
sudo apt-get update
sudo apt-get install -y python3 curl
```

Clone the repository and move to the project root:

```bash
git clone https://github.com/BlockZeroDOO/deNotary.git
cd deNotary
```

## 2. Prepare the environment file

Copy the example file and adjust paths and secrets:

```bash
sudo mkdir -p /etc/denotary
sudo cp config/offchain.env.example /etc/denotary/offchain.env
sudo nano /etc/denotary/offchain.env
```

Recommended minimum values:

```bash
PROJECT_ROOT=/opt/deNotary
PYTHON_BIN=/usr/bin/python3

OFFCHAIN_HOST=127.0.0.1
INGRESS_PORT=8080
FINALITY_PORT=8081
RECEIPT_PORT=8082
AUDIT_PORT=8083

CONTRACT_ACCOUNT=verification
RPC_URL=https://history.denotary.io
CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48
POLL_INTERVAL_SEC=10
WATCHER_AUTH_TOKEN=replace-with-shared-secret

STATE_FILE=/var/lib/denotary/finality-state.json
PID_DIR=/var/run/denotary
LOG_DIR=/var/log/denotary
```

Create runtime directories:

```bash
sudo mkdir -p /var/lib/denotary /var/run/denotary /var/log/denotary
sudo chown -R "$USER":"$USER" /var/lib/denotary /var/run/denotary /var/log/denotary
```

## 3. Manual launch

For a fast server-side smoke start, use the local orchestrator:

```bash
export OFFCHAIN_ENV_FILE=/etc/denotary/offchain.env
./scripts/offchain-stack.sh start
./scripts/offchain-stack.sh status
./scripts/offchain-healthcheck.sh
```

Stop the whole stack:

```bash
export OFFCHAIN_ENV_FILE=/etc/denotary/offchain.env
./scripts/offchain-stack.sh stop
```

Logs are written into `${LOG_DIR}` from the environment file.

## 4. systemd deployment

Copy the unit files:

```bash
sudo cp deploy/systemd/denotary-*.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Enable and start the services:

```bash
sudo systemctl enable denotary-ingress.service
sudo systemctl enable denotary-finality-watcher.service
sudo systemctl enable denotary-receipt.service
sudo systemctl enable denotary-audit.service

sudo systemctl start denotary-ingress.service
sudo systemctl start denotary-finality-watcher.service
sudo systemctl start denotary-receipt.service
sudo systemctl start denotary-audit.service
```

Check status:

```bash
sudo systemctl status denotary-ingress.service
sudo systemctl status denotary-finality-watcher.service
sudo systemctl status denotary-receipt.service
sudo systemctl status denotary-audit.service
```

Tail logs:

```bash
journalctl -u denotary-ingress.service -f
journalctl -u denotary-finality-watcher.service -f
journalctl -u denotary-receipt.service -f
journalctl -u denotary-audit.service -f
```

## 5. Reverse proxy recommendation

The services are intended to bind on `127.0.0.1`.

Recommended publication model:

- public-facing reverse proxy in front of `Ingress API`
- public-facing reverse proxy in front of `Receipt Service`
- public-facing reverse proxy in front of `Audit API`
- keep `Finality Watcher` private

If you expose `Finality Watcher` mutation endpoints beyond localhost, set `WATCHER_AUTH_TOKEN`.

## 6. Health checks

Local health endpoints:

- `http://127.0.0.1:8080/healthz`
- `http://127.0.0.1:8081/healthz`
- `http://127.0.0.1:8082/healthz`
- `http://127.0.0.1:8083/healthz`

Quick check:

```bash
export OFFCHAIN_ENV_FILE=/etc/denotary/offchain.env
./scripts/offchain-healthcheck.sh
```

## 7. Practical rollout sequence

Recommended order:

1. Start `Finality Watcher`
2. Start `Receipt Service`
3. Start `Audit API`
4. Start `Ingress API`
5. Run local health checks
6. Run integration or live-chain validation

## 8. Validation

After the services are up:

```bash
./scripts/run-integration-tests.sh
```

For live validation against the deployed `verification` contract:

```bash
./scripts/run-live-chain-integration.sh \
  --rpc-url https://history.denotary.io \
  --expected-chain-id 9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48 \
  --network-label deNotary \
  --owner-account verification \
  --submitter-account verification
```
