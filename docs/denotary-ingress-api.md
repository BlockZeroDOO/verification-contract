# DeNotary Ingress API Baseline

## Purpose

This document describes the current off-chain baseline for stage 6:

- deterministic canonicalization
- single submit preparation
- batch submit preparation
- generation of `trace_id` and `request_id` for auditability

Implementation:

- [services/ingress_api.py](/c:/projects/verification-contract/services/ingress_api.py:1)

## Current scope

The service does not yet:

- sign transactions
- broadcast them to the network
- read on-chain tables directly
- track finality by itself

The service already does:

- validate request context
- canonicalize the payload
- compute `object_hash`, `external_ref_hash`, `root_hash`, and `manifest_hash`
- prepare payloads for `submit` and `submitroot`

## Endpoints

### `GET /healthz`

Returns a health-check response.

### `POST /v1/single/prepare`

Prepares a single anchoring request.

Minimal request body:

```json
{
  "submitter": "alice",
  "external_ref": "customer-001",
  "schema": {
    "id": 1,
    "version": "1.0.0",
    "active": true,
    "canonicalization_profile": "json-sorted-v1"
  },
  "policy": {
    "id": 10,
    "active": true,
    "allow_single": true,
    "allow_batch": false,
    "require_kyc": true,
    "min_kyc_level": 2
  },
  "kyc": {
    "active": true,
    "level": 2,
    "expires_at": "2026-12-31T00:00:00Z"
  },
  "payload": {
    "doc_id": "INV-001",
    "amount": 1200,
    "currency": "EUR"
  }
}
```

The response includes:

- `trace_id`
- `request_id`
- `received_at`
- `canonical_form`
- `object_hash`
- `external_ref_hash`
- `prepared_action`

By default, the response does not return raw `canonical_form`.

If deep debugging is needed, send:

```json
{
  "include_debug_material": true
}
```

and the response will include `canonical_form`.

### `POST /v1/batch/prepare`

Prepares a batch anchoring request.

Minimal request body:

```json
{
  "submitter": "alice",
  "external_ref": "batch-2026-04-14-001",
  "schema": {
    "id": 1,
    "version": "1.0.0",
    "active": true,
    "canonicalization_profile": "json-sorted-v1"
  },
  "policy": {
    "id": 20,
    "active": true,
    "allow_single": false,
    "allow_batch": true,
    "require_kyc": false,
    "min_kyc_level": 0
  },
  "items": [
    {
      "external_leaf_ref": "leaf-001",
      "payload": {
        "doc_id": "A-001",
        "amount": 10
      }
    },
    {
      "external_leaf_ref": "leaf-002",
      "payload": {
        "doc_id": "A-002",
        "amount": 20
      }
    }
  ]
}
```

The response includes:

- `trace_id`
- `request_id`
- `received_at`
- `leaf_hashes`
- `root_hash`
- `manifest`
- `manifest_hash`
- `external_ref_hash`
- `prepared_action`

By default, the response does not return raw batch material such as the full manifest or per-leaf canonical forms.

If deep debugging is needed, send:

```json
{
  "include_debug_material": true
}
```

and the response will include:

- `leaf_hashes`
- `manifest`
- `manifest_canonical_form`

## Canonicalization rules

Current baseline profile:

- `json-sorted-v1`

Rules:

- JSON is serialized deterministically
- object keys are sorted
- extra whitespace is removed
- arrays preserve original order
- `NaN` and `Infinity` are rejected
- encoding is UTF-8

Hash formulas:

- `object_hash = SHA-256(canonical_form_utf8_bytes)`
- `external_ref_hash = SHA-256(external_ref_utf8_bytes)`

## Batch rules

For the current batch baseline:

- each leaf is canonicalized independently
- `leaf_hash = SHA-256(canonical_leaf_form)`
- the Merkle root is built by pairwise SHA-256 over concatenated raw hash bytes
- if the number of leaves is odd, the last hash is duplicated at that tree level
- `manifest_hash = SHA-256(canonical_manifest_json)`

## Audit metadata

Every prepare response returns:

- `trace_id`
- `request_id`
- `received_at`

`request_id` is deterministically derived from:

- `submitter`
- `external_ref_hash`
- `object_hash` or `root_hash`
- `mode`

## Operational handoff

The current intended flow after `prepare` is:

1. take the returned `prepared_action`
2. sign and broadcast it outside the service
3. register the same `request_id` in the Finality Watcher
4. after inclusion, attach `tx_id` and `block_num`
5. if available, attach `commitment_id` or `batch_id` into watcher anchor metadata

Related docs:

- [docs/denotary-finality-services.md](/c:/projects/verification-contract/docs/denotary-finality-services.md:1)
- [docs/denotary-audit-api.md](/c:/projects/verification-contract/docs/denotary-audit-api.md:1)

## Hardening notes

The current ingress baseline now enforces:

- request body size limit
- maximum `external_ref` length
- maximum `external_leaf_ref` length
- maximum batch size
- maximum canonicalized material size
- Antelope account-name validation for `submitter`
- rejection of `null` payloads
- safer default responses without raw canonical material

## Run

Linux/macOS:

```bash
scripts/run-ingress-api.sh --host 127.0.0.1 --port 8080 --contract-account verification
```

Windows PowerShell:

```powershell
scripts/run-ingress-api.ps1 -Host 127.0.0.1 -Port 8080 -ContractAccount verification
```

## Next step

Logical next improvements after this baseline:

- pull schema, policy, and KYC context from on-chain or indexed read models
- add transaction assembly, signing, and broadcasting
- automate the handoff into finality tracking
