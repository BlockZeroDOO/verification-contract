# Verification Contract Reference

## Purpose

This document is the full on-chain reference for the contracts in this repository:

- `verifent`
- `verifretail`
- `verifbill`

The two anchoring contracts share the same anchoring core:

- KYC registry
- schema registry
- policy registry
- single commitment anchoring
- batch anchoring
- commitment and batch lifecycle transitions

They differ in the access and payment model:

- `verifent` is the enterprise and integrator contract
- `verifretail` is the wallet-first retail contract with atomic on-chain payment
- `verifbill` is the enterprise billing and entitlement contract

## Contract Roles

### `verifent`

`verifent` is the billing-agnostic enterprise contract.

It is intended for:

- enterprise customers
- integrators
- self-prepared transactions
- direct client-side transaction signing
- client-hosted or private backends

It does not accept the retail token-payment flow as an active product path.

The enterprise payment model is a separate billing contract:

- see [docs/enterprise-billing-architecture.md](/c:/projects/verification-contract/docs/enterprise-billing-architecture.md:1)

### `verifretail`

`verifretail` is the retail contract.

It is intended for:

- wallet-first end users
- direct on-chain payment for each request
- exact-fee submit flows without deposits

It supports:

- exact single-payment receipts
- exact batch-payment receipts
- atomic `transfer + submit`
- atomic `transfer + submitroot`

## Shared Data Model

Both contracts use the same core business registries.

### `kyc`

Stores submitter access state.

Fields:

- `account`
- `level`
- `provider`
- `jurisdiction`
- `active`
- `issued_at`
- `expires_at`

Meaning:

- one row per account
- governs whether a policy requiring KYC may be used

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
- `require_kyc`
- `min_kyc_level`
- `allow_zk`
- `active`
- `created_at`
- `updated_at`

Meaning:

- controls whether a request may use `submit` or `submitroot`
- may require KYC
- may enable optional ZK capability flags

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
- `status_changed_at`
- `status`
- `superseded_by`

Meaning:

- one on-chain single-record anchor
- `request_key` enforces uniqueness for the request
- `status` tracks business lifecycle

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
- `manifest_linked_at`
- `status_changed_at`
- `status`

Meaning:

- one batch root anchoring record
- manifest is linked separately
- a batch starts open and can later be closed

### `counters`

Stores monotonic IDs.

Fields:

- `next_commitment_id`
- `next_batch_id`

Meaning:

- internal monotonic ID source for rows created by the contract

## Shared Actions

The following actions exist in both `verifent` and `verifretail`.

### KYC and Access Governance

- `issuekyc(account, level, provider, jurisdiction, expires_at)`
- `renewkyc(account, expires_at)`
- `revokekyc(account)`
- `suspendkyc(account)`

Purpose:

- govern who may use policies requiring KYC

Expected authority:

- contract owner / governance account

### Schema Governance

- `addschema(id, version, canonicalization_hash, hash_policy)`
- `updateschema(id, version, canonicalization_hash, hash_policy)`
- `deprecate(id)`

Purpose:

- create and maintain the schema registry used by submit flows

Expected authority:

- contract owner / governance account

### Policy Governance

- `setpolicy(id, allow_single, allow_batch, require_kyc, min_kyc_level, active)`
- `enablezk(id)`
- `disablezk(id)`

Purpose:

- create and maintain submit rules

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
- when policy requires KYC, submitter must have valid active KYC

Expected authority:

- `submitter`

### Commitment Lifecycle

- `supersede(id, successor_id)`
- `revokecmmt(id)`
- `expirecmmt(id)`

Purpose:

- move anchored commitments through business lifecycle states

Validation:

- referenced rows must exist
- source commitment must be active where required
- successor must be distinct for `supersede`

Expected authority:

- `submitter` for `supersede`
- governance account for `revokecmmt`
- governance account for `expirecmmt`

### Batch Anchoring

- `submitroot(submitter, schema_id, policy_id, root_hash, leaf_count, external_ref)`
- `linkmanifest(id, manifest_hash)`
- `closebatch(id)`

Purpose:

- anchor a batch root
- attach immutable manifest reference
- close the batch lifecycle

Validation:

- active schema must exist
- active policy must exist
- policy must allow batch mode
- `root_hash` must be non-zero
- `external_ref` must be non-zero
- `leaf_count > 0`
- request must be unique
- if policy requires KYC, KYC must be valid
- `closebatch` is allowed only after `linkmanifest`

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
- `1 = superseded`
- `2 = revoked`
- `3 = expired`

### Batch status

- `0 = open`
- `1 = closed`

Important:

- these are business statuses
- finality is not modeled as an on-chain business status inside the contract

## `verifent` Specific Behavior

### Product model

`verifent` is the clean enterprise anchoring contract.

Its main properties:

- no active retail payment flow
- no requirement for a trusted backend
- submitter can prepare and sign transactions directly
- suited for enterprise and integrator usage
- `submit` and `submitroot` require a matching enterprise usage authorization from `verifbill`

### Legacy cleanup

`verifent` no longer carries the former proof-payment surface.

Removed from the enterprise contract:

- all legacy proof-payment actions
- all legacy proof-payment tables
- the former enterprise-side transfer payment path

## `verifretail` Specific Behavior

### Product model

`verifretail` is the retail contract with exact on-chain payment for each request.

Its main properties:

- no deposit model
- no prepaid internal balance
- exact tariff matching
- payment receipt is one-time and per request
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

#### `rtlreceipts`

Stores one-time retail payment receipts.

Fields:

- `receipt_id`
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
- consumed after successful use

#### `rtlcounters`

Stores retail-specific monotonic IDs.

Fields:

- `next_token_id`
- `next_tariff_id`
- `next_receipt_id`

### Retail-only Actions

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setprice(mode, token_contract, price)`

Purpose:

- configure accepted tokens and exact prices for retail submit flows

Expected authority:

- contract owner / governance account

### Retail Transfer Flow

Retail payment happens through:

- `eosio.token::transfer -> verifretail`

The contract parses the transfer memo and creates a one-time pending payment receipt.

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
- receipt must be pending and unconsumed
- submitter and payer are currently expected to be the same account

### Retail Submit Path

Retail `submit` and `submitroot` do all shared validation plus:

- require matching pending receipt
- consume receipt after success

This gives a practical `atomic pay + submit` model without a deposit balance.

## `verifbill` Specific Behavior

### Product model

`verifbill` is the enterprise billing and entitlement contract.

Its main properties:

- no deposit balance inside `verifent`
- plans and packs instead of floating internal balance
- delegated submitter support
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

#### `delegates`

Stores enabled payer to submitter delegation mappings.

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
- `grantdelegate(payer, submitter)`
- `revokedeleg(payer, submitter)`
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

`verifbill` already owns enterprise purchase, delegation, quota allocation, and usage-authorization state.

`verifent` now validates enterprise usage authorization from `verifbill` and consumes it after successful anchor creation.

## Authorization Model

### Governance account

The governance account is responsible for:

- KYC registry management
- schema management
- policy management
- tariff and token management in retail
- withdrawals
- explicit revoke/expire operations

### Submitter

The submitter is responsible for:

- `submit`
- `submitroot`
- `supersede`
- `linkmanifest`
- `closebatch`

### Retail payer

In retail flow, the payer currently:

- sends the exact token transfer
- must match the declared submitter

### Enterprise payer and delegates

In enterprise flow, the payer currently:

- buys plans and packs on-chain through `verifbill`
- may delegate one or more submitter accounts
- may create usage authorization directly or let the submitter do it

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

- enterprise contract/account: `verifent`
- retail contract/account: `verifretail`
- enterprise billing contract/account: `verifbill`

Build outputs:

- `dist/verifent/verifent.wasm`
- `dist/verifent/verifent.abi`
- `dist/verifretail/verifretail.wasm`
- `dist/verifretail/verifretail.abi`
- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`

Primary runbooks:

- [docs/enterprise-deploy.md](/c:/projects/verification-contract/docs/enterprise-deploy.md:1)
- [docs/retail-deploy.md](/c:/projects/verification-contract/docs/retail-deploy.md:1)
- [docs/enterprise-onchain-smoke.md](/c:/projects/verification-contract/docs/enterprise-onchain-smoke.md:1)
- [docs/retail-onchain-smoke.md](/c:/projects/verification-contract/docs/retail-onchain-smoke.md:1)

## Summary

`verifent` is the clean enterprise anchoring contract.

`verifretail` is the retail anchoring contract with exact atomic on-chain payment.

`verifbill` is the enterprise billing and entitlement contract.

Together they provide:

- one shared anchoring core
- two anchoring surfaces and one enterprise billing surface
- clean separation between enterprise and retail behavior
