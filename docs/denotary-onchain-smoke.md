# DeNotary On-Chain Smoke Tests

## Purpose

These smoke tests validate the current on-chain production paths for:

- `KYC`
- `Schema`
- `Policy`
- `Commitment`
- `Batch`

Scripts:

- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-retail.sh:1)

## Prerequisites

- deployed `verifent` contract
- `cleos`
- `jq`
- imported keys for:
  - contract owner account
  - submitter account

## Required env vars for `verifent`

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export VERIFICATION_ACCOUNT=verifent
export OWNER_ACCOUNT=verifent
export SUBMITTER_ACCOUNT=someuser
```

Optional:

```bash
export KYC_PROVIDER=denotary-kyc
export KYC_JURISDICTION=EU
export KYC_LEVEL=2
export KYC_EXPIRES_AT=2030-01-01T00:00:00
```

## DFS boundary

DFS quote-gated storage payment smoke is no longer owned by this repository.

Use:

- `C:\projects\decentralized_storage\contracts\dfs\scripts\smoke-test-dfs.sh`
- `C:\projects\decentralized_storage\contracts\dfs\docs\dfs-testnet-bootstrap.md`

## Run

Verification smoke:

```bash
./scripts/smoke-test-enterprise.sh
```

Canonical underlying enterprise smoke:

```bash
./scripts/smoke-test-onchain.sh
```

Legacy compatibility wrapper:

```bash
./scripts/smoke-test.sh
```

It now delegates directly to `smoke-test-onchain.sh`.

Retail smoke:

```bash
./scripts/smoke-test-retail.sh
```

## What the enterprise smoke validates

- `issuekyc`
- `renewkyc`
- `addschema`
- `setpolicy` for single and batch flows
- `submit`
- duplicate single request rejection
- zero `object_hash` rejection
- `supersede` with explicit `successor_id`
- `revokecmmt`
- `expirecmmt`
- `submitroot`
- duplicate batch request rejection
- guard on `closebatch` before `linkmanifest`
- `linkmanifest`
- `closebatch`

## Notes

- run these scripts against a dedicated test account or test deployment
- `schema_id` and `policy_id` are timestamp-derived to avoid collisions between runs
- `commitment` and `batch` IDs are discovered by `external_ref`, so the scripts are not pinned to `id = 1`
- table polling uses `get table --limit 1000` to avoid missing rows on larger registries
- enterprise wrappers are documented separately in [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- retail smoke is documented separately in [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
