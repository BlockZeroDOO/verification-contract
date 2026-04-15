# Verification Enterprise/Retail Split Plan

## Goal

Split the current verification product surface into two separate smart contracts:

- `verification_enterprise`
- `verification_retail`

Chosen final deployment names:

- enterprise contract/account: `verifent`
- retail contract/account: `verifretail`

The objective is to support two different commercial and trust models without polluting one contract with the other model's requirements.

## Product Positioning

### `verification_enterprise`

Target audience:

- enterprise customers
- integrators
- client-hosted or self-prepared transaction flows
- environments where a trusted backend may exist on the client side, but must not be required by the protocol

Commercial model:

- no on-chain payment flow inside the verification contract
- billing handled outside this contract by enterprise arrangements or a future dedicated billing contract

### `verification_retail`

Target audience:

- retail or self-service users
- wallet-first direct blockchain flow
- users who should be able to pay and submit without relying on a trusted backend

Commercial model:

- on-chain payment required
- atomic `pay + submit` or `pay + submitroot`
- no deposit model

## Target Architecture

The system should be organized into:

1. Shared verification core
2. Enterprise wrapper contract
3. Retail wrapper contract

The shared core should contain:

- KYC rules
- schema registry logic
- policy registry logic
- request key rules
- commitment lifecycle
- batch lifecycle
- validation helpers

The wrappers should differ only in admission and payment gating.

## Contract Scope

### `verification_enterprise`

Should keep:

- `issuekyc`
- `renewkyc`
- `revokekyc`
- `suspendkyc`
- `addschema`
- `updateschema`
- `deprecate`
- `setpolicy`
- `enablezk`
- `disablezk`
- `submit`
- `submitroot`
- `supersede`
- `revokecmmt`
- `expirecmmt`
- `linkmanifest`
- `closebatch`
- `withdraw` if governance treasury withdrawal remains needed

Should not contain:

- token notification handlers
- pricing tables
- payment tables
- deposit logic

### `verification_retail`

Should keep the same registry and lifecycle surface as enterprise, plus retail payment gating.

Retail payment model:

- payment and submit happen atomically in the same transaction
- no persistent contract balance for the user
- no deposit table
- no legacy proof-payment flow

## Recommended Retail Payment Model

The preferred retail model is:

1. `token::transfer -> verification_retail`
2. `verification_retail::submit` or `verification_retail::submitroot`

Both actions must be in the same transaction.

The transfer creates a one-time payment receipt that is consumed by `submit` or `submitroot`.

Retail constraints:

- exact payment only
- one-time consumption only
- strict token validation
- no replay
- no double consume

## Request Binding

Retail transfer and submit must be bound together deterministically.

Recommended approach:

- transfer memo carries `request_key`
- `submit` or `submitroot` must use the same `request_key`
- payment receipt is consumed only on exact match

## Repository Structure Direction

Recommended shared files:

- `include/verification_core.hpp`
- `include/verification_tables.hpp`
- `include/verification_validators.hpp`
- `src/verification_core.cpp`

Recommended enterprise wrapper files:

- `include/verification_enterprise.hpp`
- `src/verification_enterprise.cpp`

Recommended retail wrapper files:

- `include/verification_retail.hpp`
- `src/verification_retail.cpp`

This avoids copy-paste divergence between two large contract implementations.

## Implementation Phases

### Phase 1. Extract Shared Core

Goal:

- isolate the shared registry and lifecycle logic from contract-specific gating

Tasks:

- move tables and validators into shared headers
- move common submit and batch lifecycle code into shared implementation
- prepare thin contract wrappers

Result:

- shared core exists and current contract logic can be reused

### Phase 2. Introduce `verification_enterprise`

Goal:

- establish the enterprise contract as the clean, billing-agnostic verification contract

Tasks:

- migrate current contract into the enterprise wrapper
- ensure no payment surface remains
- update ABI, Ricardian, smoke tests, and deployment docs

Result:

- production-ready enterprise contract

### Phase 3. Introduce `verification_retail`

Goal:

- create a second contract with atomic payment admission

Tasks:

- add retail wrapper
- add retail token and tariff tables
- add `on_notify(token::transfer)` handling
- add strict payment receipt consumption in `submit` and `submitroot`

Result:

- retail contract shell with atomic pay-and-submit flow

### Phase 4. Retail Tariff Governance

Tasks:

- add `settoken`
- add `rmtoken`
- add `setprice`
- support separate tariffs for:
  - `submit`
  - `submitroot`

Initial recommendation:

- fixed price for single submit
- fixed price for batch submit

### Phase 5. Security Hardening

Retail-specific security work must cover:

- replay prevention
- duplicate consume prevention
- wrong token rejection
- underpayment rejection
- overpayment handling
- cross-request payment hijack prevention
- tx atomicity assumptions

Recommended initial policy:

- exact payment only

### Phase 6. Docs And Deployment Split

Tasks:

- separate enterprise deploy guide
- separate retail deploy guide
- separate enterprise smoke suite
- separate retail smoke suite
- document product positioning and intended audiences

## Design Decisions To Confirm

### 1. Contract account names

Suggested examples:

- `verifyent` and `verifyrtl`
- or `verifent` and `verifrtl`

### 2. Retail pricing granularity

Need to confirm whether batch pricing is:

- fixed per batch
- or dependent on `leaf_count`

Recommended initial version:

- fixed single price
- fixed batch price

### 3. Overpayment policy

Options:

- reject overpayment
- accept overpayment without refund
- auto-refund difference

Recommended initial version:

- exact payment only

### 4. Shared core boundaries

Need to confirm whether KYC, schema, and policy governance remain duplicated by deployment or shared through the same administrative model across both contracts.

## Recommended Commit Sequence

1. `refactor: extract shared verification core`
2. `feat: introduce enterprise verification contract`
3. `feat: introduce retail verification contract shell`
4. `feat: add atomic pay and submit for retail`
5. `feat: add retail token and tariff governance`
6. `test: add enterprise and retail smoke coverage`
7. `docs: split enterprise and retail deploy guides`

## Working Recommendation

The recommended delivery order is:

1. build `verification_enterprise` first from the current contract
2. keep it payment-free
3. build `verification_retail` second on top of the shared core
4. implement only strict atomic retail payment in the first retail release

This keeps the enterprise product clean while giving retail users a trust-minimized on-chain payment path.
