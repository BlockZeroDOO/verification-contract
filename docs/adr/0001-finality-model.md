# ADR 0001: Finality Model

## Status

Accepted for MVP planning.

## Context

TSD v2 определяет, что запись считается заверенной только после:

- включения транзакции в блок
- перехода блока в irreversible
- доступности данных для верификации

При этом текущий контрактный слой не является хорошим местом для детекции irreversible finality сам по себе. On-chain state умеет хранить бизнес-факт anchoring, но не является самостоятельным источником события "этот блок уже irreversible" без внешнего наблюдателя.

Есть риск смешать:

- business status записи
- технический статус включения и finality

Это приведет к усложненному auth model, лишним служебным actions и путанице в audit semantics.

## Decision

Для MVP принимается следующая модель:

- on-chain хранит факт anchoring и business lifecycle записи
- off-chain `Finality Watcher` отслеживает путь `submitted -> included -> finalized`
- `Receipt Service` выдает receipt только после подтвержденного irreversible
- finality status не записывается в основной `status` поля on-chain реестров
- `Indexer / Audit API` хранит и выдает read model с technical states и finality metadata

Минимальный состав receipt:

- `hash` или `root`
- `tx_id`
- `block_num`
- `finality_flag`
- для batch: `inclusion_proof`

## Consequences

Плюсы:

- сохраняется чистая граница между business state и network finality
- не нужен отдельный chain-side action вроде `markfinal` в MVP
- упрощается permission model
- легче строить audit API и повторяемые receipts

Минусы:

- появляется обязательный off-chain компонент `Finality Watcher`
- нужны мониторинг и alerting на зависшие tx/finality transitions
- пользователю нужен read path через receipt/indexer, а не только raw table query

## Rejected alternatives

### Alternative 1. Писать finality обратно on-chain

Отклонено для MVP, потому что:

- добавляет service authority и новый mutation path
- повышает риск расхождения business и technical статусов
- усложняет контракт без критической пользы на первом релизе

### Alternative 2. Считать inclusion достаточной заверкой

Отклонено, потому что:

- противоречит TSD v2
- ломает модель доверия `consensus + irreversible`
