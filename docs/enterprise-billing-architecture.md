# Enterprise Billing Architecture

## Purpose

This document defines the recommended on-chain billing model for the enterprise verification surface.

It is intended to solve one problem:

- `verif` needs a real payment and entitlement model for enterprise and integrator customers

without reintroducing any of the removed legacy payment behavior into `verif` itself.

## Current Status

`verifbill` now exists in this repository as an initial contract shell.

Implemented in the current shell:

- accepted billing tokens
- plan definitions
- pack definitions
- entitlement rows created by purchases
- `use(...)` with one-time `usageauths`
- deploy tooling
- standalone billing smoke tooling

Still pending:

- live deploy and smoke validation on network

## Design Goal

The target architecture must satisfy all of the following:

- no deposit balance inside `verif`
- no retail-style exact `transfer + submit` flow
- no trusted backend required by protocol
- direct client-side transaction signing must remain possible
- enterprise and integrator customers must be able to pre-purchase usage rights on-chain
- payer and submitter authorization should rely on native Antelope permissions instead of contract-managed delegate state

## Core Recommendation

Use a separate on-chain billing contract for enterprise usage.

Recommended contract role:

- enterprise billing contract/account: `verifbill`

This contract should own:

- accepted payment tokens
- plans
- usage packs
- entitlements
- usage authorizations

The verification contract should remain focused on anchoring only:

- `verif` anchors
- `verifbill` controls whether a submitter has the right to anchor

## Contract Roles

### `verif`

`verif` remains:

- billing-agnostic
- anchoring-only
- schema/policy/lifecycle focused

It should not:

- hold plan state
- hold enterprise quotas
- parse billing memos
- accept enterprise payment transfers

Its only billing-related responsibility should be:

- verify that a valid enterprise usage authorization exists for the current request

### `verifbill`

`verifbill` should be a dedicated enterprise billing contract.

It should:

- receive enterprise payments on-chain
- convert payment into plans or usage packs
- mint one-time submit authorizations
- mark usage as consumed

## Product Model

The enterprise model should not be pay-per-transfer at submit time.

The recommended commercial model is:

1. subscription plans
2. usage packs
3. native-permission usage

### Subscription plans

A plan grants rights for a fixed time window.

Examples:

- monthly enterprise plan
- annual enterprise plan

A plan may include:

- single-submit quota
- batch-submit quota
- expiration time
- optional organization scope

### Usage packs

A usage pack grants a finite amount of enterprise usage without requiring a deposit.

Examples:

- `10,000` single-submit units
- `1,000` batch-submit units

This is better than deposit because:

- the customer buys a product, not a balance
- accounting is clearer
- there is no need to manually reconcile a contract-held internal wallet balance

### Native-permission usage

Enterprise customers often pay from one account and submit from another operational account.

So the billing architecture must support:

- payer account
- submitter account
- native Antelope permission delegation outside contract state

Meaning:

- one enterprise account buys plan/pack entitlement
- `use(...)` may be signed by the payer or the submitter
- if organizations need delegated operational signing, they configure it at the account-permission layer

## High-Level Flow

### Flow A. Buy plan

1. payer sends token transfer to `verifbill`
2. `verifbill` interprets the purchase request
3. `verifbill` creates or extends enterprise entitlement

Output:

- active plan entitlement

### Flow B. Buy usage pack

1. payer sends token transfer to `verifbill`
2. `verifbill` interprets the purchase request
3. `verifbill` creates or increments pack entitlement

Output:

- remaining single quota and/or batch quota

### Flow C. Use entitlement for submit

Recommended atomic request structure:

1. `verifbill::use(...)`
2. `verif::submit(...)`

or for batch:

1. `verifbill::use(...)`
2. `verif::submitroot(...)`

The `use(...)` action creates a one-time usage authorization tied to:

- payer entitlement
- submitter
- request key
- mode

Then `verif` validates that authorization before accepting the anchor.

## Recommended Verification Binding

The key design requirement is deterministic request binding.

The enterprise billing authorization should bind to:

- `submitter`
- `mode`
- `external_ref`

and ideally to the same request-key semantics used by `verif`.

Recommended request binding key:

- `request_key = hash(submitter, external_ref)`

Then:

- `verifbill::use(...)` creates authorization for that exact request key
- `verif::submit(...)` recomputes the same request key and verifies authorization

## Why This Is Better Than Deposit

This architecture avoids the main deposit problems:

- no internal user balance table in `verif`
- no need for the client to track a second wallet-like state
- enterprise customer buys plan or pack, not floating balance
- entitlement is easier to audit than a floating deposit balance

## Why This Is Better Than Retail Atomic Payment

Retail exact payment works well for wallet-first users, but is not ideal for enterprise because:

- enterprise customers want pre-purchased entitlement
- corporate payer and operational submitter are often different accounts
- governance and billing policy are usually organization-level

So enterprise should use:

- entitlement authorization

not:

- exact fee per submit transfer

## Recommended `verifbill` Data Model

### `billtokens`

Stores accepted payment tokens.

Fields:

- `config_id`
- `token_contract`
- `token_symbol`
- `enabled`
- `updated_at`

### `plans`

Stores subscription plan definitions.

Fields:

- `plan_id`
- `plan_code`
- `token_contract`
- `price`
- `duration_sec`
- `single_quota`
- `batch_quota`
- `active`
- `updated_at`

### `packs`

Stores usage pack definitions.

Fields:

- `pack_id`
- `pack_code`
- `token_contract`
- `price`
- `single_units`
- `batch_units`
- `active`
- `updated_at`

### `entitlements`

Stores purchased enterprise rights.

Fields:

- `entitlement_id`
- `payer`
- `kind`
- `plan_id`
- `pack_id`
- `single_remaining`
- `batch_remaining`
- `active_from`
- `expires_at`
- `status`
- `updated_at`

Meaning:

- `kind` distinguishes plan vs pack
- plans use time bounds
- packs use remaining units

### `usageauths`

Stores one-time usage authorizations.

Fields:

- `auth_id`
- `payer`
- `submitter`
- `mode`
- `request_key`
- `entitlement_id`
- `consumed`
- `created_at`
- `consumed_at`
- `expires_at`

Purpose:

- one authorization for one enterprise submit

### `billcounters`

Stores monotonic IDs for billing tables.

Fields:

- `next_plan_id`
- `next_pack_id`
- `next_entitlement_id`
- `next_usageauth_id`

## Recommended `verifbill` Actions

### Governance

- `settoken(token_contract, token_symbol)`
- `rmtoken(token_contract, token_symbol)`
- `setplan(...)`
- `setpack(...)`
- `deactplan(plan_id)`
- `deactpack(pack_id)`
- `withdraw(token_contract, to, quantity, memo)`

### Entitlement Purchase

- `ontransfer(...)`

Transfer memo should encode enterprise purchase intent.

Recommended memo families:

- `plan|payer|plan_code`
- `pack|payer|pack_code`

### Usage

- `use(payer, submitter, mode, external_ref)`
- `consume(auth_id)` or internal consumption by `verif`-verified flow

## Authorization Policy

### Who may buy

- any account that pays with an accepted token

### Who may use entitlement

- payer directly
- or a submitter account that already has the required authority through native Antelope permissions

### Who may consume authorization

Recommended model:

- `verifbill::use(...)` creates the usage authorization
- `verif` verifies it and signals consumption through a controlled contract-to-contract path

## Contract-to-Contract Integration Options

There are two viable models.

### Option 1. `verif` reads `usageauths`

`verif` directly reads the `verifbill` table.

Pros:

- simple
- transparent

Cons:

- tighter coupling to `verifbill` table layout

### Option 2. `verifbill` issues signed or structured usage action

`verifbill::use(...)` writes a specific on-chain authorization record and `verif` validates it.

Pros:

- still transparent
- cleaner domain separation

Cons:

- slightly more moving parts

Recommended choice:

- Option 2 with explicit `usageauths`

## Consumption Rule

Authorization must be single-use.

After successful `submit` or `submitroot`:

- matching authorization becomes consumed

This prevents:

- replay
- duplicate submit for one paid usage

## Failure Handling

### If `use(...)` succeeds and `submit(...)` fails

Recommended behavior:

- `use(...)` creates pending authorization
- failed submit does not consume it
- authorization expires after short TTL if unused

This avoids accidental quota loss.

### If `submit(...)` succeeds twice

Should not happen because:

- `verif` request uniqueness prevents duplicate anchor
- `usageauths` is one-time only

## Recommended Mode Values

Use the same semantic split as retail:

- `0 = single`
- `1 = batch`

This keeps system-wide reasoning simpler.

## Security Requirements

The billing architecture must enforce:

- accepted token whitelist
- exact plan/pack purchase validation
- no hidden deposit balance model
- one-time usage authorization
- request-key binding
- replay protection
- expiration of stale unused authorizations
- separation between governance and customer usage

## Recommended Initial Scope

The first release of enterprise billing should be intentionally narrow.

Recommended Phase 1 scope:

- one accepted token
- plan purchases
- pack purchases
- `use(...)`
- one-time `usageauths`
- single and batch quota split

Do not add yet:

- dynamic pricing
- discounts
- refunds
- multi-token price discovery
- cross-contract fee splitting

## Recommended Repository Outcome

This repository currently owns only verification contracts.

The clean structural step has now been completed:

- architecture docs were added
- `verifbill` was implemented as a third contract target in this repository

Current contract set:

- `verif`
- `verifbill`
- `verifretpay`

## Working Recommendation

The recommended enterprise payment model is:

- separate billing contract
- plans and packs instead of deposit
- payer or submitter initiated usage through native permissions
- atomic `verifbill::use + verif::submit`
- one-time usage authorization tied to request key

This gives enterprise customers:

- on-chain payment
- no deposit tracking inside `verif`
- no trusted backend requirement
- better organization-level accounting without duplicating access control inside contract state
