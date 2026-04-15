# Off-Chain Resilience Drill

This runbook packages the current Sprint 2 resilience validation into one repeatable operator flow.

It is intended for:

- degraded-provider `quorum` checks
- compose restart/recovery validation
- public-testnet or production-adjacent operational drills

The underlying assertions are executed by the existing live off-chain suite, but this wrapper makes the drill easier to run as an operational exercise.

## What the drill covers

The drill validates:

- normal live single-flow finalization
- degraded-provider `quorum` behavior where receipt remains unavailable
- compose-level restart/recovery for:
  - `finality`
  - `receipt`
  - `audit`
  - `ingress`
- batch flow finalization after the resilience checks

## 1. Prepare the environment

Copy the example env file:

```bash
cp config/offchain.compose.resilience.env.example .env.offchain.drill
```

Adjust at minimum:

- `WATCHER_AUTH_TOKEN`
- `WATCHER_RPC_URLS`
- `INGRESS_WATCHER_RPC_URLS`
- `RPC_URL`
- `CHAIN_ID`

Recommended for the drill:

- `WATCHER_VERIFICATION_POLICY=quorum`
- `WATCHER_VERIFICATION_MIN_SUCCESS=2`
- at least two configured providers

## 2. Start the compose stack

```bash
docker compose --env-file .env.offchain.drill -f docker-compose.offchain.yml up -d --build
```

Check:

```bash
docker compose --env-file .env.offchain.drill -f docker-compose.offchain.yml ps
```

## 3. Run the drill

### Linux / WSL

```bash
export WATCHER_AUTH_TOKEN=replace-with-resilience-drill-token
export RPC_URL=https://history.denotary.io
export EXPECTED_CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48
export NETWORK_LABEL=deNotary
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=verification
export COMPOSE_ENV_FILE=.env.offchain.drill

./scripts/run-offchain-resilience-drill.sh
```

### Windows PowerShell

```powershell
$env:WATCHER_AUTH_TOKEN = "replace-with-resilience-drill-token"
$env:RPC_URL = "https://history.denotary.io"
$env:EXPECTED_CHAIN_ID = "9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48"
$env:NETWORK_LABEL = "deNotary"
$env:OWNER_ACCOUNT = "verification"
$env:SUBMITTER_ACCOUNT = "verification"
$env:COMPOSE_ENV_FILE = ".env.offchain.drill"

./scripts/run-offchain-resilience-drill.ps1
```

## 4. Jungle4 example

```bash
export WATCHER_AUTH_TOKEN=replace-with-resilience-drill-token
export RPC_URL=https://jungle4.cryptolions.io
export EXPECTED_CHAIN_ID=73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d
export NETWORK_LABEL=Jungle4
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=vadim1111111
export COMPOSE_ENV_FILE=runtime/offchain.compose.jungle4.resilience.env

./scripts/run-offchain-resilience-drill.sh
```

## 5. Output artifacts

By default the drill writes logs into:

- `runtime/live-offchain-resilience-logs`

The underlying live-suite produces:

- step-by-step JSON artifacts
- final `summary.json`

Use these artifacts to confirm:

- degraded `quorum` stayed `included_unverified`
- restart/recovery returned the restarted request to `finalized_verified`
- `receipt` and `audit` remained available after service restart
- `ingress` still prepared requests and completed watcher handoff after restart

## 6. Success criteria

Treat the drill as passed only if:

- the command exits successfully
- the summary marks the run as successful
- the degraded-provider scenario stayed unverified as expected
- the restart/recovery scenario finalized correctly after watcher restart
- receipt and audit remained readable after service restarts
- ingress still prepared and auto-registered requests after restart

## 7. Clean up

```bash
docker compose --env-file .env.offchain.drill -f docker-compose.offchain.yml down
```

To also clear the shared state:

```bash
docker compose --env-file .env.offchain.drill -f docker-compose.offchain.yml down -v
```

## Notes

- this drill assumes the compose stack is already reachable on the local host
- it is best suited for server acceptance checks, testnet rehearsal, and periodic resilience validation
- for the broader production gate, combine it with [docs/denotary-production-rollout.md](/c:/projects/verification-contract/docs/denotary-production-rollout.md:1) and [docs/security-production-checklist.md](/c:/projects/verification-contract/docs/security-production-checklist.md:1)
