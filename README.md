# DeNotary Verification Contract

This repository is the canonical home of the on-chain verification contracts:

- `verif`
- `verifbill`
- `verifretpay`

Repository boundary:

- this repository owns the `verif`, `verifbill`, and `verifretpay` contracts, plus the deprecated compatibility contract `verifretail`
- `deNotary` owns the off-chain backend and operational runtime around the contract
- `decentralized_storage\contracts\dfs` owns the DFS contract

## Scope

The unified `verif` contract covers:

- schema registry
- policy registry
- single-record anchoring
- batch anchoring
- commitment and batch lifecycle tracking
- clean unified anchoring surface with no legacy proof-payment path
- external authorization from:
  - `verifbill`
  - `verifretpay`

The retail payment `verifretpay` contract covers:

- wallet-first exact payment
- retail tariffs
- one-time retail usage authorizations for `verif`
- no deposit model

The enterprise billing `verifbill` contract covers:

- accepted enterprise billing tokens
- subscription plans
- usage packs
- one-time enterprise usage authorizations

## On-chain tables

- `schemas`
- `policies`
- `commitments`
- `batches`
- `counters`

## Core actions

Registry governance:

- `addschema(...)`
- `updateschema(...)`
- `deprecate(...)`
- `setpolicy(...)`

Anchoring core:

- `submit(...)`
- `submitroot(...)`

Operational action:

- `withdraw(...)`

## Build

Linux / WSL:

```bash
./scripts/build-enterprise.sh
./scripts/build-testnet.sh
./scripts/build-retpay.sh
./scripts/build-billing.sh
./scripts/build-release.sh
```

PowerShell:

```powershell
./scripts/build-enterprise.ps1
./scripts/build-testnet.ps1
./scripts/build-retpay.ps1
./scripts/build-billing.ps1
./scripts/build-release.ps1
```

Expected artifacts:

- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`
- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`
- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`

## Deploy

deNotary:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/denotary-deploy.md](/c:/projects/verification-contract/docs/denotary-deploy.md:1)
- [docs/billing-deploy.md](/c:/projects/verification-contract/docs/billing-deploy.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [scripts/deploy-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/deploy-enterprise-denotary.sh:1)
- [scripts/deploy-denotary.sh](/c:/projects/verification-contract/scripts/deploy-denotary.sh:1)
- [scripts/deploy-billing-denotary.sh](/c:/projects/verification-contract/scripts/deploy-billing-denotary.sh:1)
- [scripts/deploy-retpay-denotary.sh](/c:/projects/verification-contract/scripts/deploy-retpay-denotary.sh:1)

Jungle4:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [scripts/deploy-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-enterprise-jungle4.sh:1)
- [scripts/deploy-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-jungle4.sh:1)
- [scripts/deploy-billing-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-billing-jungle4.sh:1)
- [scripts/deploy-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-retpay-jungle4.sh:1)

## On-chain smoke

- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- [docs/billing-onchain-smoke.md](/c:/projects/verification-contract/docs/billing-onchain-smoke.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-jungle4.sh:1)
- [scripts/smoke-test-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-denotary.sh:1)
- [scripts/smoke-test-billing.sh](/c:/projects/verification-contract/scripts/smoke-test-billing.sh:1)
- [scripts/smoke-test-billing-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-billing-jungle4.sh:1)
- [scripts/smoke-test-billing-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-billing-denotary.sh:1)
- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-jungle4.sh:1)
- [scripts/smoke-test-retpay-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-denotary.sh:1)
- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)
- [scripts/smoke-test-unified-retail-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail-jungle4.sh:1)
- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-jungle4.sh:1)
- [scripts/smoke-test.sh](/c:/projects/verification-contract/scripts/smoke-test.sh:1)
- [scripts/smoke-test-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-denotary.sh:1)

## Contract docs

- [docs/enterprise-billing-architecture.md](/c:/projects/verification-contract/docs/enterprise-billing-architecture.md:1)
- [docs/contract-reference.md](/c:/projects/verification-contract/docs/contract-reference.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/unified-retail-onchain-smoke.md](/c:/projects/verification-contract/docs/unified-retail-onchain-smoke.md:1)
- [docs/denotary-l1-contract-core.md](/c:/projects/verification-contract/docs/denotary-l1-contract-core.md:1)
- [docs/adr/0002-batch-proof-storage.md](/c:/projects/verification-contract/docs/adr/0002-batch-proof-storage.md:1)
- [docs/adr/0003-clean-deployment-cutover.md](/c:/projects/verification-contract/docs/adr/0003-clean-deployment-cutover.md:1)

## Compatibility path

`verifretail` remains in the repository only as a compatibility path during migration to `verif + verifretpay`.

Compatibility-only assets:

- [docs/retail-deploy.md](/c:/projects/verification-contract/docs/retail-deploy.md:1)
- [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
- [scripts/build-retail.sh](/c:/projects/verification-contract/scripts/build-retail.sh:1)
- [scripts/build-retail.ps1](/c:/projects/verification-contract/scripts/build-retail.ps1:1)
- [scripts/deploy-retail-denotary.sh](/c:/projects/verification-contract/scripts/deploy-retail-denotary.sh:1)
- [scripts/deploy-retail-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-retail-jungle4.sh:1)
- [scripts/smoke-test-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-retail.sh:1)
- [scripts/smoke-test-retail-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retail-denotary.sh:1)
- [scripts/smoke-test-retail-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retail-jungle4.sh:1)
- `dist/verifretail/verifretail.wasm`
- `dist/verifretail/verifretail.abi`

## Notes

- off-chain services and runtime operations were moved to `C:\projects\deNotary`
- the DFS contract was moved to `C:\projects\decentralized_storage\contracts\dfs`

## License

MIT
