# DeNotary Verification Contract

This repository is the canonical home of the on-chain verification contracts:

- `verification`
- `verification_retail`

Repository boundary:

- this repository owns the `verification` contract, its Ricardian files, and contract-facing runbooks
- `deNotary` owns the off-chain backend and operational runtime around the contract
- `decentralized_storage\contracts\dfs` owns the DFS contract

## Scope

The enterprise `verification` contract covers:

- KYC access control
- schema registry
- policy registry
- single-record anchoring
- batch anchoring
- commitment and batch lifecycle tracking
- explicit disablement of the legacy paid proof path

The retail `verification_retail` contract covers:

- the same verification core model
- wallet-first `atomic pay + submit`
- exact tariff-governed retail payment receipts
- no deposit model

## On-chain tables

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`
- `counters`
- legacy disabled tables `proofs` and `paytokens`

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

Legacy compatibility actions retained only as disabled stubs:

- `record(...)`
- `setpaytoken(...)`
- `rmpaytoken(...)`

Operational action:

- `withdraw(...)`

## Build

Linux / WSL:

```bash
./scripts/build-enterprise.sh
./scripts/build-testnet.sh
./scripts/build-retail.sh
./scripts/build-release.sh
```

PowerShell:

```powershell
./scripts/build-enterprise.ps1
./scripts/build-testnet.ps1
./scripts/build-retail.ps1
./scripts/build-release.ps1
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`

## Deploy

deNotary:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/denotary-deploy.md](/c:/projects/verification-contract/docs/denotary-deploy.md:1)
- [scripts/deploy-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/deploy-enterprise-denotary.sh:1)
- [scripts/deploy-denotary.sh](/c:/projects/verification-contract/scripts/deploy-denotary.sh:1)
- [docs/retail-deploy.md](/c:/projects/verification-contract/docs/retail-deploy.md:1)
- [scripts/deploy-retail-denotary.sh](/c:/projects/verification-contract/scripts/deploy-retail-denotary.sh:1)

Jungle4:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [scripts/deploy-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-enterprise-jungle4.sh:1)
- [scripts/deploy-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-jungle4.sh:1)
- [scripts/deploy-retail-jungle4.sh](/c:/projects/verification-contract/scripts/deploy-retail-jungle4.sh:1)

## On-chain smoke

- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)
- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-jungle4.sh:1)
- [scripts/smoke-test-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-denotary.sh:1)
- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-jungle4.sh:1)
- [scripts/smoke-test.sh](/c:/projects/verification-contract/scripts/smoke-test.sh:1)
- [scripts/smoke-test-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-denotary.sh:1)
- [scripts/smoke-test-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-retail.sh:1)

## Contract docs

- [docs/denotary-l1-contract-core.md](/c:/projects/verification-contract/docs/denotary-l1-contract-core.md:1)
- [docs/adr/0002-batch-proof-storage.md](/c:/projects/verification-contract/docs/adr/0002-batch-proof-storage.md:1)
- [docs/adr/0003-clean-deployment-cutover.md](/c:/projects/verification-contract/docs/adr/0003-clean-deployment-cutover.md:1)

## Notes

- off-chain services and runtime operations were moved to `C:\projects\deNotary`
- the DFS contract was moved to `C:\projects\decentralized_storage\contracts\dfs`

## License

MIT
