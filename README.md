# DeNotary Verification Contract

This repository is the canonical home of the on-chain verification contracts:

- `verif`
- `verifbill`
- `verifretpay`
- `verifretail`

Repository boundary:

- this repository owns the `verif`, `verifbill`, `verifretpay`, and `verifretail` contracts, their Ricardian files, and contract-facing runbooks
- `deNotary` owns the off-chain backend and operational runtime around the contract
- `decentralized_storage\contracts\dfs` owns the DFS contract

## Scope

The unified `verif` contract covers:

- KYC access control
- schema registry
- policy registry
- single-record anchoring
- batch anchoring
- commitment and batch lifecycle tracking
- clean unified anchoring surface with no legacy proof-payment path

The retail payment `verifretpay` contract covers:

- wallet-first exact payment
- retail tariffs
- one-time retail usage authorizations for `verif`
- no deposit model

The compatibility `verifretail` contract currently covers:

- the same verification core model
- wallet-first `atomic pay + submit`
- exact tariff-governed retail payment receipts
- no deposit model

The enterprise billing `verifbill` contract covers:

- accepted enterprise billing tokens
- subscription plans
- usage packs
- delegated submitter rights
- one-time enterprise usage authorizations

## On-chain tables

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`
- `counters`

## Core actions

Registry governance:

- `issuekyc(...)`
- `renewkyc(...)`
- `revokekyc(...)`
- `suspendkyc(...)`
- `addschema(...)`
- `updateschema(...)`
- `deprecate(...)`
- `setpolicy(...)`
- `enablezk(...)`
- `disablezk(...)`

Anchoring core:

- `submit(...)`
- `supersede(...)`
- `revokecmmt(...)`
- `expirecmmt(...)`
- `submitroot(...)`
- `linkmanifest(...)`
- `closebatch(...)`

Operational action:

- `withdraw(...)`

## Build

Linux / WSL:

```bash
./scripts/build-enterprise.sh
./scripts/build-testnet.sh
./scripts/build-retail.sh
./scripts/build-retpay.sh
./scripts/build-billing.sh
./scripts/build-release.sh
```

PowerShell:

```powershell
./scripts/build-enterprise.ps1
./scripts/build-testnet.ps1
./scripts/build-retail.ps1
./scripts/build-retpay.ps1
./scripts/build-billing.ps1
./scripts/build-release.ps1
```

Expected artifacts:

- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`
- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`
- `dist/verifretail/verifretail.wasm`
- `dist/verifretail/verifretail.abi`
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
- [docs/retail-deploy.md](/c:/projects/verification-contract/docs/retail-deploy.md:1)
- [scripts/deploy-billing-denotary.sh](/c:/projects/verification-contract/scripts/deploy-billing-denotary.sh:1)
- [scripts/deploy-retpay-denotary.sh](/c:/projects/verification-contract/scripts/deploy-retpay-denotary.sh:1)
- [scripts/deploy-retail-denotary.sh](/c:/projects/verification-contract/scripts/deploy-retail-denotary.sh:1)

Jungle4:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [scripts/deploy-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-enterprise-jungle4.sh:1)
- [scripts/deploy-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-jungle4.sh:1)
- [scripts/deploy-billing-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-billing-jungle4.sh:1)
- [scripts/deploy-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-retpay-jungle4.sh:1)
- [scripts/deploy-retail-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-retail-jungle4.sh:1)

## On-chain smoke

- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- [docs/billing-onchain-smoke.md](/c:/projects/verification-contract/docs/billing-onchain-smoke.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-jungle4.sh:1)
- [scripts/smoke-test-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-denotary.sh:1)
- [scripts/smoke-test-billing.sh](/c:/projects/verification-contract/scripts/smoke-test-billing.sh:1)
- [scripts/smoke-test-billing-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-billing-jungle4.sh:1)
- [scripts/smoke-test-billing-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-billing-denotary.sh:1)
- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-jungle4.sh:1)
- [scripts/smoke-test-retpay-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-denotary.sh:1)
- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-jungle4.sh:1)
- [scripts/smoke-test.sh](/c:/projects/verification-contract/scripts/smoke-test.sh:1)
- [scripts/smoke-test-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-denotary.sh:1)
- [scripts/smoke-test-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-retail.sh:1)

## Contract docs

- [docs/enterprise-billing-architecture.md](/c:/projects/verification-contract/docs/enterprise-billing-architecture.md:1)
- [docs/contract-reference.md](/c:/projects/verification-contract/docs/contract-reference.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/denotary-l1-contract-core.md](/c:/projects/verification-contract/docs/denotary-l1-contract-core.md:1)
- [docs/adr/0002-batch-proof-storage.md](/c:/projects/verification-contract/docs/adr/0002-batch-proof-storage.md:1)
- [docs/adr/0003-clean-deployment-cutover.md](/c:/projects/verification-contract/docs/adr/0003-clean-deployment-cutover.md:1)

## Notes

- off-chain services and runtime operations were moved to `C:\projects\deNotary`
- the DFS contract was moved to `C:\projects\decentralized_storage\contracts\dfs`

## License

MIT
