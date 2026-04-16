# Revised Contract Simplification Plan

## Target Model

Keep three contracts:

- `verif`
- `verifbill`
- `verifretpay`

Use `verif` as the single registry and anchoring surface.

Keep separate payment contracts because they represent different commercial flows:

- `verifbill` for enterprise
- `verifretpay` for retail

Replace contract-level access modeling with native Antelope permissions and account delegation.

## Design Principles

1. One canonical registry
- all commitments and batches live only in `verif`

2. Separate payment concerns
- `verifbill` and `verifretpay` issue one-time request-bound authorizations
- `verif` only verifies and consumes them

3. No on-chain business access model
- no KYC registry as an access gate
- no delegate registry inside billing contracts
- no allowlist unless absolutely necessary later

4. Native authority over contract authority
- who may sign a submit is determined by account permissions
- contract state should not duplicate that model

5. Minimize mutable state
- fewer tables
- fewer long-lived rows
- fewer lifecycle transitions

## Recommended Contract Roles

### `verif`

Should keep:

- schema registry
- minimal policy/config registry
- `commitments`
- `batches`
- `submit`
- `submitroot`

Should not own:

- payment logic
- customer balances
- entitlement logic
- delegation logic
- access registry logic

### `verifbill`

Should remain the enterprise payment contract.

Near-term:

- keep enterprise purchases and request-bound auth

Mid-term:

- remove on-chain delegate state
- simplify enterprise pricing model if possible

### `verifretpay`

Should remain the retail payment contract.

Keep:

- exact tariff
- transfer memo parsing
- one-time request-bound auth
- consume after successful anchor

This contract is already close to the desired shape.

## What To Remove From `verif`

### Phase 1

Remove KYC access model:

- `issuekyc`
- `renewkyc`
- `revokekyc`
- `suspendkyc`
- KYC validation in `submit`
- KYC validation in `submitroot`

### Phase 2

Simplify policy model.

Keep only:

- `allow_single`
- `allow_batch`
- `active`

Remove from policy:

- `require_kyc`
- `min_kyc_level`
- `allow_zk`

Also remove:

- `enablezk`
- `disablezk`

### Phase 3

Reduce mutable lifecycle.

Target removals:

- `supersede`
- `revokecmmt`
- `expirecmmt`

For batches, target simplification:

- move `manifest_hash` into `submitroot`
- remove `linkmanifest`
- remove `closebatch`

## What To Remove From `verifbill`

### Phase 1

Remove contract-level delegation:

- `grantdelegate`
- `revokedeleg`
- `delegates` table
- delegate checks in `use(...)`

This is replaced by native account permissions and real submitter signatures.

### Phase 2

Reassess enterprise pricing complexity.

Possible later simplification:

- collapse plans and packs into a smaller exact-price or simple quota model

But this is not required for the first simplification pass.

## What To Keep In `verifretpay`

Keep most of the current structure:

- accepted tokens
- exact tariffs
- one-time request-bound auth
- consume after successful anchor

This remains the clean retail path.

## Unified Runtime Flow

### Enterprise

1. `token::transfer -> verifbill`
2. `verifbill` issues one-time auth
3. `verif::submit` or `verif::submitroot`
4. `verifbill::consume`

### Retail

1. `token::transfer -> verifretpay`
2. `verifretpay` issues one-time auth
3. `verif::submit` or `verif::submitroot`
4. `verifretpay::consume`

## First Implementation Slice

The safest first implementation slice is:

1. save this revised roadmap
2. remove KYC action surface from `verif`
3. remove KYC runtime checks from `verif`
4. simplify `verif::setpolicy` to minimal mode flags
5. update enterprise smoke to no longer depend on KYC

This gives immediate simplification with limited blast radius.

## Recommended Commit Sequence

1. `docs: add revised contract simplification plan`
2. `refactor: remove kyc access model from verif`
3. `refactor: simplify verif policy shape`
4. `refactor: remove delegate state from verifbill`
5. `refactor: deprecate verifretail from primary path`
6. `refactor: simplify verif commitment lifecycle`
7. `refactor: simplify verif batch lifecycle`

## End State

Final intended structure:

- `verif` = canonical registry
- `verifbill` = enterprise payment/auth
- `verifretpay` = retail payment/auth
- access = native Antelope permissions

This preserves:

- one registry
- separate enterprise and retail payment models
- direct client-side transaction signing

while materially reducing:

- contract complexity
- state size
- RAM exposure
- action surface
