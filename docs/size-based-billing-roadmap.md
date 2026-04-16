# Size-Based Billing Roadmap

## Goal

Move the supported architecture from record-based charging to size-based charging:

- `verif` remains the only registry
- `verifbill` moves from record quotas to byte or kibibyte quotas
- `verifretpay` moves from fixed per-request tariffs to size-based retail pricing

Target commercial rule:

- enterprise quota is measured in `KiB`
- retail payment is charged in `KiB`

## Important Constraint

`verif` anchors hashes, not full payload bytes.

That means the contract cannot independently prove the off-chain payload size from:

- `object_hash`
- `root_hash`
- `external_ref`

So the protocol must make size explicit.

Recommended rule:

- every supported request carries declared `billable_bytes`
- `billable_bytes` is included in the signed action data
- `billable_kib` is derived deterministically from `billable_bytes`

Recommended formula:

```text
billable_kib = max(1, ceil(billable_bytes / 1024))
```

This does not prove the client told the truth about payload size, but it does make:

- pricing deterministic
- authorization binding auditable
- disputes observable on-chain

If later you want cryptographic enforcement of true payload size, the protocol would need a stronger data-availability model than hash-only anchoring.

## Target Architecture

Supported contracts remain:

- `verif`
- `verifbill`
- `verifretpay`

Meaning:

- `verif` validates request identity and consumes external auth
- `verifbill` authorizes enterprise usage by `KiB`
- `verifretpay` authorizes retail usage by `KiB`

## Protocol Changes

## 1. `verif` must carry billable size

### `submit(...)`

Current shape:

```text
submit(submitter, schema_id, policy_id, object_hash, external_ref)
```

Target shape:

```text
submit(submitter, schema_id, policy_id, object_hash, external_ref, billable_bytes)
```

### `submitroot(...)`

Current shape:

```text
submitroot(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref)
```

Target shape:

```text
submitroot(submitter, schema_id, policy_id, root_hash, leaf_count, manifest_hash, external_ref, billable_bytes)
```

### `verif` validation

`verif` should:

- require `billable_bytes > 0`
- derive `billable_kib`
- require matching external authorization for:
  - `submitter`
  - `mode`
  - `external_ref`
  - `billable_kib`

### `verif` state

Add to `commitments`:

- `billable_bytes`
- `billable_kib`

Add to `batches`:

- `billable_bytes`
- `billable_kib`

This makes price basis auditable later.

## 2. `verifbill` must move from record quotas to size quotas

## Current model

Today `verifbill` stores:

- `single_quota`
- `batch_quota`
- `single_remaining`
- `batch_remaining`

That is record-based.

## Target model

Replace with size-based quota:

### Plans

Replace:

- `single_quota`
- `batch_quota`

With:

- `included_kib`

Optional future extension:

- separate `single_kib_limit`
- separate `batch_kib_limit`

But for the first migration, one total `included_kib` is simpler.

### Packs

Replace:

- `single_units`
- `batch_units`

With:

- `included_kib`

### Entitlements

Replace:

- `single_remaining`
- `batch_remaining`

With:

- `kib_remaining`

### Usage authorization

Add to `usageauths`:

- `billable_bytes`
- `billable_kib`

### `use(...)`

Current shape:

```text
use(payer, submitter, mode, external_ref)
```

Target shape:

```text
use(payer, submitter, mode, external_ref, billable_bytes)
```

Behavior:

- derive `billable_kib`
- bind auth to request and size
- do not burn quota yet

### `consume(...)`

On successful consume:

- burn `kib_remaining -= billable_kib`

This fixes the current bug where quota is lost even if anchoring never succeeds.

## 3. `verifretpay` must move from fixed tariff per request to price per KiB

## Current model

Today `verifretpay` stores:

- exact tariff for `single`
- exact tariff for `batch`

That is record-based.

## Target model

Replace fixed tariffs with:

- `price_per_kib`
- optionally `minimum_charge`

Recommended first version:

- one `price_per_kib` per mode and token
- no additional complexity yet

### Tariff table

Replace or reshape `rtltariffs` to store:

- `mode`
- `token_contract`
- `price_per_kib`
- `active`

Optional later:

- `minimum_charge`
- `rounding_policy`

### Retail memo

Current memo:

```text
single|submitter|external_ref_hex
batch|submitter|external_ref_hex
```

Target memo:

```text
single|submitter|external_ref_hex|billable_bytes
batch|submitter|external_ref_hex|billable_bytes
```

### Retail payment validation

`verifretpay` should:

- parse `billable_bytes`
- derive `billable_kib`
- compute expected exact payment:

```text
expected_quantity = billable_kib * price_per_kib
```

- require exact match
- persist auth bound to:
  - `submitter`
  - `mode`
  - `external_ref`
  - `billable_bytes`
  - `billable_kib`

### Retail auth state

Add to `rtlauths`:

- `billable_bytes`
- `billable_kib`

## 4. `verif` must match size against auth source

Current `verif` matching is based on:

- `submitter`
- `mode`
- `request_key`
- `external_ref`

Target matching must also require:

- `billable_kib` equality

Meaning:

- an enterprise auth for `16 KiB` cannot be reused for `64 KiB`
- a retail payment for `1 KiB` cannot be reused for `20 KiB`

## 5. Audit-driven fixes to include in the same migration

This migration should not be done without also fixing the current billing bugs.

### Fix A. Prevent third-party burning of enterprise quota

Current problem:

- `submitter` can spend someone else's `payer` entitlement

Required fix:

- `use(...)` must require `has_auth(payer)`

If later you need delegated usage:

- use native account permissions
- or explicit payer-signed higher-level orchestration

But the contract must not allow arbitrary third-party quota burn.

### Fix B. Burn quota on consume, not on use

Current problem:

- quota is burned before anchoring succeeds

Required fix:

- `use(...)` only creates pending auth
- `consume(...)` burns `billable_kib`

### Fix C. Reclaim stale auth

Current problem:

- stale auth can block the same request forever

Required fix:

- add TTL for both enterprise and retail auth
- allow cleanup or reissue after expiry

### Fix D. Reduce RAM exposure

Current problem:

- user-triggered flows grow contract-paid rows indefinitely

Required fix:

- add cleanup actions for expired unused auth
- add cleanup for exhausted or expired entitlements
- define retention rules for old auth rows

This may not fully solve RAM economics, but it removes the worst unbounded-growth path.

## Migration Phases

## Phase 1. Protocol shape

Goal:

- make billable size explicit everywhere

Work:

- add `billable_bytes` to `verif::submit`
- add `billable_bytes` to `verif::submitroot`
- add `billable_bytes` and `billable_kib` to `commitments`
- add `billable_bytes` and `billable_kib` to `batches`

Result:

- registry records are auditable by size basis

## Phase 2. Enterprise size billing

Goal:

- convert enterprise quota to `KiB`

Work:

- replace plan and pack record quotas with `included_kib`
- replace entitlement remaining units with `kib_remaining`
- extend `use(...)` auth to include size
- move quota burn from `use(...)` to `consume(...)`
- require `has_auth(payer)`

Result:

- enterprise billing becomes size-based and safer

## Phase 3. Retail size pricing

Goal:

- convert retail payment to exact `KiB` pricing

Work:

- replace fixed tariff with `price_per_kib`
- extend retail memo with `billable_bytes`
- store `billable_bytes` and `billable_kib` in `rtlauths`
- require exact computed payment

Result:

- retail payment is proportional to anchored size, not request count

## Phase 4. Authorization matching hardening

Goal:

- ensure auth cannot be reused for a different size

Work:

- `verif` must match size fields against enterprise or retail auth
- add stale-auth cleanup or reissue logic

Result:

- safer request binding

## Phase 5. Live validation

Goal:

- validate final size-based architecture on Jungle4

Required smoke coverage:

- enterprise:
  - buy pack
  - issue auth for N KiB
  - anchor
  - consume exact KiB
- retail:
  - pay exact amount for N KiB
  - anchor
  - consume exact auth
- negative:
  - underpayment
  - mismatched `billable_bytes`
  - stale auth
  - replay
  - attempt to burn чужой payer quota

## Recommended Commit Sequence

1. `refactor: add billable_bytes to verif submit actions`
2. `refactor: store billable size in commitments and batches`
3. `refactor: convert verifbill quotas from records to kib`
4. `fix: require payer authority in verifbill use`
5. `fix: burn enterprise quota on consume`
6. `refactor: convert verifretpay tariffs to price_per_kib`
7. `refactor: bind retail auth to billable size`
8. `feat: add stale auth cleanup and reissue paths`
9. `test: add size-based enterprise and retail smoke coverage`

## End State

Final intended commercial model:

- enterprise pays by `KiB`
- retail pays by `KiB`
- `verif` remains the only registry

Final intended technical model:

- size is explicit in every signed request
- auth is bound to request and size
- quota is consumed only after successful anchor
- stale auth does not poison future retries
