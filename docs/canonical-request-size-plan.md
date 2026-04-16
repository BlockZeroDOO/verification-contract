# Canonical Registry Request Size Plan

## Goal

Move billing away from client-supplied `billable_bytes` and toward a contract-computed
canonical size of the request that reaches `verif`.

Supported model:

- `verif` is the internal-only registry
- `verifbill` computes canonical enterprise request size
- `verifretpay` computes canonical retail request size

## Core Rule

Billing is charged for the canonical serialized request to `verif`, not for:

- off-chain payload size
- full packed transaction size
- client-declared `billable_bytes`

Canonical request size means the serialized action data of the internal registry call:

- single request:
  - `submitter`
  - `schema_id`
  - `policy_id`
  - `object_hash`
  - `external_ref`
- batch request:
  - `submitter`
  - `schema_id`
  - `policy_id`
  - `root_hash`
  - `leaf_count`
  - `manifest_hash`
  - `external_ref`

This makes request size:

- deterministic
- contract-reproducible
- identical for enterprise and retail

## Risks Reduced

- client can no longer understate `billable_bytes`
- enterprise and retail no longer depend on external size declarations
- `verif` stores a billable size derived from its own canonical request shape

## Remaining Non-Goals

This model does not try to bill for:

- size of the off-chain document behind a hash
- DFS payload size
- full transaction overhead such as signatures or TAPOS

That data is outside the registry request model and should not drive anchoring billing.

## Implementation Phases

### Phase 1

Introduce a shared canonical request size helper and switch contracts to use it.

Deliverables:

- shared `verification_request_size` helper
- `verif` computes `billable_bytes` internally
- `verifbill` computes size for `submit` and `submitroot`
- `verifretpay` computes size from atomic retail memo content

### Phase 2

Remove client-supplied `billable_bytes` from public billing interfaces.

Deliverables:

- `verifbill::submit(...)` without `billable_bytes`
- `verifbill::submitroot(...)` without `billable_bytes`
- retail atomic memo without trailing `billable_bytes`

### Phase 3

Update smoke coverage and docs to assert contract-computed size.

Deliverables:

- billing smoke derives expected size from canonical request shape
- retail smoke uses new memo format
- docs/reference updated to reflect computed request size model

### Phase 4

Run live Jungle4 validation on the computed-size billing model.

## Migration Notes

- registry tables keep `billable_bytes` and `billable_kib`
- those fields become fully contract-computed
- this is an ABI change for:
  - `verifbill`
  - `verifretpay`
  - internal `verif` entrypoints

Fresh validation accounts are recommended for Jungle4 whenever old table rows or old ABI
assumptions may interfere with the new runtime.
