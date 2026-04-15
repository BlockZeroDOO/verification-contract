# DeNotary On-Chain Smoke Tests

## Purpose

These smoke tests validate the current on-chain production paths for:

- `KYC`
- `Schema`
- `Policy`
- `Commitment`
- `Batch`

Scripts:

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-retail.sh:1)

## Prerequisites

- deployed `verification` contract
- `cleos`
- `jq`
- imported keys for:
  - contract owner account
  - submitter account

## Required env vars for `verification`

```bash
export RPC_URL=https://your-rpc
export VERIFICATION_ACCOUNT=verification
export OWNER_ACCOUNT=verification
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
./scripts/smoke-test-onchain.sh
```

Legacy compatibility wrapper:

```bash
./scripts/smoke-test.sh
```

It now delegates to `smoke-test-onchain.sh`, because the legacy proof-payment path in
`verification` is intentionally disabled.

Retail smoke:

```bash
./scripts/smoke-test-retail.sh
```

## What the verification smoke validates

- `issuekyc`
- `renewkyc`
- `addschema`
- `setpolicy` for single and batch flows
- `submit`
- duplicate single request rejection
- zero `object_hash` rejection
- disabled legacy `record` and `setpaytoken` actions
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
- retail smoke is documented separately in [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
