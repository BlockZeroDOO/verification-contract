# DeNotary On-Chain Smoke Tests

## Purpose

These smoke tests validate the current on-chain production paths for:

- `KYC`
- `Schema`
- `Policy`
- `Commitment`
- `Batch`
- DFS quote-gated storage payments

Scripts:

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-dfs.sh](/c:/projects/verification-contract/scripts/smoke-test-dfs.sh:1)

## Prerequisites

- deployed `verification` contract
- deployed `dfs` contract if you want to run the DFS payment smoke
- `cleos`
- `jq`
- imported keys for:
  - contract owner account
  - submitter account
  - DFS settlement authority and DFS payer account for the storage-payment smoke

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

## Required env vars for `dfs`

```bash
export RPC_URL=https://your-rpc
export DFS_ACCOUNT=dfs
export DFS_SETTLEMENT_ACCOUNT=dfs
export DFS_PAYER_ACCOUNT=someuser
```

Optional:

```bash
export PAYMENT_TOKEN_CONTRACT=eosio.token
export PAYMENT_AMOUNT="1.0000 EOS"
```

## Run

Verification smoke:

```bash
./scripts/smoke-test-onchain.sh
```

DFS payment smoke:

```bash
./scripts/smoke-test-dfs.sh
```

Legacy compatibility wrapper:

```bash
./scripts/smoke-test.sh
```

It now delegates to `smoke-test-onchain.sh`, because the legacy proof-payment path in
`verification` is intentionally disabled.

## What the verification smoke validates

- `issuekyc`
- `renewkyc`
- `addschema`
- `setpolicy` for single and batch flows
- `submit`
- duplicate single request rejection
- `supersede` with explicit `successor_id`
- `revokecmmt`
- `expirecmmt`
- `submitroot`
- duplicate batch request rejection
- guard on `closebatch` before `linkmanifest`
- `linkmanifest`
- `closebatch`

## What the DFS smoke validates

- `mkstorquote`
- matching `storage|<payment_reference>|<manifest_hash>` transfer acceptance
- receipt creation in `received` status
- quote transition from `open` to `consumed`
- duplicate use of the same `payment_reference` is rejected

## Notes

- run these scripts against a dedicated test account or test deployment
- `schema_id` and `policy_id` are timestamp-derived to avoid collisions between runs
- `commitment` and `batch` IDs are discovered by `external_ref`, so the scripts are not pinned to `id = 1`
- DFS storage payments now require an explicit open quote before the payer transfer is accepted
