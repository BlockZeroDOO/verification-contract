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
- consuming external usage authorization after successful anchor creation

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
- `external_ref`
- `request_key`
- `block_num`
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
- `external_ref`
- `request_key`
- `block_num`
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

- `submit(submitter, schema_id, policy_id, object_hash, external_ref)`
- `submitroot(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref)`

#### Treasury

- `withdraw(token_contract, to, quantity, memo)`

### Validation Rules

`submit(...)` requires:

- active schema
- active policy
- policy allows single mode
- non-zero `object_hash`
- non-zero `external_ref`
- unique request
- valid external authorization

`submitroot(...)` requires:

- active schema
- active policy
- policy allows batch mode
- non-zero `root_hash`
- non-zero `manifest_hash`
- non-zero `external_ref`
- `leaf_count > 0`
- unique request
- valid external authorization

### Authorization Wiring

`verif` accepts one-time authorization from:

- `verifbill`
- `verifretpay`

The deployed accounts are configured through:

- `setauthsrcs(billing_account, retail_payment_account)`

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
- `setplan(plan_code, token_contract, price, duration_sec, single_quota, batch_quota, active)`
- `deactplan(plan_id)`
- `setpack(pack_code, token_contract, price, single_units, batch_units, active)`
- `deactpack(pack_id)`
- `use(payer, submitter, mode, external_ref)`
- `consume(auth_id)`
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
2. `use(...)` issues one-time auth for a concrete request
3. `verif` anchors the request
4. `verif` calls `verifbill::consume(...)`

### Authority Model

- governance config is controlled by contract authority
- `use(...)` accepts real user authority
- account delegation should be handled by native Antelope permissions, not by contract state

## `verifretpay`

### Purpose

`verifretpay` is the supported retail payment and authorization contract.

It is responsible for:

- accepted retail tokens
- exact tariffs
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
- `setprice(mode, token_contract, price)`
- `consume(auth_id)`
- `setverifacct(verification_account)`
- `withdraw(token_contract, to, quantity, memo)`

### Retail Payment Flow

Retail payment is funded through:

- `eosio.token::transfer -> verifretpay`

Current memo format:

```text
single|submitter|external_ref_hex
batch|submitter|external_ref_hex
```

Rules:

- exact payment only
- underpayment is rejected
- wrong token is rejected
- mode mismatch is rejected
- auth is one-time and request-bound
- payer currently must match submitter

### Usage Flow

1. retail payer transfers exact amount to `verifretpay`
2. `verifretpay` creates one-time auth for the request
3. `verif` anchors the request
4. `verif` calls `verifretpay::consume(...)`

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
