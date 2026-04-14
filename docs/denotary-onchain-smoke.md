# DeNotary On-Chain Smoke Test

## Purpose

Этот smoke test проверяет уже добавленные on-chain actions для:

- `KYC`
- `Schema`
- `Policy`
- `Commitment`
- `Batch`

Скрипт находится в [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1).

## Prerequisites

- развернут контракт `verification`
- `cleos`
- `jq`
- импортированы ключи для:
  - контрактного owner account
  - submitter account

## Required env vars

```bash
export RPC_URL=https://your-rpc
export VERIFICATION_ACCOUNT=verification
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=someuser
```

Опционально:

```bash
export KYC_PROVIDER=denotary-kyc
export KYC_JURISDICTION=EU
export KYC_LEVEL=2
export KYC_EXPIRES_AT=2030-01-01T00:00:00
```

## Run

```bash
./scripts/smoke-test-onchain.sh
```

## What it validates

- `issuekyc`
- `renewkyc`
- `addschema`
- `setpolicy` для single и batch
- `submit`
- duplicate single request rejection
- `supersede` с явным `successor_id`
- `revokecmmt`
- `expirecmmt`
- `submitroot`
- duplicate batch request rejection
- guard на `closebatch` до `linkmanifest`
- `linkmanifest`
- `closebatch`

## Notes

- скрипт лучше запускать на выделенном тестовом аккаунте/контракте
- `schema_id` и `policy_id` генерируются от текущего timestamp, чтобы не конфликтовать между прогонами
- `commitment` и `batch` IDs теперь ищутся по `external_ref`, поэтому скрипт не привязан к `id = 1`
