# Verification Contract Reference

## Purpose

This document is the full on-chain reference for the contracts in this repository:

- `verif`
- `verifbill`
- `verifretpay`

The repository contains one primary unified anchoring contract and one deprecated compatibility anchoring contract:

- schema registry
- policy registry
- single commitment anchoring
- batch anchoring
- append-only commitment anchoring
- embedded-manifest batch anchoring in the primary path

They differ in the access and payment model:

- `verif` is the unified anchoring contract
- `verifbill` is the enterprise billing and entitlement contract
- `verifretpay` is the wallet-first retail payment and authorization contract
- `verifretail` is a deprecated compatibility retail anchoring contract retained during migration

## Contract Roles

### `verif`

`verif` is the unified anchoring contract.

It is intended for:

- enterprise customers
- integrators
- self-prepared transactions
- direct client-side transaction signing
- client-hosted or private backends

It accepts external one-time usage authorization from both:

- `verifbill` for enterprise usage
- `verifretpay` for retail usage

The enterprise payment model is a separate billing contract:

- see [docs/enterprise-billing-architecture.md](/c:/projects/verification-contract/docs/enterprise-billing-architecture.md:1)

### `verifretpay`

`verifretpay` is the retail payment contract.

It is intended for:

- wallet-first end users
- exact on-chain payment for each request
- one-time retail authorization for downstream `verif`

It supports:

- exact single-payment authorizations
- exact batch-payment authorizations
- atomic `transfer + submit` when paired with `verif`
- atomic `transfer + submitroot` when paired with `verif`

### `verifretail`

`verifretail` is the deprecated compatibility retail contract.

It keeps the old wallet-first retail anchoring flow available during migration, but it is no longer the target end-state architecture.

## Shared Data Model

Both contracts use the same core business registries.

### `schemas`

Stores schema and canonicalization references.

Fields:

- `id`
- `version`
- `canonicalization_hash`
- `hash_policy`
- `active`
- `created_at`
- `updated_at`

Meaning:

- each anchoring request references an existing schema
- the contract does not store the canonicalization algorithm itself, only its committed hash/reference

### `policies`

Stores submit rules.

Fields:

- `id`
- `allow_single`
- `allow_batch`
- `active`
- `created_at`
- `updated_at`

Meaning:

- controls whether a request may use `submit` or `submitroot`

### `commitments`

Stores single-record anchors.

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

Meaning:

- one on-chain single-record anchor
- `request_key` enforces uniqueness for the request
- append-only commitment record in the primary unified path

### `batches`

Stores batch anchors.

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

Meaning:

- one batch root anchoring record
- manifest is embedded at creation time in the primary `verif` path
- append-only batch record in the primary unified path

### `counters`

Stores monotonic IDs.

Fields:

- `next_commitment_id`
- `next_batch_id`

Meaning:

- internal monotonic ID source for rows created by the contract

## Shared Actions

The following actions define the unified `verif` action surface and are still mirrored by `verifretail` only for compatibility.

### Schema Governance

- `addschema(id, version, canonicalization_hash, hash_policy)`
- `updateschema(id, version, canonicalization_hash, hash_policy)`
- `deprecate(id)`

Purpose:

- create and maintain the schema registry used by submit flows

Expected authority:

- contract owner / governance account

### Policy Governance

- `setpolicy(id, allow_single, allow_batch, active)`

Purpose:

- create and maintain minimal submit rules

Expected authority:

- contract owner / governance account

### Single Anchoring

- `submit(submitter, schema_id, policy_id, object_hash, external_ref)`

Purpose:

- anchors a single object hash on-chain

Validation:

- active schema must exist
- active policy must exist
- policy must allow single-submit mode
- `object_hash` must be non-zero
- `external_ref` must be non-zero
- request must be unique

Expected authority:

- `submitter`

### Batch Anchoring

- `submitroot(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref)`

Purpose:

- anchor a batch root
- attach immutable manifest reference in the same action

Validation:

- active schema must exist
- active policy must exist
- policy must allow batch mode
- `root_hash` must be non-zero
- `manifest_hash` must be non-zero
- `external_ref` must be non-zero
- `leaf_count > 0`
- request must be unique

Expected authority:

- `submitter`

### Treasury

- `withdraw(token_contract, to, quantity, memo)`

Purpose:

- move tokens already held by the contract to another account

Expected authority:

- contract owner / governance account

## Shared Status Model

### Commitment status

- `0 = active`

Compatibility note:

- legacy compatibility paths may still interpret historical values for superseded, revoked, or expired commitments

### Batch status

Important:

- finality is not modeled as an on-chain business status inside the contract

## `verif` Specific Behavior

### Product model

`verif` is the clean unified anchoring contract.

Its main properties:

- no embedded payment logic
- no requirement for a trusted backend
- submitter can prepare and sign transactions directly
- suited for enterprise and integrator usage
- no on-chain KYC access model
- `submit` and `submitroot` require a matching external usage authorization
- the external authorization may come from:
  - `verifbill`
  - `verifretpay`

### Legacy cleanup

`verif` no longer carries the former proof-payment surface.

Removed from the enterprise contract:

- all legacy proof-payment actions
- all legacy proof-payment tables
- the former enterprise-side transfer payment path

## `verifretpay` Specific Behavior

### Product model

`verifretpay` is the retail payment and authorization contract.

Its main properties:

- no deposit model
- no prepaid internal balance
- exact tariff matching
- usage authorization is one-time and per request
- payer must currently match submitter

### Retail Tables

#### `rtltokens`

Stores accepted payment tokens.

Fields:

- `config_id`
- `token_contract`
- `token_symbol`
- `enabled`
- `updated_at`

Purpose:

- whitelist tokens that may be used for retail payment

#### `rtltariffs`

Stores exact tariffs.

Fields:

- `config_id`
- `mode`
- `token_contract`
- `price`
- `active`
- `updated_at`

Meaning:

- `mode = 0` means single submit
- `mode = 1` means batch submit

#### `rtlauths`

Stores one-time retail usage authorizations.

Fields:

- `auth_id`
- `mode`
- `payer`
- `submitter`
- `external_ref`
- `request_key`
- `token_contract`
- `quantity`
- `consumed`
- `created_at`
- `consumed_at`

Purpose:

- links one incoming transfer to one exact request
- consumed after successful use by downstream `verif`

#### `rtlcounters`

Stores retail-specific monotonic IDs.

Fields:

- `next_token_id`
- `next_tariff_id`
- `next_auth_id`

### Retail-only Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setprice(mode, token_contract, price)`
- `consume(auth_id)`

Purpose:

- configure accepted tokens and exact prices for retail submit flows

Expected authority:

- contract owner / governance account

### Retail Transfer Flow

Retail payment happens through:

- `eosio.token::transfer -> verifretpay`

The contract parses the transfer memo and creates a one-time pending usage authorization.

Current memo format:

```text
single|submitter|external_ref_hex
batch|submitter|external_ref_hex
```

Interpretation:

- `single` means the payment is for `submit`
- `batch` means the payment is for `submitroot`
- `submitter` is the account that will later call the action
- `external_ref_hex` is the request reference that must match the later submit

### Retail Payment Rules

Current rules:

- exact payment only
- underpayment is rejected
- wrong token is rejected
- mode mismatch is rejected
- authorization must be pending and unconsumed
- submitter and payer are currently expected to be the same account

### Retail Authorization Consumption

`verifretpay` does not anchor by itself. Instead:

- it creates a retail authorization bound to the request key
- `verif` may use that authorization for `submit` or `submitroot`
- `verif` consumes the authorization after successful anchor creation

This is the target retail path for the unified architecture.

## `verifretail` Specific Behavior

### Product model

`verifretail` is the deprecated compatibility retail anchoring contract.

It keeps the older wallet-first `atomic pay + submit` flow available while migration proceeds toward the unified `verif + verifretpay` architecture.

### Compatibility role

Current role:

- preserve the already validated legacy retail path
- provide backward compatibility for deployments not yet migrated to `verifretpay`
- avoid forcing a hard cutover in one step
- stay out of the primary deploy and smoke path

## `verifbill` Specific Behavior

### Product model

`verifbill` is the enterprise billing and entitlement contract.

Its main properties:

- no deposit balance inside `verif`
- plans and packs instead of floating internal balance
- one-time usage authorization tied to request key

### Billing Tables

#### `billtokens`

Stores accepted enterprise billing tokens.

#### `plans`

Stores plan definitions with duration and single or batch quotas.

#### `packs`

Stores usage-pack definitions with single or batch units.

#### `entitlements`

Stores purchased plan and pack rights for a payer.

#### `usageauths`

Stores one-time enterprise usage authorizations created by `use(...)`.

#### `billcounters`

Stores monotonic IDs for enterprise billing tables.

### Billing Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setplan(plan_code, token_contract, price, duration_sec, single_quota, batch_quota, active)`
- `deactplan(plan_id)`
- `setpack(pack_code, token_contract, price, single_units, batch_units, active)`
- `deactpack(pack_id)`
- `use(payer, submitter, mode, external_ref)`
- `consume(auth_id)`
- `withdraw(token_contract, to, quantity, memo)`

### Billing Transfer Flow

Enterprise purchases happen through:

- `eosio.token::transfer -> verifbill`

Current memo families:

```text
plan|payer|plan_code
pack|payer|pack_code
```

### Current implementation boundary

`verifbill` already owns enterprise purchase, quota allocation, and usage-authorization state.

`verif` validates enterprise usage authorization from `verifbill` and consumes it after successful anchor creation.

## Unified Authorization Wiring

### `verif::setauthsrcs`

Configures the two external authorization sources used by `verif`:

- `billing_account`
- `retail_payment_account`

This allows real deployed account names to differ from the canonical contract names.

### `verifbill::setverifacct`

Configures which deployed `verif` account is allowed to call `verifbill::consume(...)`.

### `verifretpay::setverifacct`

Configures which deployed `verif` account is allowed to call `verifretpay::consume(...)`.

## Authorization Model

### Governance account

The governance account is responsible for:

- schema management
- policy management
- tariff and token management in retail
- withdrawals

### Submitter

The submitter is responsible for:

- `submit`
- `submitroot`

### Retail payer

In retail flow, the payer currently:

- sends the exact token transfer
- must match the declared submitter

### Enterprise payer and submitter

In enterprise flow:

- the payer buys plans and packs on-chain through `verifbill`
- `use(...)` accepts authority from either the payer or the submitter
- account-level delegation is expected to be handled through native Antelope permissions, not contract state

## Request Identity and Uniqueness

Both contracts derive request uniqueness from request-key semantics.

Inputs used by the contract-level model include:

- submitter
- external reference
- mode or lifecycle context

Practical effect:

- duplicate request submission with the same request identity is rejected
- duplicate batch submission with the same request identity is rejected

## What These Contracts Do Not Do

These contracts do not perform:

- off-chain canonicalization
- finality observation
- receipt generation
- audit indexing
- ingress preparation
- storage billing
- DFS logic

Those concerns are either:

- off-chain concerns in `C:\projects\deNotary`
- or DFS concerns in `C:\projects\decentralized_storage\contracts\dfs`

## Deployment Notes

Current final names:

- unified anchoring contract/account: `verif`
- retail payment contract/account: `verifretpay`
- enterprise billing contract/account: `verifbill`

Build outputs:

- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`
- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`
- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`

Primary runbooks:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/retail-payment-deploy.md](/c:/projects/verification-contract/docs/retail-payment-deploy.md:1)
- [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- [docs/retail-payment-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-payment-onchain-smoke.md:1)
- [docs/unified-retail-onchain-smoke.md](/c:/projects/verification-contract/docs/unified-retail-onchain-smoke.md:1)

## Summary

`verif` is the clean unified anchoring contract.

`verifretpay` is the target retail payment and authorization contract for the unified architecture.

`verifretail` is a deprecated compatibility retail anchoring contract.

`verifbill` is the enterprise billing and entitlement contract.

Together they provide:

- one canonical anchoring surface
- one enterprise billing surface
- one target retail payment surface
- one deprecated compatibility retail anchoring surface during migration
