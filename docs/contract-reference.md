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

- schema registry
- policy registry
- single-record anchoring
- batch anchoring
- request uniqueness
- transitional internal anchoring entrypoints for payment contracts

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

### Actions

#### Governance

- `addschema(id, version, canonicalization_hash, hash_policy)`
- `updateschema(id, version, canonicalization_hash, hash_policy)`
- `deprecate(id)`
- `setpolicy(id, allow_single, allow_batch, active)`
- `setauthsrcs(billing_account, retail_payment_account)`

#### Anchoring

- `billsubmit(submitter, schema_id, policy_id, object_hash, external_ref, billable_bytes)`
- `retailsub(submitter, schema_id, policy_id, object_hash, external_ref, billable_bytes)`
- `billbatch(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref, billable_bytes)`
- `retailbatch(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref, billable_bytes)`

#### Treasury

- `withdraw(token_contract, to, quantity, memo)`

### Validation Rules

Contract-only transition:

- `billsubmit(...)` and `billbatch(...)` require `verifbill` authority
- `retailsub(...)` and `retailbatch(...)` require `verifretpay` authority
- these internal entrypoints perform the same registry validation and uniqueness checks
- they are the active anchoring runtime for the supported payment contracts

### Authorization Wiring

`verif` allows contract-only anchoring from:

- `verifbill`
- `verifretpay`

The deployed accounts are configured through:

- `setauthsrcs(billing_account, retail_payment_account)`

This transitional config now controls allowed internal callers, not external auth-table lookup.

## `verifbill`

### Purpose

`verifbill` is the enterprise payment and authorization contract.

It is responsible for:

- accepted billing tokens
- plans
- packs
- entitlements
- request-bound enterprise auth
- downstream consume authorization for `verif`

### Tables

- `billtokens`
- `plans`
- `packs`
- `entitlements`
- `usageauths`
- `billcounters`

### Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setplan(plan_code, token_contract, price, duration_sec, included_kib, active)`
- `deactplan(plan_id)`
- `setpack(pack_code, token_contract, price, included_kib, active)`
- `deactpack(pack_id)`
- `submit(payer, submitter, schema_id, policy_id, object_hash, external_ref, billable_bytes)`
- `submitroot(payer, submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref, billable_bytes)`
- `use(payer, submitter, mode, external_ref, billable_bytes)`
- `consume(auth_id)`
- `cleanauths(limit)`
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

### Usage Flow

1. enterprise payer buys plan or pack
2. `use(...)` issues one-time auth for a concrete request and billable size
3. `verif` anchors the request
4. `verif` calls `verifbill::consume(...)`

Transitional contract-only flow:

1. enterprise payer buys plan or pack
2. `verifbill::submit(...)` or `submitroot(...)` validates payer entitlement
3. `verifbill` calls `verif::billsubmit(...)` or `billbatch(...)`
4. `verifbill` burns the matching `KiB` after successful inline anchoring

Maintenance:

- `cleanauths(limit)` removes consumed or expired `usageauths`
- `cleanentls(limit)` removes expired or exhausted `entitlements` that are no longer referenced by live auth

Entitlement selection:

- `use(...)` spends the eligible entitlement with the nearest `expires_at`
- non-expiring pack entitlements are used only when no sooner-expiring entitlement can satisfy the request

### Authority Model

- governance config is controlled by contract authority
- `use(...)` requires real payer authority
- transitional atomic `submit(...)` and `submitroot(...)` also require real payer authority
- current contract-only atomic flow requires `payer == submitter`
- account delegation should be handled by native Antelope permissions, not by contract state

## `verifretpay`

### Purpose

`verifretpay` is the supported retail payment and authorization contract.

It is responsible for:

- accepted retail tokens
- exact size-based tariffs
- one-time retail auth for `verif`
- downstream consume authorization for `verif`

### Tables

- `rtltokens`
- `rtltariffs`
- `rtlauths`
- `rtlcounters`

### Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setprice(mode, token_contract, price_per_kib)`
- `consume(auth_id)`
- `cleanauths(limit)`
- `setverifacct(verification_account)`
- `withdraw(token_contract, to, quantity, memo)`

### Retail Payment Flow

Retail payment is funded through:

- `eosio.token::transfer -> verifretpay`

Current transitional memo formats:

```text
single|submitter|external_ref_hex|billable_bytes
batch|submitter|external_ref_hex|billable_bytes
single|submitter|schema_id|policy_id|object_hash|external_ref_hex|billable_bytes
batch|submitter|schema_id|policy_id|root_hash|leaf_count|manifest_hash|external_ref_hex|billable_bytes
```

Rules:

- exact payment only
- payment is derived from `billable_kib * price_per_kib`
- underpayment is rejected
- wrong token is rejected
- mode mismatch is rejected
- auth is one-time and request-bound
- auth is bound to `billable_bytes` and `billable_kib`
- payer currently must match submitter
- atomic retail variants perform inline anchoring and do not create pending auth rows

### Usage Flow

1. retail payer transfers exact amount to `verifretpay`
2. `verifretpay` creates one-time auth for the request
3. `verif` anchors the request
4. `verif` calls `verifretpay::consume(...)`

Transitional contract-only flow:

1. retail payer transfers exact amount to `verifretpay`
2. `verifretpay` validates atomic memo payload and exact tariff
3. `verifretpay` calls `verif::retailsub(...)` or `retailbatch(...)`
4. transaction finalizes without creating a pending retail auth row

Maintenance:

- `cleanauths(limit)` removes consumed or expired `rtlauths`

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

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/billing-deploy.md](/c:/projects/verification-contract/docs/billing-deploy.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- [docs/billing-onchain-smoke.md](/c:/projects/verification-contract/docs/billing-onchain-smoke.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/unified-retail-onchain-smoke.md](/c:/projects/verification-contract/docs/unified-retail-onchain-smoke.md:1)

## Summary

Supported production model:

- `verif` as the only registry
- `verifbill` as the enterprise payment model
- `verifretpay` as the retail payment model
