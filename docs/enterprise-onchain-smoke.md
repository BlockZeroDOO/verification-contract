# Enterprise On-Chain Smoke Tests

## Purpose

These smoke tests validate the enterprise verification contract surface for:

- `Schema`
- `Policy`
- `Commitment`
- `Batch`
- `Enterprise Billing Authorization`
- `Authorization Wiring`

Scripts:

- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-denotary.sh:1)
- [scripts/smoke-test-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-jungle4.sh:1)

The enterprise wrappers delegate to the canonical on-chain smoke:

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)

## Prerequisites

- deployed `verif` contract
- deployed `verifbill` contract
- `cleos`
- `jq`
- imported keys for:
  - enterprise contract owner account
  - billing contract owner account
  - submitter account

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export OWNER_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
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

- `addschema`
- minimal `setpolicy` for single and batch flows
- `verifbill::settoken`
- `verif::setauthsrcs`
- `verifbill::setpack`
- `verifbill::setverifacct`
- pack purchase via `transfer -> verifbill`
- `verifbill::use` before every enterprise `submit` and `submitroot`
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

- enterprise smoke now validates the combined `verif + verifbill` path
- for Jungle4, using a separate `READ_RPC_URL` for table polling is recommended
- the smoke uses `get table --limit 1000` to avoid false negatives from paginated registry tables
- retail smoke is documented separately in [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
