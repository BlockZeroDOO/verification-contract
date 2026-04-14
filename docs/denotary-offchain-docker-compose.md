# Off-Chain Docker Compose

This document describes the simplest local deployment path for the deNotary off-chain stack with Docker Compose.

## Services

The compose stack runs:

- `ingress` on `127.0.0.1:8080`
- `finality` on `127.0.0.1:8081`
- `receipt` on `127.0.0.1:8082`
- `audit` on `127.0.0.1:8083`

`finality`, `receipt`, and `audit` share one named Docker volume for `finality-state.json`.

## 1. Prepare the env file

```bash
cp config/offchain.compose.env.example .env.offchain
```

Adjust values if needed:

```bash
CONTRACT_ACCOUNT=verification
RPC_URL=https://history.denotary.io
CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48
POLL_INTERVAL_SEC=10
WATCHER_AUTH_TOKEN=
```

For Jungle4 instead:

```bash
RPC_URL=https://jungle4.api.eosnation.io
CHAIN_ID=73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d
```

## 2. Build and start

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml up -d --build
```

## 3. Check status

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml ps
docker compose --env-file .env.offchain -f docker-compose.offchain.yml logs -f
```

## 4. Health checks

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8081/healthz
curl http://127.0.0.1:8082/healthz
curl http://127.0.0.1:8083/healthz
```

## 5. Stop the stack

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml down
```

To also remove the shared state volume:

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml down -v
```

## 6. Practical local workflow

Start stack:

```bash
docker compose --env-file .env.offchain -f docker-compose.offchain.yml up -d --build
```

Run local integration tests against the running stack:

```bash
python -m unittest tests.test_service_integration
```

Use the services:

- `Ingress API`: `http://127.0.0.1:8080`
- `Finality Watcher`: `http://127.0.0.1:8081`
- `Receipt Service`: `http://127.0.0.1:8082`
- `Audit API`: `http://127.0.0.1:8083`

If you want mutation auth on `Finality Watcher`, set `WATCHER_AUTH_TOKEN` in `.env.offchain` before starting the stack.
