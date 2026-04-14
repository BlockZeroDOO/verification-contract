# DeNotary L1 Contract Core Draft

## Purpose

Этот документ закрывает этап 1 для on-chain core и фиксирует:

- целевую структуру контракта `verification`
- table/action matrix для MVP
- primary/secondary index strategy
- стратегию генерации ID
- clean deployment assumption без миграции старых таблиц

## Stage 1 Outcome

На данном этапе принимается следующая рамка:

- DeNotary L1 MVP реализуется в одном Antelope-контракте `verification`
- контракт деплоится на чистый аккаунт
- миграция существующей таблицы `proofs` не требуется
- текущая платежная модель может быть сохранена как отдельный слой, но не должна определять shape core registry model

## Contract Boundaries

Контракт `verification` в MVP состоит из трех logical zones.

### 1. Governance registries

Сюда входят:

- `KYCRegistry`
- `SchemaRegistry`
- `PolicyRegistry`

Эта зона отвечает за:

- кто допускается к записи
- какая схема данных используется
- какие режимы записи разрешены

### 2. Anchoring core

Сюда входят:

- `CommitmentRegistry`
- `BatchRegistry`
- business status transitions

Эта зона отвечает за:

- single anchoring
- batch anchoring
- lifecycle anchored record

### 3. Payment layer

Сюда входят:

- accepted payment tokens
- payment memo parsing
- treasury/withdraw path

Эта зона отвечает за:

- экономику submit path
- но не за finality semantics и не за business lifecycle записи

## Target On-Chain Tables

### `kyc`

Назначение:

- хранение KYC допуска по account

Fields:

- `account: name`
- `level: uint8_t`
- `provider: string`
- `jurisdiction: string`
- `active: bool`
- `issued_at: time_point_sec`
- `expires_at: time_point_sec`

Indexes:

- primary: `account`
- optional secondary: `active` не нужен, если основной lookup всегда по account

### `schemas`

Назначение:

- хранение canonicalization/hash rules

Fields:

- `id: uint64_t`
- `version: string`
- `canonicalization_hash: checksum256`
- `hash_policy: checksum256`
- `active: bool`
- `created_at: time_point_sec`
- `updated_at: time_point_sec`

Indexes:

- primary: `id`
- secondary: `active + id` не обязателен для MVP

ID strategy:

- `id` задается governance явно
- это позволяет держать стабильные schema identifiers без обязательного on-chain counter для registry слоя

### `policies`

Назначение:

- хранение правил допуска single/batch/ZK/KYC

Fields:

- `id: uint64_t`
- `allow_single: bool`
- `allow_batch: bool`
- `require_kyc: bool`
- `min_kyc_level: uint8_t`
- `allow_zk: bool`
- `active: bool`
- `created_at: time_point_sec`
- `updated_at: time_point_sec`

Indexes:

- primary: `id`
- secondary: `active + id` не обязателен для MVP

ID strategy:

- `id` задается governance явно
- policy identifiers остаются стабильными и предсказуемыми для off-chain конфигурации

### `commitments`

Назначение:

- single record anchoring

Fields:

- `id: uint64_t`
- `submitter: name`
- `schema_id: uint64_t`
- `policy_id: uint64_t`
- `hash: checksum256`
- `external_ref: checksum256`
- `request_key: checksum256`
- `submitted_tx: checksum256`
- `block_num: uint32_t`
- `created_at: time_point_sec`
- `status: uint8_t`

Indexes:

- primary: `id`
- secondary: `submitter`
- secondary: `schema_id`
- secondary: `policy_id`
- secondary: `status`
- secondary: `request_key`
- optional secondary: `external_ref`

Обоснование:

- `request_key` нужен для идемпотентности
- `external_ref` нужен как внешний ключ поиска, но лучше хранить его в виде hash
- `submitted_tx` можно сделать optional, если решим не записывать tx metadata on-chain в MVP

### `batches`

Назначение:

- batch anchoring

Fields:

- `id: uint64_t`
- `submitter: name`
- `root_hash: checksum256`
- `leaf_count: uint32_t`
- `schema_id: uint64_t`
- `policy_id: uint64_t`
- `manifest_hash: checksum256`
- `request_key: checksum256`
- `submitted_tx: checksum256`
- `block_num: uint32_t`
- `created_at: time_point_sec`
- `status: uint8_t`

Indexes:

- primary: `id`
- secondary: `submitter`
- secondary: `schema_id`
- secondary: `policy_id`
- secondary: `status`
- secondary: `request_key`

### `paytokens`

Назначение:

- платежный конфиг

Статус:

- таблица может быть сохранена почти без изменений
- она orthogonal к registry core

### `counters`

Назначение:

- централизованная генерация monotonic IDs

Fields:

- `next_commitment_id: uint64_t`
- `next_batch_id: uint64_t`
- `next_proof_id: uint64_t`

Причина:

- governance registries используют явно задаваемые IDs
- timestamp-based id generation в текущем `proofs` не подходит для будущих anchored entities
- singleton counter дает детерминированную и тестируемую генерацию для `commitments`, `batches` и optional proof layer

## Business Status Model

Для `commitments`:

- `0 = active`
- `1 = superseded`
- `2 = revoked`
- `3 = expired`

Для `batches`:

- `0 = open`
- `1 = closed`

Важно:

- finality state не входит в эти статусы

## Target Actions

### Governance registries

| Action | Назначение | Auth |
|---|---|---|
| `issuekyc` | выдать KYC | `get_self()` или выделенный admin |
| `renewkyc` | продлить KYC | `get_self()` или выделенный admin |
| `revokekyc` | отозвать KYC | `get_self()` или governance |
| `suspendkyc` | приостановить KYC | `get_self()` или governance |
| `addschema` | создать schema | `get_self()` или schema admin |
| `updateschema` | обновить schema | `get_self()` или schema admin |
| `deprecate` | вывести schema из активного использования | `get_self()` или governance |
| `setpolicy` | создать или обновить policy | `get_self()` или policy admin |
| `enablezk` | включить optional capability | `get_self()` или policy admin |
| `disablezk` | выключить optional capability | `get_self()` или policy admin |

### Anchoring core

| Action | Назначение | Auth |
|---|---|---|
| `submit` | single anchoring | `submitter` |
| `supersede` | перевести запись в superseded | `submitter` или governance |
| `revokecmmt` | перевести запись в revoked | governance |
| `expirecmmt` | перевести запись в expired | governance/maintenance |
| `submitroot` | batch anchoring | `submitter` |
| `linkmanifest` | связать batch с immutable manifest | `submitter` или service model позже |
| `closebatch` | закрыть batch | `submitter` или governance |

### Optional layer

| Action | Назначение | Auth |
|---|---|---|
| `submitproof` | optional proof submit | future |
| `verifyproof` | optional proof verification | future |

### Payment layer

| Action | Назначение | Auth |
|---|---|---|
| `setpaytoken` | конфиг платежного токена | `get_self()` |
| `rmpaytoken` | удаление платежного токена | `get_self()` |
| `withdraw` | вывод treasury | `get_self()` |
| `ontransfer` | paid ingress path | token notify |

## Action Rules

### `submit`

Обязательные проверки:

- `submitter` существует
- `schema_id` существует и `active = true`
- `policy_id` существует и `active = true`
- policy разрешает `allow_single`
- если policy требует KYC, то:
- KYC запись существует
- `active = true`
- `expires_at` не истек
- `level >= min_kyc_level`
- `request_key` еще не использован

Результат:

- создается row в `commitments`
- `status = active`
- выделяется новый monotonic `id`

### `submitroot`

Обязательные проверки:

- policy разрешает `allow_batch`
- schema активна
- policy активна
- KYC policy enforced при необходимости
- `leaf_count > 0`
- `request_key` уникален

Результат:

- создается row в `batches`
- `status = open`

### `supersede`

Правила:

- исходная запись должна быть `active`
- terminal status менять нельзя
- для MVP действие меняет только статус исходной записи
- связь со следующей записью можно добавить на этапе 3, если понадобится явный successor reference

### `closebatch`

Правила:

- batch должен быть `open`
- закрытый batch менять нельзя

## ID Generation Strategy

Для MVP выбирается monotonic singleton-based strategy.

Правила:

- `schemas` и `policies` используют явно задаваемые governance IDs
- `commitments`, `batches` и optional proof entities используют свои `next_*_id`
- ID выделяется только в успешной action
- стартовое значение для каждого счетчика равно `1`
- `0` зарезервирован как invalid/unset sentinel

Плюсы:

- детерминированность
- простые тесты
- отсутствие зависимости от времени блока
- отсутствие коллизий при нескольких insert в один и тот же second

## Secondary Index Strategy

Минимально нужные secondary indexes:

### `commitments`

- `bysubmitter`
- `byschemaid`
- `bypolicyid`
- `bystatus`
- `byrequest`

Опционально:

- `byexternal`

### `batches`

- `bysubmitter`
- `byschemaid`
- `bypolicyid`
- `bystatus`
- `byrequest`

### `paytokens`

- сохранить `bytokensym`

## Clean Deployment Assumption

Так как контракт будет деплоиться на чистые аккаунты:

- миграция `proofs -> commitments` не проектируется
- backward compatibility с текущим action `record(...)` не требуется
- можно безопасно переименовать действия и таблицы под целевую модель
- deploy docs должны прямо отражать fresh deployment flow

Практическое следствие:

- текущий `record(...)` рассматривается как legacy path и не является частью целевого MVP
- текущая структура `proofs` не ограничивает новую domain model

## Code Structure Draft

Рекомендуемая раскладка файлов на этапе реализации:

- `include/verification.hpp`
- `include/verification/constants.hpp`
- `include/verification/tables.hpp`
- `include/verification/validation.hpp`
- `include/verification/ids.hpp`
- `src/verification.cpp`

Если хотим минимизировать churn, можно оставить один публичный `verification.hpp`, но внутри кода группировать секции так:

- constants
- table structs
- action declarations
- validation helpers
- id helpers
- payment helpers

## Release Criteria For Stage 1

Этап 1 считается завершенным, когда:

- table/action matrix зафиксирован
- index strategy зафиксирована
- ID generation strategy выбрана
- clean deploy assumption зафиксирован
- команда может переходить к реализации `KYC`, `Schema`, `Policy` без архитектурных разворотов
