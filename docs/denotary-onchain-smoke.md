# On-Chain Smoke Tests

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

Supported smoke coverage:

- enterprise path: `verif + verifbill`
- retail path: `verif + verifretpay`

## Scripts

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-billing.sh](/c:/projects/verification-contract/scripts/smoke-test-billing.sh:1)
- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)

## Coverage

### Enterprise

- pre-provisioned schema and policy rows
- existing `authsources` row or canonical default caller names
- billing pack purchase
- `verifbill::submit -> verif::billsubmit`
- `verifbill::submitroot -> verif::billbatch`
- persisted `billable_bytes`
- persisted `billable_kib`
- contract-computed canonical request size
- duplicate and zero-hash rejection

### Retail

- retail token and tariff setup
- pre-provisioned schema and policy rows
- existing `authsources` row or canonical default caller names
- atomic `transfer -> verifretpay`
- `verif::retailsub`
- `verif::retailbatch`
- persisted `billable_bytes`
- persisted `billable_kib`
- contract-computed canonical request size
- duplicate and tariff-validation rejection

## DFS Boundary

DFS smoke is outside this repository:

- `C:\projects\decentralized_storage\contracts\dfs\scripts\smoke-test-dfs.sh`
