# Enterprise On-Chain Smoke Tests

## Purpose

These smoke tests validate the enterprise verification contract surface for:

- `KYC`
- `Schema`
- `Policy`
- `Commitment`
- `Batch`

Scripts:

- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-denotary.sh:1)
- [scripts/smoke-test-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-jungle4.sh:1)

The enterprise wrappers delegate to the canonical on-chain smoke:

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)

## Prerequisites

- deployed `verification` contract
- `cleos`
- `jq`
- imported keys for:
  - contract owner account
  - submitter account

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export VERIFICATION_ACCOUNT=verification
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=someuser
```

## Run

Generic enterprise smoke:

```bash
./scripts/smoke-test-enterprise.sh
```

Jungle4:

```bash
./scripts/smoke-test-enterprise-jungle4.sh
```

deNotary:

```bash
./scripts/smoke-test-enterprise-denotary.sh
```

## What the enterprise smoke validates

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

- enterprise smoke validates the `verification` contract, which is the current deployment target for `verification_enterprise`
- for Jungle4, using a separate `READ_RPC_URL` for table polling is recommended
- the smoke uses `get table --limit 1000` to avoid false negatives from paginated registry tables
- retail smoke is documented separately in [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
