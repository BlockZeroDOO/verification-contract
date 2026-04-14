# DeNotary L1 Backlog

## Назначение

Этот backlog переводит TSD v2 в очередность реализации для MVP и для optional-слоя.

## Epic 0. Discovery Baseline

### E0-1 Discovery pack

- Описание: собрать entity map, auth matrix, lifecycle model
- Зависимости: нет
- Acceptance criteria:
- есть документ discovery
- есть backlog
- есть минимум два ADR

### E0-2 MVP test outline

- Описание: зафиксировать минимальную тестовую матрицу по contract/API/finality/batch
- Зависимости: E0-1
- Acceptance criteria:
- тесты сгруппированы по слоям
- есть release gates для testnet

## Epic 1. Contract Core Refactor

### E1-1 Domain model draft

- Описание: спроектировать таблицы и индексы для новых registry сущностей
- Зависимости: E0-1
- Acceptance criteria:
- есть table/action matrix
- зафиксированы secondary indexes
- решен вопрос id generation

### E1-2 Clean deployment contract cutover

- Описание: зафиксировать fresh deployment на новых аккаунтах и убрать зависимость от legacy `proofs`
- Зависимости: E1-1
- Acceptance criteria:
- documented clean deploy assumption
- documented impact on action names and table names
- обновлены ожидания для deploy docs

### E1-3 Contract module split

- Описание: разложить код `verification` по registry-доменам
- Зависимости: E1-1
- Acceptance criteria:
- структура кода поддерживает дальнейшее расширение
- действия и таблицы не смешаны хаотично

## Epic 2. Access Registries

### E2-1 KYC registry

- Описание: реализовать таблицу и actions для KYC
- Зависимости: E1-3
- Acceptance criteria:
- есть `issuekyc`, `renewkyc`, `revoke`, `suspend`
- есть проверки active/expiry

### E2-2 Schema registry

- Описание: реализовать schema rules registry
- Зависимости: E1-3
- Acceptance criteria:
- есть `addschema`, `updateschema`, `deprecate`
- схема проверяется при submit

### E2-3 Policy registry

- Описание: реализовать policy rules registry
- Зависимости: E1-3
- Acceptance criteria:
- есть `allow_single`, `allow_batch`, `require_kyc`, `min_kyc_level`, `allow_zk`
- policy проверяется при submit

## Epic 3. Single Anchoring

### E3-1 Commitment table and indexes

- Описание: реализовать storage model для single record
- Зависимости: E2-1, E2-2, E2-3
- Acceptance criteria:
- запись создается с `submitter`, `schema_id`, `policy_id`, `hash`
- есть индексы по `submitter`, `schema_id`, `policy_id`, `status`

### E3-2 Submit validation path

- Описание: собрать full validation path для single submit
- Зависимости: E3-1
- Acceptance criteria:
- неактивная schema отклоняется
- policy без `allow_single` отклоняется
- KYC policy enforced

### E3-3 Lifecycle actions

- Описание: реализовать безопасные переходы `supersede/revoke/expire`
- Зависимости: E3-1
- Acceptance criteria:
- недопустимые переходы запрещены
- audit trail не теряется

### E3-4 Idempotency and duplicate protection

- Описание: ввести canonical request key
- Зависимости: E3-2
- Acceptance criteria:
- повторный submit того же запроса детерминированно обрабатывается
- replay path покрыт тестами

## Epic 4. Batch Anchoring

### E4-1 Batch table and indexes

- Описание: реализовать on-chain модель batch
- Зависимости: E2-2, E2-3
- Acceptance criteria:
- есть `root_hash`, `leaf_count`, `manifest_hash`, `schema_id`, `policy_id`
- есть индексирование по submitter/policy/schema

### E4-2 Batch submit flow

- Описание: реализовать `submitroot`
- Зависимости: E4-1
- Acceptance criteria:
- batch policy enforced
- root сохраняется детерминированно

### E4-3 Manifest linking and close flow

- Описание: реализовать `linkmanifest` и `closebatch`
- Зависимости: E4-2
- Acceptance criteria:
- manifest immutable по hash
- закрытый batch нельзя менять

## Epic 5. Ingestion Services

### E5-1 Canonicalization rules contract

- Описание: определить вход/выход canonicalization service
- Зависимости: E0-1
- Acceptance criteria:
- одинаковый input дает одинаковый canonical form
- output version-linked to schema

### E5-2 Ingress API single flow

- Описание: принять данные, канонизировать и отправить single tx
- Зависимости: E3-2, E5-1
- Acceptance criteria:
- API не отправляет tx без валидных prechecks
- request traceable end-to-end

### E5-3 Batch builder flow

- Описание: собрать leafs, Merkle root и manifest
- Зависимости: E4-2, E5-1
- Acceptance criteria:
- root воспроизводим
- inclusion proof воспроизводим

## Epic 6. Finality and Receipts

### E6-1 Finality watcher

- Описание: отслеживать `submitted -> included -> finalized`
- Зависимости: E3-2, E4-2
- Acceptance criteria:
- watcher связывает request id с tx id и block num
- finality определяется только после irreversible

### E6-2 Receipt service single

- Описание: выдавать receipt для single anchoring
- Зависимости: E6-1
- Acceptance criteria:
- receipt содержит `hash`, `tx_id`, `block_num`, `finality_flag`
- receipt не выдается до finality

### E6-3 Receipt service batch

- Описание: выдавать receipt для batch leaf
- Зависимости: E5-3, E6-1
- Acceptance criteria:
- receipt содержит `root`, `inclusion_proof`, `tx_id`
- leaf proof сверяется с `manifest_hash`

## Epic 7. Indexer and Audit API

### E7-1 Indexer baseline

- Описание: индексировать chain tables и tx events
- Зависимости: E3-1, E4-1, E6-1
- Acceptance criteria:
- single и batch сущности доступны в read model
- запросы работают без обращения к raw node вручную

### E7-2 Audit API

- Описание: реализовать внешнюю проверку записей и receipts
- Зависимости: E7-1, E6-2, E6-3
- Acceptance criteria:
- есть поиск по `commitment_id`
- есть поиск по `external_ref`
- есть выдача receipt и verification chain

## Epic 8. Security Hardening

### E8-1 Replay protection

- Описание: проверить и усилить идемпотентность
- Зависимости: E3-4, E4-3
- Acceptance criteria:
- replay single и batch сценариев покрыт тестами

### E8-2 Metadata leakage review

- Описание: оценить, какие поля светят лишние данные
- Зависимости: E3-1, E4-1
- Acceptance criteria:
- зафиксированы safe defaults для `external_ref` и manifest metadata

### E8-3 Permission boundary review

- Описание: проверить governance и submitter authority model
- Зависимости: E2-1, E2-2, E2-3, E3-3, E4-3
- Acceptance criteria:
- нет generic status mutation path без строгих правил
- роли и полномочия документированы

## Epic 9. Testnet Rollout

### E9-1 Test matrix

- Описание: сформировать test matrix по уровням
- Зависимости: E3-4, E4-3, E6-3, E7-2
- Acceptance criteria:
- есть contract tests
- есть API tests
- есть finality tests

### E9-2 Testnet deployment runbook

- Описание: обновить шаги сборки, деплоя и smoke test
- Зависимости: E9-1
- Acceptance criteria:
- команда может развернуть стенд без чтения исходников

## Epic 10. Optional Proof Layer

### E10-1 Proof registry

- Описание: реализовать optional proof storage
- Зависимости: E7-2
- Acceptance criteria:
- core flow не зависит от ZK
- proof layer подключается отдельно

### E10-2 ZK verification path

- Описание: определить proof worker interface и verify flow
- Зависимости: E10-1
- Acceptance criteria:
- trusted path и ограничения documented

## Release slices

### Release A. On-chain foundation

- E1-1
- E1-2
- E1-3
- E2-1
- E2-2
- E2-3
- E3-1
- E3-2

### Release B. End-to-end anchoring

- E3-3
- E3-4
- E4-1
- E4-2
- E4-3
- E5-1
- E5-2
- E5-3

### Release C. Verification pipeline

- E6-1
- E6-2
- E6-3
- E7-1
- E7-2
- E8-1
- E8-2
- E8-3
- E9-1
- E9-2
