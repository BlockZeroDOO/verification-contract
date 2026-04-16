# Contract-Only `verif` Migration Plan

Historical note:

- the migration described here has already been completed
- current supported runtime is:
  - `verif` as internal-only registry
  - `verifbill` as enterprise public entrypoint
  - `verifretpay` as retail public entrypoint
- sections below remain as implementation history and rationale

## Purpose

This document defines the target migration from the current auth-based registry model to a contract-only registry model:

- `verif` remains the only supported registry
- `verifbill` remains the enterprise payment contract
- `verifretpay` remains the retail payment contract

Target runtime rule:

- end users do not call `verif` directly
- only `verifbill` and `verifretpay` may push anchoring transactions into `verif`
- `verif` becomes a trusted internal registry contract

This is a multi-month target.

It does **not** imply immediate key burn.

## Motivation

The current model still leaves `verif` exposed to some avoidable complexity:

- external authorization lookup
- cross-contract auth matching
- public `submit` and `submitroot` entrypoints
- request poisoning risk through pre-issued auth rows
- extra RAM and CPU spent on auth validation that could instead live fully inside payment contracts

The proposed model removes that surface by pushing orchestration outward:

- `verifbill` handles enterprise payment and then calls `verif`
- `verifretpay` handles retail payment and then calls `verif`
- `verif` only validates caller contract, registry inputs, and request uniqueness

## Target Architecture

Supported contracts remain:

- `verif`
- `verifbill`
- `verifretpay`

### `verif`

Target role:

- trusted internal registry
- only canonical storage for commitments and batches
- no direct public anchoring path

Target callers:

- `verifbill`
- `verifretpay`

### `verifbill`

Target role:

- public enterprise entrypoint
- enterprise pricing and quota enforcement
- enterprise orchestration into `verif`

### `verifretpay`

Target role:

- public retail entrypoint
- exact retail payment enforcement
- retail orchestration into `verif`

## Target Flow

### Enterprise

1. payer funds enterprise product in `verifbill`
2. `verifbill` validates plan or pack economics
3. `verifbill` decrements or reserves the required `KiB`
4. `verifbill` calls `verif`
5. `verif` writes the registry record
6. transaction finalizes

### Retail

1. user transfers exact retail payment to `verifretpay`
2. `verifretpay` validates retail tariff and request size
3. `verifretpay` calls `verif`
4. `verif` writes the registry record
5. transaction finalizes

In both cases:

- the user waits for finality
- the user verifies the final transaction and resulting on-chain registry state

## Why This Improves Security

### 1. `verif` stops being a public write surface

Today users can call:

- `submit(...)`
- `submitroot(...)`

In the target model, only trusted payment contracts can call registry writes.

This removes:

- direct malformed public submit attempts
- direct auth-source ambiguity inside `verif`
- a large part of request-binding complexity

### 2. Cross-contract auth lookup disappears from `verif`

Current `verif` must:

- read `usageauths`
- read `rtlauths`
- match request key
- match mode
- match `billable_bytes`
- match `billable_kib`
- consume external auth

Target `verif` should not do any of this.

The billing contracts should fully own:

- payment validation
- quota validation
- request binding
- atomic orchestration

### 3. Request poisoning risk drops sharply

Today enterprise `use(...)` can create a live request-bound auth before the actual anchor call.

In the target model:

- the payment contract performs validation and immediately calls `verif`
- there is no long-lived public “pending auth” path required for normal operation

### 4. Upgrade hardening becomes meaningful later

Once the model is stable and validated, `verif` can move toward:

- no direct user entry
- minimal mutable governance surface
- optional long-term key burn

That is only safe after the contract-only flow has been proven in real conditions.

## Important Constraint

Do **not** plan around burning the `verif` upgrade key during migration.

The safe order is:

1. migrate runtime model
2. validate in real conditions
3. stabilize ABI and operational flows
4. only then evaluate upgrade-key minimization or burn

## Contract Changes

## 1. `verif`

### Remove from runtime surface

Eventually remove public user anchoring actions:

- `submit(...)`
- `submitroot(...)`

Replace them with internal contract-only entrypoints, for example:

- `billsubmit(...)`
- `billbatch(...)`
- `retailsub(...)`
- `retailbatch(...)`

or a single internal shape if the team prefers one ABI.

The key rule is:

- caller must be `verifbill` or `verifretpay`
- direct end-user authority must not be accepted

### Remove auth-source machinery

After cutover, remove:

- `setauthsrcs(...)`
- external auth lookups
- external `consume(...)` callbacks

At that point `verif` should no longer:

- inspect `usageauths`
- inspect `rtlauths`
- decide which auth source is valid

### Keep

- `schemas`
- `policies`
- `commitments`
- `batches`
- size accounting:
  - `billable_bytes`
  - `billable_kib`
- request uniqueness checks

### Validation in target model

`verif` should validate only:

- caller contract identity
- active schema
- active policy
- mode allowed
- non-zero hashes
- `leaf_count > 0` for batch
- `billable_bytes > 0`
- unique request

It should not validate:

- who paid
- whether payment was exact
- whether quota exists
- whether an external auth row exists

## 2. `verifbill`

### New responsibility

`verifbill` becomes the full enterprise orchestration layer.

It should:

- accept payment or consume purchased entitlement
- validate request size
- validate enterprise policy for the request
- call `verif` inline
- only finalize if registry write succeeds

### Simplify target runtime

The current long-lived `usageauths` model can be reduced or removed.

Recommended end state:

- no separate public “issue auth now, anchor later” flow for standard usage
- use one atomic enterprise action that both authorizes and anchors

For example:

- `submit(...)`
- `submitroot(...)`

implemented on `verifbill`, not on `verif`

### Keep

- `billtokens`
- `plans`
- `packs`
- `entitlements`

### Reassess

Once contract-only orchestration is live, reassess whether `usageauths` are still needed at all.

If not needed, remove them and simplify:

- cleanup logic
- TTL logic
- auth poisoning surface

## 3. `verifretpay`

### New responsibility

`verifretpay` becomes the full retail orchestration layer.

It should:

- accept exact payment
- validate size-based retail tariff
- immediately call `verif`
- only finalize if registry write succeeds

### Simplify target runtime

The current `rtlauths` model can be reduced or removed for the normal path.

Recommended end state:

- `transfer` parses payment memo
- contract validates tariff
- contract immediately calls `verif`
- no separate pending retail auth row is needed for standard flow

If a temporary retail auth row is still useful during migration, keep it only as a transition tool.

## ABI Direction

## Current external user ABI

Today users directly touch:

- `verif::submit`
- `verif::submitroot`
- `verifbill::use`
- `verifretpay::transfer memo`

## Target external user ABI

Users should touch only:

- enterprise actions on `verifbill`
- retail payment flow on `verifretpay`

`verif` should become an internal contract ABI.

## Migration Phases

## Phase 1. Introduce internal registry entrypoints

Goal:

- prepare `verif` to accept contract-only calls

Work:

- add internal contract-only anchoring actions to `verif`
- restrict them to calls from configured payment contracts
- keep current public `submit` and `submitroot` temporarily for compatibility

Result:

- `verifbill` and `verifretpay` can start calling `verif` directly

## Phase 2. Add contract-driven enterprise anchoring

Goal:

- make `verifbill` capable of full enterprise orchestration

Work:

- add enterprise anchoring actions to `verifbill`
- inside them:
  - validate payer and quota
  - derive `billable_kib`
  - call `verif`
  - finalize quota burn only if `verif` succeeds

Result:

- enterprise users no longer need to call `verif` directly

## Phase 3. Add contract-driven retail anchoring

Goal:

- make `verifretpay` capable of full retail orchestration

Work:

- extend `ontransfer(...)` or add explicit retail anchor action
- validate retail exact payment
- call `verif` inline
- finalize only if registry write succeeds

Result:

- retail users no longer need to call `verif` directly

## Phase 4. Remove external auth lookup from `verif`

Goal:

- shrink `verif` to pure registry logic

Work:

- remove `setauthsrcs(...)`
- remove external auth table reads
- remove `consume_usage_authorization(...)`
- remove multiple-auth conflict logic

Result:

- `verif` becomes materially simpler and safer

## Phase 5. Remove public user anchoring from `verif`

Goal:

- finish cutover

Work:

- remove or disable direct public anchoring actions
- update smoke/deploy docs to call only payment contracts

Result:

- all real traffic enters through `verifbill` or `verifretpay`

## Phase 6. Long-run hardening

Goal:

- evaluate whether `verif` is ready for upgrade minimization

Preconditions:

- stable ABI
- stable live operations
- repeated validation on real networks
- no unresolved migration needs

Possible future actions:

- reduce mutable governance
- move to hardened permission setup
- evaluate eventual upgrade-key burn

This is a future production-hardening decision, not part of the initial migration.

## Security Benefits Expected From Migration

- fewer public entrypoints in `verif`
- removal of auth-source ambiguity
- removal of pending-auth request poisoning in normal flow
- smaller trusted code path in the registry contract
- easier reasoning about registry correctness

## Risks Introduced By Migration

- `verifbill` and `verifretpay` become orchestration-critical
- transaction composition must be correct in payment contracts
- users must validate final transaction results rather than trusting intermediate intent

These are acceptable if the product model explicitly assumes:

- users wait for finality
- users inspect final on-chain result

## Recommended Next Implementation Slice

Start with enterprise first.

Recommended first code slice:

1. add contract-only internal write path in `verif`
2. implement enterprise inline anchoring from `verifbill`
3. validate enterprise path on Jungle4
4. then migrate retail

This keeps the first migration narrower and easier to reason about.
