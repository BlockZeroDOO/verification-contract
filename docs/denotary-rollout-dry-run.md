# DeNotary Rollout Dry-Run

## Purpose

This runbook describes the pre-rollout dry-run gate for DeNotary.

The dry-run runner can combine:

- contract build
- local service integration tests
- optional live-chain integration tests
- optional on-chain smoke test

Implementation:

- [scripts/run-rollout-dry-run.sh](/c:/projects/verification-contract/scripts/run-rollout-dry-run.sh:1)
- [scripts/run-rollout-dry-run.ps1](/c:/projects/verification-contract/scripts/run-rollout-dry-run.ps1:1)

## Default behavior

By default, the dry-run is conservative:

- it builds artifacts
- it runs the local service integration suite
- it does not touch a live chain unless you explicitly enable that step

That means the default invocation is safe to use as a local preflight gate.

## Linux / WSL run

```bash
./scripts/run-rollout-dry-run.sh
```

## PowerShell run

```powershell
./scripts/run-rollout-dry-run.ps1
```

## Enable live-chain validation

deNotary.io example:

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
RUN_LIVE_CHAIN_INTEGRATION=true \
RUN_ONCHAIN_SMOKE=true \
./scripts/run-rollout-dry-run.sh
```

Jungle4 example:

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
RPC_URL=https://jungle4.api.eosnation.io \
EXPECTED_CHAIN_ID=73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d \
NETWORK_LABEL=Jungle4 \
RUN_LIVE_CHAIN_INTEGRATION=true \
RUN_ONCHAIN_SMOKE=true \
./scripts/run-rollout-dry-run.sh
```

## Useful environment variables

- `BUILD_BEFORE_DRY_RUN=true|false`
- `BUILD_PROFILE=release|testnet`
- `BUILD_TARGETS="verification dfs"`
- `RUN_SERVICE_INTEGRATION=true|false`
- `RUN_LIVE_CHAIN_INTEGRATION=true|false`
- `RUN_ONCHAIN_SMOKE=true|false`
- `RPC_URL`
- `EXPECTED_CHAIN_ID`
- `NETWORK_LABEL`
- `OWNER_ACCOUNT`
- `SUBMITTER_ACCOUNT`
- `WATCHER_AUTH_TOKEN`

## Recommended rollout gate

For a serious pre-release pass, run:

1. build artifacts with the intended profile
2. pass local service integration
3. pass live-chain integration against the target network
4. pass on-chain smoke against the deployed `verification`
5. verify tables manually with `cleos get table`

## Notes

- the live-chain step uses [docs/denotary-live-chain-integration.md](/c:/projects/verification-contract/docs/denotary-live-chain-integration.md:1)
- the smoke step uses [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- if `WATCHER_AUTH_TOKEN` is set, the dry-run passes it into the live-chain watcher flow
