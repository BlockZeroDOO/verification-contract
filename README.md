# DeNotary Verification Contracts

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

The basic idea is that the verif smart contract remains trusted; its key is burned. The verifbill and verifretpay contracts are untrusted, so after publishing a record in verif, the record must be linked to the original, which allows the record to be trusted in the future. We have developed a full software cycle for data notarization, verification, and auditing.

This repository is the canonical home of the supported on-chain verification model:

- `verif`
- `verifbill`
- `verifretpay`

Repository boundary:

- this repository owns the on-chain verification contracts
- `C:\projects\deNotary` owns the off-chain backend and runtime
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Supported Model

### `verif`

Unified anchoring registry for:

- single-record anchoring
- batch anchoring
- validation against pre-provisioned schema and policy rows
- internal entrypoints from `verifbill` and `verifretpay`

### `verifbill`

Enterprise billing contract for:

- accepted billing tokens
- plans and packs
- atomic enterprise billing into `verif`

### `verifretpay`

Retail payment contract for:

- exact on-chain retail payment
- atomic retail billing into `verif`
- wallet-first client-side transaction flow without deposits

## Build

Linux / WSL:

```bash
./scripts/build-testnet.sh verif
./scripts/build-billing.sh
./scripts/build-retpay.sh
```

PowerShell:

```powershell
./scripts/build-testnet.ps1 verif
./scripts/build-billing.ps1
./scripts/build-retpay.ps1
```

Expected artifacts:

- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`
- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`
- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`

## Deploy

- [docs/billing-deploy.md](/c:/projects/verification-contract/docs/billing-deploy.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [docs/denotary-deploy.md](/c:/projects/verification-contract/docs/denotary-deploy.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [docs/jungle4-validation-report.md](/c:/projects/verification-contract/docs/jungle4-validation-report.md:1)

## Operations

- [docs/verifbill-plan-admin.md](/c:/projects/verification-contract/docs/verifbill-plan-admin.md:1)
- [docs/verifretpay-price-admin.md](/c:/projects/verification-contract/docs/verifretpay-price-admin.md:1)
- [docs/verifbill-plan-purchase.md](/c:/projects/verification-contract/docs/verifbill-plan-purchase.md:1)
- [docs/corporate-pricing-grid.md](/c:/projects/verification-contract/docs/corporate-pricing-grid.md:1)

## Smoke

- [docs/billing-onchain-smoke.md](/c:/projects/verification-contract/docs/billing-onchain-smoke.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/unified-retail-onchain-smoke.md](/c:/projects/verification-contract/docs/unified-retail-onchain-smoke.md:1)
- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)

## Reference

- [docs/contract-reference.md](/c:/projects/verification-contract/docs/contract-reference.md:1)
- [docs/canonical-request-size-plan.md](/c:/projects/verification-contract/docs/canonical-request-size-plan.md:1)
- [docs/verif-runtime-freeze-release-note.md](/c:/projects/verification-contract/docs/verif-runtime-freeze-release-note.md:1)
- [docs/external-auditor-verification.md](/c:/projects/verification-contract/docs/external-auditor-verification.md:1)
- [docs/external-auditor-runbook.md](/c:/projects/verification-contract/docs/external-auditor-runbook.md:1)

## Notes

- `verif` is the only supported registry
- the live `verif` surface is frozen to runtime anchoring entrypoints and does not expose self-managed registry or treasury actions
- `verifbill` is the supported enterprise payment model
- `verifretpay` is the supported retail payment model
- latest Jungle4-validated layout is `decentrfstor -> verif`, `vadim1111111 -> verifbill`, `verification -> verifretpay`

## License

MIT
