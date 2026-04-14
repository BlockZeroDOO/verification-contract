# DeNotary Finality Watcher And Receipt Service

## Purpose

Этот этап добавляет минимальный off-chain baseline для:

- отслеживания перехода `submitted -> included -> finalized`
- выдачи receipt только после finality

Реализация:

- [services/finality_watcher.py](/c:/projects/verification-contract/services/finality_watcher.py:1)
- [services/receipt_service.py](/c:/projects/verification-contract/services/receipt_service.py:1)
- [services/finality_store.py](/c:/projects/verification-contract/services/finality_store.py:1)

## Finality model

Watcher использует pragmatic baseline:

- request регистрируется через `POST /v1/watch/register`
- когда появляется `tx_id` и `block_num`, request помечается как `included`
- watcher опрашивает `v1/chain/get_info`
- как только `last_irreversible_block_num >= block_num`, request помечается как `finalized`

Это соответствует принятому ADR:

- business status остается on-chain
- finality status живет в off-chain read model

## Storage

Состояние хранится в JSON файле:

- по умолчанию `runtime/finality-state.json`

Там фиксируются:

- `request_id`
- `trace_id`
- `mode`
- `tx_id`
- `block_num`
- `status`
- `finalized_at`
- `chain_state`
- anchor metadata

## Finality Watcher API

### `GET /healthz`

Health-check.

### `POST /v1/watch/register`

Регистрирует request для наблюдения.

Пример:

```json
{
  "request_id": "req-123",
  "trace_id": "trace-123",
  "mode": "single",
  "submitter": "alice",
  "contract": "verification",
  "rpc_url": "https://dev-history.globalforce.io",
  "anchor": {
    "object_hash": "abcd...",
    "external_ref_hash": "ef01..."
  }
}
```

### `POST /v1/watch/<request_id>/included`

Добавляет `tx_id` и `block_num` после chain inclusion.

Пример:

```json
{
  "tx_id": "abcd1234",
  "block_num": 12345678
}
```

### `POST /v1/watch/<request_id>/poll`

Принудительно опрашивает chain state для одного request.

### `POST /v1/watch/poll`

Принудительно опрашивает все зарегистрированные requests.

### `GET /v1/watch/<request_id>`

Возвращает текущее watcher state.

## Receipt API

### `GET /healthz`

Health-check.

### `GET /v1/receipts/<request_id>`

Возвращает receipt только если request уже finalized.

Single receipt содержит:

- `request_id`
- `trace_id`
- `object_hash`
- `external_ref_hash`
- `tx_id`
- `block_num`
- `finality_flag`
- `finalized_at`

Batch receipt содержит:

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

## Run

Watcher:

```bash
scripts/run-finality-watcher.sh --rpc-url https://dev-history.globalforce.io
```

Receipt service:

```bash
scripts/run-receipt-service.sh
```

Windows PowerShell:

```powershell
scripts/run-finality-watcher.ps1 -RpcUrl https://dev-history.globalforce.io
scripts/run-receipt-service.ps1
```

## Expected flow

1. `Ingress API` готовит `request_id` и action payload.
2. Внешний broadcaster отправляет tx.
3. Watcher request регистрируется.
4. После inclusion вызывается `.../included` с `tx_id` и `block_num`.
5. Watcher дожидается irreversible finality.
6. Receipt service начинает отдавать finalized receipt.

## Next step

После этого baseline логично добавить:

- tx broadcaster integration
- автоматическую передачу данных из ingress в watcher
- indexer и audit read model вместо чисто file-based store
