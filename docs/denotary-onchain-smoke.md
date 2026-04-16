# DeNotary On-Chain Smoke Tests

## Purpose

These smoke tests validate the current on-chain production paths for:

- `KYC`
- `Schema`
- `Policy`
- `Commitment`
- `Batch`
- enterprise authorization
- unified retail authorization

Scripts:

- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-billing.sh](/c:/projects/verification-contract/scripts/smoke-test-billing.sh:1)
- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)

## Prerequisites

- deployed `verifbill` and `verif` contracts for enterprise validation
- `cleos`
- `jq`
- imported keys for:
  - billing owner account
  - contract owner account
  - submitter account

## Required env vars for `verif`

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export VERIFICATION_BILLING_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
export OWNER_ACCOUNT=verif
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

Standalone retail payment smoke:

```bash
./scripts/smoke-test-retpay.sh
```

Unified retail smoke:

```bash
./scripts/smoke-test-unified-retail.sh
```

Standalone billing smoke:

```bash
./scripts/smoke-test-billing.sh
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
- enterprise billing authorization via `verifbill`

## Notes

- run these scripts against a dedicated test account or test deployment
- `schema_id` and `policy_id` are timestamp-derived to avoid collisions between runs
- `commitment` and `batch` IDs are discovered by `external_ref`, so the scripts are not pinned to `id = 1`
- table polling uses `get table --limit 1000` to avoid missing rows on larger registries
- enterprise wrappers are documented separately in [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- billing smoke is documented separately in [docs/billing-onchain-smoke.md](/c:/projects/verification-contract/docs/billing-onchain-smoke.md:1)
- retail payment smoke is documented separately in [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- unified retail smoke is documented separately in [docs/unified-retail-onchain-smoke.md](/c:/projects/verification-contract/docs/unified-retail-onchain-smoke.md:1)
