# External Auditor Runbook

This runbook is the practical companion to:

- [docs/external-auditor-verification.md](/c:/projects/verification-contract/docs/external-auditor-verification.md:1)

It is intentionally short and execution-oriented.

## Ready Templates

Example payloads live in:

- [examples/external-auditor/selected-row.canonical.json](/c:/projects/verification-contract/examples/external-auditor/selected-row.canonical.json:1)
- [examples/external-auditor/batch-leaf.canonical.json](/c:/projects/verification-contract/examples/external-auditor/batch-leaf.canonical.json:1)
- [examples/external-auditor/batch-proof.json](/c:/projects/verification-contract/examples/external-auditor/batch-proof.json:1)
- [examples/external-auditor/batch-manifest.json](/c:/projects/verification-contract/examples/external-auditor/batch-manifest.json:1)

Replace the placeholder values with:

- the real canonical row payload
- the real `external_ref`
- the real proof path
- the real `schema_id` and `policy_id`
- the real `submitter`

## Single-Row Audit

### Step 1: Derive the expected object hash

Linux / WSL:

```bash
python scripts/derive-audit-hash.py \
  --kind object \
  --json-file examples/external-auditor/selected-row.canonical.json \
  --pretty
```

PowerShell:

```powershell
python .\scripts\derive-audit-hash.py `
  --kind object `
  --json-file .\examples\external-auditor\selected-row.canonical.json `
  --pretty
```

Save the returned `hash_hex`.

### Step 2: Verify the on-chain single anchor

Linux / WSL:

```bash
python scripts/verify-external-audit.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --mode single \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --object-hash REPLACE_WITH_HASH_FROM_STEP_1
```

PowerShell:

```powershell
python .\scripts\verify-external-audit.py `
  --rpc-url https://history.denotary.io `
  --verification-account verif `
  --mode single `
  --submitter dbagentstest `
  --schema-id 1 `
  --policy-id 1 `
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef `
  --object-hash REPLACE_WITH_HASH_FROM_STEP_1
```

### One-Command Single Audit

Linux / WSL:

```bash
python scripts/verify-audit-chain.py \
  --mode single \
  --row-json-file examples/external-auditor/selected-row.canonical.json \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

PowerShell:

```powershell
python .\scripts\verify-audit-chain.py `
  --mode single `
  --row-json-file .\examples\external-auditor\selected-row.canonical.json `
  --submitter dbagentstest `
  --schema-id 1 `
  --policy-id 1 `
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

## Batch Audit

### Step 1: Derive the expected leaf hash

Linux / WSL:

```bash
python scripts/derive-audit-hash.py \
  --kind leaf \
  --json-file examples/external-auditor/batch-leaf.canonical.json \
  --pretty
```

PowerShell:

```powershell
python .\scripts\derive-audit-hash.py `
  --kind leaf `
  --json-file .\examples\external-auditor\batch-leaf.canonical.json `
  --pretty
```

### Step 2: Derive the expected manifest hash

Linux / WSL:

```bash
python scripts/derive-audit-hash.py \
  --kind manifest \
  --json-file examples/external-auditor/batch-manifest.json \
  --pretty
```

PowerShell:

```powershell
python .\scripts\derive-audit-hash.py `
  --kind manifest `
  --json-file .\examples\external-auditor\batch-manifest.json `
  --pretty
```

### Step 3: Verify leaf inclusion in the batch root

Linux / WSL:

```bash
python scripts/verify-batch-leaf-proof.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --proof-file examples/external-auditor/batch-proof.json \
  --leaf-hash REPLACE_WITH_HASH_FROM_STEP_1
```

PowerShell:

```powershell
python .\scripts\verify-batch-leaf-proof.py `
  --rpc-url https://history.denotary.io `
  --verification-account verif `
  --proof-file .\examples\external-auditor\batch-proof.json `
  --leaf-hash REPLACE_WITH_HASH_FROM_STEP_1
```

### Step 4: Verify the anchored batch row

Linux / WSL:

```bash
python scripts/verify-external-audit.py \
  --rpc-url https://history.denotary.io \
  --verification-account verif \
  --mode batch \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --root-hash REPLACE_WITH_COMPUTED_ROOT \
  --manifest-hash REPLACE_WITH_MANIFEST_HASH \
  --leaf-count 100
```

PowerShell:

```powershell
python .\scripts\verify-external-audit.py `
  --rpc-url https://history.denotary.io `
  --verification-account verif `
  --mode batch `
  --submitter dbagentstest `
  --schema-id 1 `
  --policy-id 1 `
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef `
  --root-hash REPLACE_WITH_COMPUTED_ROOT `
  --manifest-hash REPLACE_WITH_MANIFEST_HASH `
  --leaf-count 100
```

### One-Command Batch Audit

Linux / WSL:

```bash
python scripts/verify-audit-chain.py \
  --mode batch \
  --row-json-file examples/external-auditor/batch-leaf.canonical.json \
  --proof-file examples/external-auditor/batch-proof.json \
  --submitter dbagentstest \
  --schema-id 1 \
  --policy-id 1 \
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

PowerShell:

```powershell
python .\scripts\verify-audit-chain.py `
  --mode batch `
  --row-json-file .\examples\external-auditor\batch-leaf.canonical.json `
  --proof-file .\examples\external-auditor\batch-proof.json `
  --submitter dbagentstest `
  --schema-id 1 `
  --policy-id 1 `
  --external-ref 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

## Expected Result

All helpers return JSON.

Successful verification means:

- `"ok": true`

Any mismatch returns:

- `"ok": false`

or exits with a non-zero process code.

## Boundary Reminder

These helpers verify:

- canonical payload hashing
- Merkle inclusion
- on-chain anchored state in `verif`

They do not independently discover:

- the database-side canonicalization rules
- which rows should have been included in a batch
- whether the operator omitted rows before building the manifest

For that part, the auditor still needs the agreed source extraction procedure and the operator-provided evidence package.
