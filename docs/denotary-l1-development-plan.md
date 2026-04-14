# План разработки по ТЗ DeNotary L1 (TSD v2)

## 1. Исходная точка

Текущее состояние репозитория:

- `verification` уже реализует базовую immutable proof registry с оплатой через `*::transfer`
- `dfs` существует как отдельный экономический/scaffold-контракт и не покрывает требования TSD v2
- off-chain сервисы из ТЗ в репозитории пока отсутствуют

Разрыв между текущим состоянием и ТЗ:

- нет реестров `KYCRegistry`, `SchemaRegistry`, `PolicyRegistry`
- нет сущностей `CommitmentRegistry`, `BatchRegistry`, `RecordStatusRegistry`, `ProofRegistry`
- нет batch anchoring и Merkle/inclusion proof потока
- нет `Finality Watcher`, `Receipt Service`, `Indexer / Audit API`
- текущая модель `verification.proofs` хранит только факт платной записи, но не покрывает policy/schema/finality lifecycle

## 2. Рекомендуемые рамки MVP

Чтобы не расползтись по объему, предлагается зафиксировать MVP так:

- включить: `KYCRegistry`, `SchemaRegistry`, `PolicyRegistry`, `CommitmentRegistry`, `BatchRegistry`, `RecordStatusRegistry`
- включить off-chain: `Ingress API`, `Canonicalization Service`, `Batch Builder`, `Finality Watcher`, `Receipt Service`, `Indexer / Audit API`
- оставить опционально: `ProofRegistry` и ZKP-поток
- сохранить оплату как отдельный слой, но не смешивать ее с логикой finality и proof lifecycle

Ключевое архитектурное допущение для плана:

- на первом этапе core-реестры реализуются в рамках одного контракта `verification` с отдельными таблицами и action-группами
- `dfs` не трогаем, пока не появится отдельное требование связать экономику DFS с DeNotary L1
- если позже понадобится жесткое разделение по permission boundary, реестры можно вынести в отдельные контракты после стабилизации модели данных

## 3. Главные архитектурные решения до старта кодинга

Перед активной разработкой нужно зафиксировать три решения:

1. Что считается "заверенной записью" в коде и API.
   Рекомендуемо разделить состояния:
   - `accepted` — запрос принят
   - `included` — транзакция попала в блок
   - `finalized` — блок стал irreversible

2. Где хранится finality truth.
   Рекомендуемо:
   - on-chain хранит данные записи и ее business status
   - off-chain `Finality Watcher` отслеживает inclusion/finality
   - `Receipt Service` выдает проверяемый receipt только после irreversible

3. Где живет batch inclusion proof.
   Рекомендуемо:
   - on-chain хранить только `root_hash`, `manifest_hash`, метаданные batch
   - off-chain хранить manifest и выдавать inclusion proof через `Receipt Service`/`Audit API`

## 4. Пошаговый план разработки

### Этап 0. Discovery и декомпозиция ТЗ

Цель:

- перевести ТЗ в backlog, контракты, API и тестовые сценарии

Задачи:

- описать entity map: KYC, schema, policy, commitment, batch, status, proof
- зафиксировать state machine записи и batch
- подготовить action/table matrix с auth-правами
- решить, какие поля обязательны в MVP, а какие откладываются
- подготовить ADR по finality model и storage model для batch proof

Результат этапа:

- backlog по эпикам
- схема данных и auth matrix
- список API/сервисов для первой поставки

### Этап 1. Рефакторинг contract core под новую модель

Цель:

- подготовить `verification` к расширению без смешивания старой proof-модели и новой registry-модели

Задачи:

- выделить доменные секции контракта по registry-модулям
- спроектировать primary/secondary indexes под `schema_id`, `policy_id`, `submitter`, `status`
- определить стратегию генерации `uint64_t id`
- зафиксировать clean deployment модель на новых аккаунтах без миграции старых таблиц
- обновить README и build/deploy сценарии под новый состав контракта

Результат этапа:

- согласованная структура on-chain модуля
- зафиксированная стратегия fresh deploy без legacy migration

### Этап 2. Реализация базовых реестров допуска и правил

Цель:

- закрыть foundation слой: кто может писать и по каким правилам

Задачи:

- реализовать `KYCRegistry`
- реализовать `SchemaRegistry`
- реализовать `PolicyRegistry`
- ввести проверки:
  - `require_kyc`
  - `min_kyc_level`
  - активность схемы
  - активность policy
- покрыть unit/contract tests на позитивные и негативные сценарии

Definition of Done:

- запись нельзя создать без выполнения policy/schema/KYC ограничений
- все governance actions валидируют входные данные и права доступа

### Этап 3. Реализация single-record потока

Цель:

- собрать основной путь `hash anchoring` для одиночной записи

Задачи:

- реализовать `CommitmentRegistry`
- добавить `submit`, `supersede`, `setstatus`, `linkproof`
- хранить:
  - `submitter`
  - `schema_id`
  - `policy_id`
  - `hash`
  - `external_ref`
  - `block_num`
  - `created_at`
  - `status`
- определить, кто и когда обновляет `block_num`/status после inclusion/finality
- добавить защиту от replay/duplicate requests

Definition of Done:

- одиночная запись создается, проходит валидации и может быть найдена для последующей верификации
- supersede/revoke/expire сценарии не ломают audit trail

### Этап 4. Реализация batch anchoring потока

Цель:

- добавить масштабируемый поток массовой фиксации данных

Задачи:

- реализовать `BatchRegistry`
- добавить `submitroot`, `closebatch`, `linkmanifest`
- определить формат batch manifest
- определить формат Merkle leaf canonicalization
- зафиксировать off-chain контракт между `Batch Builder` и `Receipt Service`
- покрыть сценарии:
  - создание batch
  - финализация batch
  - выдача inclusion proof для leaf

Definition of Done:

- batch root фиксируется on-chain
- manifest и inclusion proof воспроизводимы и проверяемы off-chain

### Этап 5. Жизненный цикл и статусы записей

Цель:

- отделить business lifecycle от события включения в irreversible block

Задачи:

- реализовать `RecordStatusRegistry` или эквивалентную status-модель
- закрепить allowed transitions:
  - `active`
  - `superseded`
  - `revoked`
  - `expired`
- отдельно описать technical states для off-chain слежения:
  - `accepted`
  - `included`
  - `finalized`
- решить, записываются ли technical states on-chain или остаются в indexer/audit слое

Definition of Done:

- статусная модель непротиворечива
- верификатор может отличить business status от finality status

### Этап 6. Ingress API и Canonicalization Service

Цель:

- стандартизовать входной поток до попадания данных в блокчейн

Задачи:

- реализовать `Ingress API` для single и batch режимов
- реализовать `Canonicalization Service`
- ввести версионирование canonicalization rules
- привязать canonicalization profile к `SchemaRegistry`
- формировать детерминированный hash и request metadata
- логировать trace id / request id для аудита

Definition of Done:

- одинаковые входные данные всегда дают одинаковый canonical form и hash
- API не отправляет транзакцию без валидных schema/policy/KYC условий

### Этап 7. Finality Watcher и Receipt Service

Цель:

- построить ключевой слой "заверения через consensus/finality"

Задачи:

- реализовать `Finality Watcher`
- отслеживать:
  - отправку транзакции
  - inclusion в блок
  - переход блока в `irreversible`
- реализовать `Receipt Service` для двух режимов:
  - single receipt
  - batch receipt
- в receipt включать:
  - hash/root
  - tx id
  - block num
  - finality flag
  - inclusion proof для batch

Definition of Done:

- receipt выдается только после подтвержденной finality
- для любой записи можно восстановить цепочку `request -> tx -> block -> irreversible`

### Этап 8. Indexer / Audit API

Цель:

- дать внешнему верификатору быстрый и проверяемый способ проверки записи

Задачи:

- реализовать индексатор событий и таблиц контрактов
- реализовать `Audit API`:
  - поиск по `commitment_id`
  - поиск по `external_ref`
  - получение receipt
  - проверка статуса
  - выдача chain of proof
- добавить аудит-эндпоинты для batch proof
- добавить pagination, filtering, exportable audit format

Definition of Done:

- внешний клиент может проверить существование записи и ее finality без доступа к исходным данным

### Этап 9. Security hardening

Цель:

- закрыть риски, перечисленные в ТЗ, до выхода в testnet/mainnet

Задачи:

- replay protection и идемпотентность запросов
- строгая canonicalization и schema enforcement
- снижение metadata leakage
- при необходимости добавить `salt`/HMAC слой до хеширования
- проверить permission boundaries и governance actions
- ограничить emergency pause только безопасными сценариями

Definition of Done:

- негативные сценарии покрыты тестами
- нет путей создать двусмысленный или недоверифицируемый receipt

### Этап 10. ProofRegistry и ZKP как отдельная очередь

Цель:

- не блокировать MVP optional-функциональностью

Задачи:

- реализовать `ProofRegistry` после стабилизации core-потока
- определить типы proof workers
- зафиксировать интерфейс `submitproof` / `verify`
- отдельно спроектировать public inputs, verification result и trust assumptions

Definition of Done:

- ZKP не влияет на core flow single/batch anchoring
- optional proof слой можно разворачивать независимо

### Этап 11. Интеграционное тестирование и rollout

Цель:

- проверить систему end-to-end до production rollout

Задачи:

- собрать test matrix:
  - unit tests контрактов
  - contract integration tests
  - API integration tests
  - finality watcher tests
  - batch/inclusion proof tests
- провести dry run на testnet
- проверить observability:
  - service logs
  - trace ids
  - alerting по stuck finality
- обновить runbooks деплоя и эксплуатации

Definition of Done:

- подтверждены single и batch потоки end-to-end
- команда умеет развернуть, проверить и поддерживать систему по runbook

## 5. Рекомендуемый порядок реализации по спринтам

Если делать без ZKP в первом релизе, последовательность лучше держать такой:

1. Discovery + ADR + backlog
2. Refactor core контракта
3. KYC + Schema + Policy
4. Commitment single flow
5. Batch flow
6. Canonicalization Service + Ingress API
7. Finality Watcher + Receipt Service
8. Indexer / Audit API
9. Security hardening
10. Testnet rollout
11. Production hardening
12. ProofRegistry / ZKP как отдельный релиз

## 6. Что можно переиспользовать из текущего репозитория

Можно использовать:

- текущую сборочную структуру `CMakeLists.txt`
- существующий контракт `verification` как точку входа для нового core
- текущие deploy/build scripts как основу для обновленных runbooks
- существующую практику таблиц, secondary indexes и `on_notify("*::transfer")` для платежного слоя

Нужно будет заменить или расширить:

- текущую таблицу `proofs`
- текущий action `record(...)`, потому что он не знает о schema/policy/finality lifecycle
- README и deploy docs, потому что они описывают более узкую модель

## 7. Основные риски проекта

- смешение business status и finality status
- попытка решить finality полностью on-chain
- отсутствие жесткой canonicalization версии
- слишком раннее добавление ZKP до стабилизации single/batch модели
- разрастание контракта без явной auth matrix
- хранение лишних доказательных данных on-chain вместо вынесения их в receipt/indexer слой

## 8. Практический итог

Оптимальная стратегия разработки:

- сначала стабилизировать on-chain data model
- затем собрать deterministic ingestion и finality pipeline
- после этого строить receipt/audit слой
- ZKP оставить отдельной дорожкой после MVP

Такой порядок минимизирует архитектурные развороты и позволяет рано получить рабочий `Proof of Existence + Hash/Batch Anchoring + Finality Verification` контур.
