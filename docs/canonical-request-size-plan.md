# Canonical Registry Request Size Model

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

## Current State

Billing is contract-computed from the canonical request that reaches `verif`.

Supported model:

- `verif` is the internal-only registry
- `verifbill` computes canonical enterprise request size
- `verifretpay` computes canonical retail request size

Current implementation status:

- `verif` computes and stores `billable_bytes`
- `verif` computes and stores `billable_kib`
- `verifbill::submit(...)` and `submitroot(...)` no longer take client-supplied `billable_bytes`
- `verifretpay` derives request size from the atomic payment memo payload
- Jungle4 live validation has been completed for the contract-computed size model

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

## Migration Notes

- registry tables keep `billable_bytes` and `billable_kib`
- those fields become fully contract-computed
- this is an ABI change for:
  - `verifbill`
  - `verifretpay`
  - internal `verif` entrypoints

## Validation Notes

- Jungle4 validation has been run on the contract-computed model
- current validated Jungle4 layout is recorded in [docs/jungle4-validation-report.md](/c:/projects/verification-contract/docs/jungle4-validation-report.md:1)
- fresh validation accounts are still useful when old rows or old ABI assumptions could interfere with smoke results

## Summary

The repository now treats canonical request size as part of the active runtime model, not as planned work.
