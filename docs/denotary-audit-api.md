# DeNotary Audit API Baseline

## Purpose

This baseline adds a read-only audit layer on top of the shared finality state so that we can:

- search records without reading the raw state file
- return the audit record, receipt, and proof chain from one API
- keep ingestion/finality write paths separate from public audit reads

Implementation:

- [services/audit_api.py](/c:/projects/verification-contract/services/audit_api.py:1)

## Current data source

The current Audit API reads the same watcher state backend used by:

- `Finality Watcher`
- `Receipt Service`

Recommended production runtime:

- `SQLite`

Compatibility mode still exists for:

- `runtime/finality-state.json`

## Endpoints

### `GET /healthz`

Health check.

### `GET /openapi.json`

Returns the OpenAPI specification for the public `Audit API` surface.

### `GET /docs`

Returns Swagger UI for interactive API exploration.

### `GET /v1/audit/requests/<request_id>`

Returns the audit record for a request.

### `GET /v1/audit/chain/<request_id>`

Returns:

- audit record
- finalized receipt when available
- proof chain

### `GET /v1/audit/by-external-ref/<external_ref_hash>`

Finds a record by `external_ref_hash`.

### `GET /v1/audit/by-tx/<tx_id>`

Finds a record by `tx_id`.

### `GET /v1/audit/by-commitment/<commitment_id>`

Finds a single-mode record by `commitment_id` when that ID has been attached to anchor metadata.

### `GET /v1/audit/by-batch/<batch_id>`

Finds a batch-mode record by `batch_id` when that ID has been attached to anchor metadata.

### `GET /v1/audit/search`

Supported query parameters:

- `mode`
- `status`
- `trust_state`
- `submitter`
- `contract`
- `external_ref_hash`
- `commitment_id`
- `batch_id`
- `limit`
- `offset`
- `format`

Example:

```text
/v1/audit/search?mode=single&status=finalized&submitter=alice&limit=20&offset=0
```

If `format=jsonl`, the API returns newline-delimited JSON for export-friendly downstream processing.

## Audit chain shape

`GET /v1/audit/chain/<request_id>` returns:

- `record`
- `receipt`
- `proof_chain`

The baseline `proof_chain` contains these stages:

- `request_registered`
- `transaction_verified`
- `transaction_included`
- `block_finalized`

`record` responses now also expose:

- `trust_state`
- `receipt_available`
- `inclusion_verified`
- `inclusion_verification_error`

## Privacy modes

The Audit API now supports:

- `full`
- `public`

`full` mode exposes the complete audit surface and is intended for trusted internal deployments.

`public` mode redacts correlation-heavy fields from:

- record payloads
- proof-chain details
- embedded receipt payloads

Configure it with:

```bash
scripts/run-audit-api.sh --privacy-mode public
```

Or in deployment env:

- `AUDIT_PRIVACY_MODE=public`

If finality is not reached yet, the last stage is returned with `pending` status. If a block is finalized but
transaction verification is still missing or failed, `block_finalized` stays `completed` while `transaction_verified`
shows the verification outcome separately.

## Attaching anchor IDs

To support lookups by `commitment_id` or `batch_id`, the watcher can merge extra anchor metadata after the request has been registered:

```text
POST /v1/watch/<request_id>/anchor
```

Example body:

```json
{
  "anchor": {
    "commitment_id": 42
  }
}
```

For batch mode:

```json
{
  "anchor": {
    "batch_id": 7
  }
}
```

## Run

Linux/macOS:

```bash
scripts/run-audit-api.sh
```

Windows PowerShell:

```powershell
scripts/run-audit-api.ps1
```

Swagger UI:

- `http://127.0.0.1:8083/docs`
- `http://127.0.0.1:8083/openapi.json`

## Next step

After this baseline, the natural follow-up is:

- index direct on-chain `commitments` and `batches`
- support lookup by on-chain IDs without manual anchor patching
- add batch inclusion proof retrieval
- unify audit reads over chain tables, finality state, and receipts
