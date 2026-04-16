# Revised Contract Simplification Plan

## Target Model

Keep three supported contracts:

- `verif`
- `verifbill`
- `verifretpay`

Use `verif` as the only supported registry and anchoring surface.

Use separate payment contracts because they represent different commercial flows:

- `verifbill` for enterprise
- `verifretpay` for all other clients

Use native Antelope permissions for account control instead of contract-level access registries.

## Design Principles

1. One canonical registry
- all supported commitments and batches live only in `verif`

2. Separate payment concerns
- `verifbill` issues request-bound enterprise authorizations for `verif`
- `verifretpay` issues request-bound retail authorizations for `verif`
- `verif` verifies and consumes them

3. No contract-level business access model
- no on-chain KYC access registry
- no delegate registry inside billing contracts
- no duplicated access model in contract state

4. Native authority over contract authority
- the real signer controls submit permissions
- enterprise operational delegation should be done with native account permissions

5. Minimize mutable state
- fewer tables
- fewer lifecycle transitions
- fewer long-lived rows

## Supported Roles

### `verif`

Keep:

- `schemas`
- `policies`
- `commitments`
- `batches`
- `submit`
- `submitroot`
- `setauthsrcs`

Do not keep:

- payment logic
- prepaid balances
- KYC access logic
- enterprise delegate state

### `verifbill`

Keep:

- accepted billing tokens
- plans
- packs
- entitlements
- `use`
- `consume`
- `setverifacct`

Simplify:

- keep native permissions as the only delegation model
- do not reintroduce contract-level delegates

### `verifretpay`

Keep:

- accepted retail tokens
- exact tariffs
- one-time request-bound auth
- `consume`
- `setverifacct`

This is the supported retail payment contract.

## Runtime Flow

### Enterprise

1. `token::transfer -> verifbill`
2. `verifbill` records plan or pack purchase
3. `verifbill::use(...)` issues one-time auth
4. `verif::submit(...)` or `submitroot(...)`
5. `verifbill::consume(...)`

### Retail

1. `token::transfer -> verifretpay`
2. `verifretpay` issues one-time auth
3. `verif::submit(...)` or `submitroot(...)`
4. `verifretpay::consume(...)`

## Simplification Work

### Completed

- removed KYC action surface from `verif`
- removed KYC checks from `verif`
- simplified `setpolicy(...)`
- removed legacy commitment lifecycle actions from `verif`
- embedded `manifest_hash` directly into `submitroot(...)`
- removed contract-level delegate state from `verifbill`

### Remaining

1. Remove unsupported documentation and legacy migration narratives
2. Reduce or archive legacy retail artifacts that are no longer part of the supported model
3. Reassess whether `verifbill` still needs full plan and pack complexity
4. Add cleanup strategy for stale auth rows to reduce RAM pressure

## End State

Supported architecture:

- `verif` = canonical registry
- `verifbill` = enterprise payment/auth
- `verifretpay` = retail payment/auth

This preserves:

- one registry
- one enterprise model
- one retail model
- direct client-side transaction signing

while reducing:

- duplicated retail paths
- contract complexity
- state size
- operational ambiguity
