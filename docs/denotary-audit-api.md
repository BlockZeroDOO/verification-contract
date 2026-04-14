# DeNotary Audit API Baseline

## Purpose

This baseline adds a read-only audit layer on top of `runtime/finality-state.json` so that we can:

- search records without reading the raw state file
- return the audit record, receipt, and proof chain from one API
- keep ingestion/finality write paths separate from public audit reads

Implementation:

- [services/audit_api.py](/c:/projects/verification-contract/services/audit_api.py:1)

## Current data source

The current Audit API reads a file-based read model:

- `runtime/finality-state.json`

This is a temporary baseline before a fuller indexer over chain tables and transaction events.

## Endpoints

### `GET /healthz`

Health check.

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
- `transaction_included`
- `block_finalized`

If finality is not reached yet, the last stage is returned with `pending` status.

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

## Next step

After this baseline, the natural follow-up is:

- index direct on-chain `commitments` and `batches`
- support lookup by on-chain IDs without manual anchor patching
- add batch inclusion proof retrieval
- unify audit reads over chain tables, finality state, and receipts
