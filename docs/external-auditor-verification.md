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

## Auditor Hash Derivation Helper

This repository also includes:

- [scripts/derive-audit-hash.py](/c:/projects/verification-contract/scripts/derive-audit-hash.py)

This helper is for the first half of external verification:

- deriving the expected `object_hash`
- deriving a batch `leaf_hash`
- deriving a `manifest_hash`

The important boundary is explicit:

- this helper hashes the payload exactly as the auditor provides it
- it does not guess database canonicalization rules

That makes it useful when:

- the auditor already knows the agreed canonical payload shape
- the operator provided a canonical JSON payload or canonical manifest file
- both sides want a neutral reproducible hash derivation tool

Supported input modes:

- `--text`
- `--text-file`
- `--json`
- `--json-file`
- `--hex`

JSON inputs are normalized as:

- UTF-8
- sorted keys
- compact separators

### Object Hash Example

```bash
python scripts/derive-audit-hash.py \
  --kind object \
  --json-file selected-row.canonical.json \
  --pretty
```

### Leaf Hash Example

```bash
python scripts/derive-audit-hash.py \
  --kind leaf \
  --json-file batch-leaf.canonical.json \
  --pretty
```

### Manifest Hash Example

```bash
python scripts/derive-audit-hash.py \
  --kind manifest \
  --json-file batch-manifest.json \
  --pretty
```

Recommended external auditor flow for a batch is then:

1. use `derive-audit-hash.py` to compute a leaf hash from the agreed canonical payload
2. use `verify-batch-leaf-proof.py` to prove inclusion in the batch root
3. use `verify-external-audit.py` to verify the anchored batch row in `verif`

## End-to-End Audit Chain Helper

This repository also includes:

- [scripts/verify-audit-chain.py](/c:/projects/verification-contract/scripts/verify-audit-chain.py)

This helper is the convenience wrapper for external auditors.

It takes:

- a canonical row JSON file
- single-mode metadata
- or batch-mode metadata plus a proof file

And it performs the full verification chain in one command.

### Single Example

```bash
python scripts/verify-audit-chain.py \
  --mode single \
  --row-json-file selected-row.canonical.json \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

This run:

1. derives `object_hash` from the canonical row payload
2. recomputes `request_key`
3. loads the matching `commitments` row from `verif`
4. verifies the on-chain row

### Batch Example

```bash
python scripts/verify-audit-chain.py \
  --mode batch \
  --row-json-file batch-leaf.canonical.json \
  --proof-file batch-proof.json \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

This run:

1. derives `leaf_hash` from the canonical row payload
2. verifies Merkle inclusion from `proof-file`
3. fetches the matching `batches` row from `verif`
4. verifies `root_hash`, `request_key`, schema, policy, and optional proof metadata

## Batch Leaf Proof Helper

This repository also includes:

- [scripts/verify-batch-leaf-proof.py](/c:/projects/verification-contract/scripts/verify-batch-leaf-proof.py)

This helper is for the second half of batch verification:

- proving that one specific leaf belongs to the anchored batch root

It expects:

- a precomputed `leaf_hash`
- a Merkle proof
- either:
  - an explicit `root_hash`
  - or `external_ref` so it can fetch the on-chain batch row

Supported proof input styles:

- repeated `--sibling <hash>` with `--leaf-index <n>`
- a JSON `--proof-file` with:
  - `leaf_hash`
  - `leaf_index`
  - `root_hash` or `external_ref`
  - `proof`

Proof steps may be either:

- plain hashes, using `leaf_index` to infer left/right order
- objects like:

```json
{
  "hash": "abcdef...",
  "side": "left"
}
```

Current helper algorithm:

- binary Merkle tree
- parent hash = `sha256(left_child_bytes || right_child_bytes)`

### Example

```bash
python scripts/verify-batch-leaf-proof.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --leaf-hash abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789 \
  --leaf-index 7 \
  --sibling 1111111111111111111111111111111111111111111111111111111111111111 \
  --sibling 2222222222222222222222222222222222222222222222222222222222222222
```

If `manifest_hash` and `leaf_count` are also known from the proof package, they can be checked too:

```bash
python scripts/verify-batch-leaf-proof.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --leaf-hash abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789 \
  --leaf-index 7 \
  --sibling 1111111111111111111111111111111111111111111111111111111111111111 \
  --sibling 2222222222222222222222222222222222222222222222222222222222222222 \
  --manifest-hash 3333333333333333333333333333333333333333333333333333333333333333 \
  --leaf-count 100
```

## Scope Boundary

What this repository verifies:

- on-chain registry rows
- request identity
- schema/policy linkage
- stored root or object hash
- optional batch leaf inclusion proof against the stored root

What still depends on the off-chain evidence package:

- canonicalization of the original source rows
- manifest contents for batch-level forensic review

That split is intentional:

- `verif` proves that a specific hash or root was anchored
- the operator or agent proof bundle proves how source data produced that hash or root
- the batch proof helper verifies that a supplied leaf really belongs to the anchored root
