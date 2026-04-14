# DeNotary Finality Watcher And Receipt Service

## Purpose

This stage adds the off-chain finality baseline required for DeNotary receipts:

- track the transition `submitted -> included -> finalized`
- keep finality outside the on-chain business status model
- issue receipts only after irreversible finality

Implementation:

- [services/finality_watcher.py](/c:/projects/verification-contract/services/finality_watcher.py:1)
- [services/receipt_service.py](/c:/projects/verification-contract/services/receipt_service.py:1)
- [services/finality_store.py](/c:/projects/verification-contract/services/finality_store.py:1)

Related read path:

- [services/audit_api.py](/c:/projects/verification-contract/services/audit_api.py:1)
- [docs/denotary-audit-api.md](/c:/projects/verification-contract/docs/denotary-audit-api.md:1)

## Finality model

The watcher uses a pragmatic MVP model:

- a request is registered through `POST /v1/watch/register`
- once `tx_id` and `block_num` are known, the request becomes `included`
- the watcher polls `/v1/chain/get_info`
- when `last_irreversible_block_num >= block_num`, the request becomes `finalized`

This matches the current ADR:

- business lifecycle stays on-chain
- finality lifecycle stays in an off-chain read model

## Storage

State is stored in:

- `runtime/finality-state.json`

The file currently tracks:

- `request_id`
- `trace_id`
- `mode`
- `submitter`
- `contract`
- `tx_id`
- `block_num`
- `status`
- `registered_at`
- `updated_at`
- `finalized_at`
- `failed_at`
- `failure_reason`
- `failure_details`
- `chain_state`
- `anchor` metadata

## Finality Watcher API

### `GET /healthz`

Health check.

### `POST /v1/watch/register`

Registers a request for watching.

Example:

```json
{
  "request_id": "req-123",
  "trace_id": "trace-123",
  "mode": "single",
  "submitter": "alice",
  "contract": "verification",
  "rpc_url": "https://history.denotary.io",
  "anchor": {
    "object_hash": "abcd...",
    "external_ref_hash": "ef01..."
  }
}
```

For batch mode, `anchor` can contain `root_hash`, `manifest_hash`, `leaf_count`, and `external_ref_hash`.

### `POST /v1/watch/<request_id>/included`

Attaches inclusion metadata after the transaction is accepted into a block.

Example:

```json
{
  "tx_id": "abcd1234",
  "block_num": 12345678
}
```

### `POST /v1/watch/<request_id>/anchor`

Merges extra anchor metadata into an already registered request.

This is currently used to attach on-chain IDs needed by the Audit API.

Single-mode example:

```json
{
  "anchor": {
    "commitment_id": 42
  }
}
```

Batch-mode example:

```json
{
  "anchor": {
    "batch_id": 7
  }
}
```

Rules:

- `commitment_id` is valid only for `single` mode
- `batch_id` is valid only for `batch` mode
- existing anchor IDs and hashes cannot be overwritten with different values

### `POST /v1/watch/<request_id>/poll`

Forces a one-request finality poll.

### `POST /v1/watch/<request_id>/failed`

Marks a request as failed when broadcasting or reconciliation determines that it will not finalize.

Example:

```json
{
  "reason": "tx_dropped",
  "details": {
    "stage": "broadcast"
  }
}
```

### `POST /v1/watch/poll`

Forces polling for all registered requests.

### `GET /v1/watch/<request_id>`

Returns the current watcher state.

## Receipt API

### `GET /healthz`

Health check.

### `GET /v1/receipts/<request_id>`

Returns a receipt only when the request is already finalized.

Single receipt fields:

- `request_id`
- `trace_id`
- `object_hash`
- `external_ref_hash`
- `tx_id`
- `block_num`
- `finality_flag`
- `finalized_at`

Batch receipt fields:

- `request_id`
- `trace_id`
- `root_hash`
- `manifest_hash`
- `external_ref_hash`
- `leaf_count`
- `tx_id`
- `block_num`
- `finality_flag`
- `finalized_at`

## Expected flow

1. The Ingress API prepares `request_id`, hashes, and action payload.
2. An external broadcaster signs and submits the transaction.
3. The watcher registers the request.
4. After inclusion, the watcher receives `tx_id` and `block_num`.
5. If needed, the watcher is updated with `commitment_id` or `batch_id`.
6. The watcher waits for irreversible finality.
7. The Receipt Service starts returning finalized receipts.
8. The Audit API can expose the record, receipt, and proof chain in one read path.

## Hardening notes

The current watcher baseline now enforces:

- request body size limit
- strict `request_id` validation as 64-char hex
- strict `tx_id` validation as 64-char hex
- Antelope account-name validation for `submitter` and `contract`
- optional shared-token auth for watcher mutation endpoints
- idempotent `register` behavior for matching requests
- rejection of conflicting re-use of an existing `request_id`
- rejection of `tx_id` and `block_num` rewrites once recorded
- explicit `failed` state for dropped or rejected requests
- no regression from `finalized` back to `included`

## Run

Watcher:

```bash
scripts/run-finality-watcher.sh --rpc-url https://history.denotary.io
```

With mutation auth:

```bash
scripts/run-finality-watcher.sh --rpc-url https://history.denotary.io --auth-token your-shared-token
```

Receipt service:

```bash
scripts/run-receipt-service.sh
```

Windows PowerShell:

```powershell
scripts/run-finality-watcher.ps1 -RpcUrl https://history.denotary.io
scripts/run-receipt-service.ps1
```

## Next step

The natural follow-up after this baseline is:

- broadcaster integration
- automatic handoff from ingress into watcher registration
- richer indexed read model beyond the file-based state store
