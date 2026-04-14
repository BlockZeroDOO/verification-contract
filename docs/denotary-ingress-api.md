# DeNotary Ingress API Baseline

## Purpose

Этот документ фиксирует минимальный off-chain baseline для этапа 6:

- deterministic canonicalization
- single submit preparation
- batch submit preparation
- trace id / request id для аудита

Текущая реализация находится в [services/ingress_api.py](/c:/projects/verification-contract/services/ingress_api.py:1).

## Current Scope

Сервис пока не:

- подписывает транзакции
- отправляет их в сеть
- читает on-chain tables напрямую
- отслеживает finality

Сервис уже:

- валидирует входной request context
- канонизирует payload
- вычисляет `object_hash`, `external_ref_hash`, `root_hash`, `manifest_hash`
- подготавливает payload под actions `submit` и `submitroot`

## Endpoints

### `GET /healthz`

Возвращает базовый health-check.

### `POST /v1/single/prepare`

Готовит single anchoring request.

Минимальный request body:

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

### `POST /v1/batch/prepare`

Готовит batch anchoring request.

Минимальный request body:

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

## Canonicalization Rules

Текущий baseline-профиль:

- `json-sorted-v1`

Правила:

- JSON сериализуется детерминированно
- ключи объектов сортируются
- лишние пробелы убираются
- массивы сохраняют исходный порядок
- `NaN` и `Infinity` запрещены
- кодировка: UTF-8

Формула hash:

- `object_hash = SHA-256(canonical_form_utf8_bytes)`
- `external_ref_hash = SHA-256(external_ref_utf8_bytes)`

## Batch Rules

Для batch baseline:

- каждый leaf canonicalize-ится отдельно
- `leaf_hash = SHA-256(canonical_leaf_form)`
- Merkle root строится попарным SHA-256 от конкатенации raw hash bytes
- при нечетном числе leaf последний hash дублируется на уровне дерева
- `manifest_hash = SHA-256(canonical_manifest_json)`

## Audit Metadata

Каждый prepare-response возвращает:

- `trace_id`
- `request_id`
- `received_at`

`request_id` детерминированно считается из:

- `submitter`
- `external_ref_hash`
- `object_hash` или `root_hash`
- `mode`

## Run

Linux/macOS:

```bash
scripts/run-ingress-api.sh --host 127.0.0.1 --port 8080 --contract-account verification
```

Windows PowerShell:

```powershell
scripts/run-ingress-api.ps1 -Host 127.0.0.1 -Port 8080 -ContractAccount verification
```

## Next Step

Следующий шаг после этого baseline:

- подключить on-chain read model вместо передачи `schema/policy/kyc` в request body
- добавить tx assembly/sign/broadcast
- передать prepared tx в `Finality Watcher` и `Receipt Service`
