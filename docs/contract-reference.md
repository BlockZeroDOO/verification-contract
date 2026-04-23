# Verification Contract Reference

## Supported Contracts

This repository supports three on-chain contracts:

- `verif`
- `verifbill`
- `verifretpay`

`verif` is the only supported registry.

`verifbill` is the enterprise payment contract.

`verifretpay` is the retail payment contract.

## `verif`

### Purpose

`verif` is the unified registry and anchoring contract.

It is responsible for:

- single-record anchoring
- batch anchoring
- request uniqueness
- validation against stored schema and policy rows
- internal anchoring entrypoints for payment contracts

### Tables

#### `schemas`

Fields:

- `id`
- `version`
- `canonicalization_hash`
- `hash_policy`
- `active`
- `created_at`
- `updated_at`

#### `policies`

Fields:

- `id`
- `allow_single`
- `allow_batch`
- `active`
- `created_at`
- `updated_at`

#### `commitments`

Fields:

- `id`
- `submitter`
- `schema_id`
- `policy_id`
- `object_hash`
- `billable_bytes`
- `billable_kib`
- `external_ref`
- `request_key`
- `created_at`

#### `batches`

Fields:

- `id`
- `submitter`
- `root_hash`
- `leaf_count`
- `schema_id`
- `policy_id`
- `manifest_hash`
- `billable_bytes`
- `billable_kib`
- `external_ref`
- `request_key`
- `created_at`

#### `counters`

Fields:

- `next_commitment_id`
- `next_batch_id`

#### `authsources`

Fields:

- `billing_account`
- `retail_payment_account`

### Actions

#### Anchoring

- `billsubmit(submitter, schema_id, policy_id, object_hash, external_ref)`
- `retailsub(submitter, schema_id, policy_id, object_hash, external_ref)`
- `billbatch(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref)`
- `retailbatch(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref)`

### Validation Rules

Contract-only runtime:

- `billsubmit(...)` and `billbatch(...)` require `verifbill` authority
- `retailsub(...)` and `retailbatch(...)` require `verifretpay` authority
- these internal entrypoints perform the same registry validation and uniqueness checks
- they are the active anchoring runtime for the supported payment contracts
- `billable_bytes` and `billable_kib` are computed inside `verif` from the canonical registry request shape
- `verif` relies on already provisioned `schemas` and `policies` rows and does not expose runtime governance actions on the live surface

### Authorization Wiring

`verif` allows contract-only anchoring from:

- `verifbill`
- `verifretpay`

Caller authorization is read from the `authsources` singleton.

If the singleton is absent, `verif` defaults to:

- `billing_account = verifbill`
- `retail_payment_account = verifretpay`

## `verifbill`

### Purpose

`verifbill` is the enterprise payment contract.

It is responsible for:

- accepted billing tokens
- plans
- packs
- entitlements
- atomic enterprise billing
- inline anchoring into `verif`

### Tables

- `billtokens`
- `plans`
- `packs`
- `entitlements`
- `billcounters`

### Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setplan(plan_code, token_contract, price, duration_sec, included_kib, active)`
- `deactplan(plan_id)`
- `setpack(pack_code, token_contract, price, included_kib, active)`
- `deactpack(pack_id)`
- `submit(payer, submitter, schema_id, policy_id, object_hash, external_ref)`
- `submitroot(payer, submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref)`
- `cleanentls(limit)`
- `setverifacct(verification_account)`
- `withdraw(token_contract, to, quantity, memo)`

### Purchase Flow

Enterprise purchases are funded through:

- `eosio.token::transfer -> verifbill`

Current memo families:

```text
plan|payer|plan_code
pack|payer|pack_code
```

1. enterprise payer buys plan or pack
2. `verifbill::submit(...)` or `submitroot(...)` computes the canonical registry request size
3. `verifbill::submit(...)` or `submitroot(...)` validates payer entitlement
4. `verifbill` calls `verif::billsubmit(...)` or `billbatch(...)`
5. `verifbill` burns the matching `KiB` after successful inline anchoring

Maintenance:

- `cleanentls(limit)` removes expired or exhausted `entitlements`

Entitlement selection:

- `submit(...)` and `submitroot(...)` spend the eligible entitlement with the nearest `expires_at`
- non-expiring pack entitlements are used only when no sooner-expiring entitlement can satisfy the request
- request size is contract-computed from the canonical serialized request to `verif`

### Authority Model

- governance config is controlled by contract authority
- `submit(...)` and `submitroot(...)` require real payer authority
- current contract-only enterprise flow requires `payer == submitter`
- account delegation should be handled by native Antelope permissions, not by contract state

## `verifretpay`

### Purpose

`verifretpay` is the supported retail payment contract.

It is responsible for:

- accepted retail tokens
- exact size-based tariffs
- atomic retail payment
- inline anchoring into `verif`

### Tables

- `rtltokens`
- `rtltariffs`
- `rtlcounters`

### Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setprice(mode, token_contract, price_per_kib)`
- `setverifacct(verification_account)`
- `withdraw(token_contract, to, quantity, memo)`

### Retail Payment Flow

Retail payment is funded through:

- `eosio.token::transfer -> verifretpay`

Supported atomic memo formats:

```text
single|submitter|schema_id|policy_id|object_hash|external_ref_hex
batch|submitter|schema_id|policy_id|root_hash|leaf_count|manifest_hash|external_ref_hex
```

Rules:

- exact payment only
- payment is derived from contract-computed `billable_kib * price_per_kib`
- underpayment is rejected
- wrong token is rejected
- mode mismatch is rejected
- request size is computed by `verifretpay` from the canonical registry request shape
- payer currently must match submitter
- atomic retail transfer performs inline anchoring and does not create pending auth rows

1. retail payer transfers exact amount to `verifretpay`
2. `verifretpay` validates atomic memo payload and exact tariff
3. `verifretpay` calls `verif::retailsub(...)` or `retailbatch(...)`
4. transaction finalizes without creating any pending retail auth row

## Deployment Names

Canonical names:

- `verif`
- `verifbill`
- `verifretpay`

Build outputs:

- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`
- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`
- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`

## Primary Docs

- [docs/denotary-deploy.md](/c:/projects/verification-contract/docs/denotary-deploy.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [docs/billing-deploy.md](/c:/projects/verification-contract/docs/billing-deploy.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- [docs/billing-onchain-smoke.md](/c:/projects/verification-contract/docs/billing-onchain-smoke.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/unified-retail-onchain-smoke.md](/c:/projects/verification-contract/docs/unified-retail-onchain-smoke.md:1)

## Summary

Supported production model:

- `verif` as the only registry
- `verifbill` as the enterprise payment model
- `verifretpay` as the retail payment model
