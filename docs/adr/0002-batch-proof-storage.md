# ADR 0002: Batch Proof Storage Model

## Status

Accepted for MVP planning.

## Context

TSD v2 требует поддержать batch anchoring:

- сбор данных в batch
- построение Merkle tree
- публикацию `root_hash` on-chain
- выдачу inclusion proof для отдельного leaf

Если хранить manifest и весь proof material on-chain, система быстро упрется в стоимость RAM/CPU/NET и потеряет одно из ключевых преимуществ batch-first архитектуры.

Нужно определить минимальный on-chain набор данных, достаточный для верификации, и вынести остальное в off-chain read model.

## Decision

Для MVP принимается следующая модель:

- on-chain `BatchRegistry` хранит:
- `id`
- `submitter`
- `root_hash`
- `leaf_count`
- `schema_id`
- `policy_id`
- `manifest_hash`
- `created_at`

- off-chain хранит:
- immutable batch manifest
- canonical leaf list
- inclusion proof material для каждого leaf

- `manifest_hash` является ссылкой на immutable off-chain manifest
- `Receipt Service` выдает inclusion proof на основе manifest и indexed chain record
- клиент проверяет:
- leaf hash
- путь inclusion proof до `root_hash`
- привязку `root_hash` к on-chain batch record
- finality batch transaction

## Consequences

Плюсы:

- on-chain хранит только то, что действительно нужно для anchored fact
- batch остается дешевым и масштабируемым
- manifest/proof формат можно эволюционировать вне контракта

Минусы:

- нужен надежный immutable storage/read path для manifest
- необходимо четко версионировать manifest format
- audit слой становится обязательной частью пользовательской проверки

## Rejected alternatives

### Alternative 1. Хранить inclusion proofs on-chain

Отклонено, потому что:

- слишком дорого по ресурсам
- не соответствует `off-chain heavy processing`

### Alternative 2. Хранить только `root_hash` без `manifest_hash`

Отклонено, потому что:

- теряется жесткая ссылка на состав batch
- ухудшается воспроизводимость аудита и доказательства leaf inclusion
