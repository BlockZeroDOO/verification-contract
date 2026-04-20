# External Auditor Verification

This document describes the supported path for an external auditor to verify that selected source data was anchored into `verif`.

The goal is simple:

1. select a source row or a source batch outside the signer runtime
2. recompute the expected hashes independently
3. verify that the matching on-chain row exists in `verif`
4. confirm that the on-chain row matches the expected hash, schema, policy, submitter, and request identity

## What `verif` Already Stores

For single anchors, `verif.commitments` stores:

- `submitter`
- `schema_id`
- `policy_id`
- `object_hash`
- `external_ref`
- `request_key`
- `billable_bytes`
- `billable_kib`
- `created_at`

For batch anchors, `verif.batches` stores:

- `submitter`
- `schema_id`
- `policy_id`
- `root_hash`
- `manifest_hash`
- `leaf_count`
- `external_ref`
- `request_key`
- `billable_bytes`
- `billable_kib`
- `created_at`

That is enough for an independent auditor to verify the chain side of an anchor.

## Auditor Inputs

### Single-Row Verification

An external auditor needs:

- selected source row data
- the canonicalization rules used for that schema version
- expected `submitter`
- expected `schema_id`
- expected `policy_id`
- expected `external_ref`
- recomputed `object_hash`

### Batch Verification

An external auditor needs:

- selected source rows included in the batch
- the canonicalization rules used for that schema version
- expected `submitter`
- expected `schema_id`
- expected `policy_id`
- expected `external_ref`
- recomputed `root_hash`
- recomputed `manifest_hash`
- expected `leaf_count`

Important:

- `verif` stores only the batch root, not every batch leaf
- for leaf-level verification, the operator must provide the external auditor with the batch manifest and the Merkle inclusion proof material

## Request Identity

`verif` stores `request_key`, which is derived from:

- `submitter`
- `external_ref`

The formula is:

```text
sha256(submitter + ":" + external_ref_bytes)
```

This lets the auditor verify that the anchor identity also matches the expected client-side reference.

## Recommended Audit Path

### Single Row

1. Select the source row from the database.
2. Canonicalize it using the schema version that was active when it was submitted.
3. Compute `object_hash`.
4. Compute or recover the expected `external_ref`.
5. Read the matching `commitments` row from `verif`.
6. Confirm:
   - `submitter`
   - `schema_id`
   - `policy_id`
   - `object_hash`
   - `external_ref`
   - `request_key`

### Batch

1. Select the claimed source rows.
2. Canonicalize each row independently.
3. Rebuild the leaf set and batch root.
4. Rebuild `manifest_hash`.
5. Read the matching `batches` row from `verif`.
6. Confirm:
   - `submitter`
   - `schema_id`
   - `policy_id`
   - `root_hash`
   - `manifest_hash`
   - `leaf_count`
   - `external_ref`
   - `request_key`

## Auditor Helper Script

This repository now includes:

- [scripts/verify-external-audit.py](/c:/projects/verification-contract/scripts/verify-external-audit.py)

The script:

- reads `verif` tables through RPC
- finds the row by `external_ref`
- verifies the expected fields
- recomputes `request_key`
- verifies registry linkage through `schemas` and `policies`

### Single Example

```bash
python scripts/verify-external-audit.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --mode single \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --object-hash abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789
```

### Batch Example

```bash
python scripts/verify-external-audit.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --mode batch \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --root-hash abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789 \
  --manifest-hash 1111111111111111111111111111111111111111111111111111111111111111 \
  --leaf-count 100
```

The script returns JSON and exits non-zero if the on-chain state does not match the expected values.

## Scope Boundary

What this repository verifies:

- on-chain registry rows
- request identity
- schema/policy linkage
- stored root or object hash

What still depends on the off-chain evidence package:

- canonicalization of the original source rows
- proof that a specific row was part of a batch leaf set
- manifest contents for batch-level forensic review

That split is intentional:

- `verif` proves that a specific hash or root was anchored
- the operator or agent proof bundle proves how source data produced that hash or root
