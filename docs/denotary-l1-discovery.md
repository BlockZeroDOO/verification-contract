# DeNotary L1 Discovery Pack

## Цель этапа 0

Этот документ фиксирует результат discovery по TSD v2 и служит входом для этапа 1.

Результат discovery:

- согласованная карта доменных сущностей
- границы on-chain и off-chain ответственности
- state machine для single и batch потоков
- auth matrix для actions и сервисов
- список архитектурных уточнений, которые нужно удержать до старта реализации

## Scope MVP

В MVP входят:

- `KYCRegistry`
- `SchemaRegistry`
- `PolicyRegistry`
- `CommitmentRegistry`
- `BatchRegistry`
- status model для business lifecycle
- `Ingress API`
- `Canonicalization Service`
- `Batch Builder`
- `Finality Watcher`
- `Receipt Service`
- `Indexer / Audit API`

Вне MVP:

- `ProofRegistry`
- ZKP verification
- расширенная governance automation
- интеграция `dfs` как обязательной части core-потока

Операционное допущение:

- контракт будет деплоиться на чистые аккаунты, поэтому legacy-миграция старых таблиц не входит в текущий scope

## Границы системы

### On-chain зона ответственности

On-chain слой отвечает за:

- хранение реестров допуска и правил
- хранение факта anchoring
- хранение business lifecycle записи
- хранение batch root и его метаданных
- проверяемый audit trail на уровне chain state

On-chain слой не должен отвечать за:

- canonicalization исходных документов
- построение Merkle tree
- отслеживание irreversible finality как единственного источника правды
- хранение больших manifest/inclusion proof данных
- выдачу пользовательских receipts

### Off-chain зона ответственности

Off-chain слой отвечает за:

- прием входных данных
- deterministic canonicalization
- hashing и request metadata
- построение batch manifest и Merkle root
- отслеживание inclusion/finality
- формирование verifiable receipt
- индексирование и audit API

## Bounded Contexts

### 1. Access & Governance

Сущности:

- `KYCRegistry`
- `SchemaRegistry`
- `PolicyRegistry`

Назначение:

- определить, кто может писать
- по какой схеме и в каком режиме можно писать
- какие режимы допускают batch/ZK и какой KYC нужен

### 2. Anchoring Core

Сущности:

- `CommitmentRegistry`
- `BatchRegistry`
- business status model

Назначение:

- фиксировать single и batch anchoring
- хранить связку submitter/schema/policy/hash/root
- обеспечивать последующую верификацию и audit trail

### 3. Deterministic Ingestion

Сервисы:

- `Ingress API`
- `Canonicalization Service`
- `Batch Builder`

Назначение:

- получать данные извне
- канонизировать их по версии схемы
- формировать hash и batch root без неоднозначности

### 4. Finality & Receipts

Сервисы:

- `Finality Watcher`
- `Receipt Service`

Назначение:

- отслеживать inclusion и irreversible
- связывать request/business object с chain event
- выдавать receipt только после finality

### 5. Audit & Verification

Сервисы:

- `Indexer`
- `Audit API`

Назначение:

- давать внешним клиентам read-only верификацию
- строить proof chain без доступа к исходным данным

## Entity Map

### KYCRegistry

| Поле | Тип | Где хранится | Примечание |
|---|---|---|---|
| `account` | `name` | on-chain | primary key |
| `level` | `uint8_t` | on-chain | уровень допуска |
| `provider` | `string` | on-chain | кто выдал KYC |
| `jurisdiction` | `string` | on-chain | нужна для policy rules |
| `active` | `bool` | on-chain | запись доступна для проверок |
| `issued_at` | `time_point` | on-chain | дата выдачи |
| `expires_at` | `time_point` | on-chain | дата истечения |

### SchemaRegistry

| Поле | Тип | Где хранится | Примечание |
|---|---|---|---|
| `id` | `uint64_t` | on-chain | primary key |
| `version` | `string` | on-chain | человекочитаемая версия |
| `canonicalization_hash` | `checksum256` | on-chain | hash canonicalization rules |
| `hash_policy` | `checksum256` | on-chain | hash hashing policy |
| `active` | `bool` | on-chain | схема доступна для новых записей |

### PolicyRegistry

| Поле | Тип | Где хранится | Примечание |
|---|---|---|---|
| `id` | `uint64_t` | on-chain | primary key |
| `allow_single` | `bool` | on-chain | разрешен single flow |
| `allow_batch` | `bool` | on-chain | разрешен batch flow |
| `require_kyc` | `bool` | on-chain | нужна проверка KYC |
| `min_kyc_level` | `uint8_t` | on-chain | минимальный KYC |
| `allow_zk` | `bool` | on-chain | optional capability flag |
| `active` | `bool` | on-chain | рекомендуется добавить в MVP |

### CommitmentRegistry

| Поле | Тип | Где хранится | Примечание |
|---|---|---|---|
| `id` | `uint64_t` | on-chain | primary key |
| `submitter` | `name` | on-chain | владелец записи |
| `schema_id` | `uint64_t` | on-chain | ссылка на схему |
| `policy_id` | `uint64_t` | on-chain | ссылка на policy |
| `hash` | `checksum256` | on-chain | anchor hash |
| `external_ref` | `checksum256` | on-chain | hash внешнего reference/idempotency ключа |
| `block_num` | `uint32_t` | on-chain | block number на момент submit |
| `created_at` | `time_point` | on-chain | время создания записи |
| `status` | `uint8_t` | on-chain | business status |

Рекомендуемые поля для MVP:

- secondary index по `submitter`
- secondary index по `schema_id`
- secondary index по `policy_id`
- secondary index по `status`
- явный idempotency key, если `external_ref` недостаточен по смыслу

### BatchRegistry

| Поле | Тип | Где хранится | Примечание |
|---|---|---|---|
| `id` | `uint64_t` | on-chain | primary key |
| `submitter` | `name` | on-chain | владелец batch |
| `root_hash` | `checksum256` | on-chain | Merkle root |
| `leaf_count` | `uint32_t` | on-chain | число leafs |
| `schema_id` | `uint64_t` | on-chain | схема batch |
| `policy_id` | `uint64_t` | on-chain | policy batch |
| `manifest_hash` | `checksum256` | on-chain | hash off-chain manifest |
| `block_num` | `uint32_t` | on-chain | block number на момент submit |
| `created_at` | `time_point` | on-chain | время создания batch |

Рекомендуемые поля для MVP:

- `status` для batch lifecycle
- индекс по `submitter`
- индекс по `schema_id`
- индекс по `policy_id`

### RecordStatus Model

| Статус | Код | Где хранится | Смысл |
|---|---|---|---|
| `active` | `0` | on-chain | действующая запись |
| `superseded` | `1` | on-chain | заменена новой версией |
| `revoked` | `2` | on-chain | отозвана governance/business rules |
| `expired` | `3` | on-chain | срок действия истек |

Важно:

- это business status
- finality state не должен смешиваться с этим полем

### ProofRegistry

| Поле | Тип | Где хранится | Примечание |
|---|---|---|---|
| `id` | `uint64_t` | on-chain | primary key |
| `type` | `uint64_t` | on-chain | тип доказательства |
| `public_inputs` | `checksum256` | on-chain | hash публичных входов |
| `result` | `checksum256` | on-chain | hash результата верификации |
| `verified` | `bool` | on-chain | статус верификации |

Статус для MVP:

- optional
- не блокирует single/batch anchoring

### Off-chain Request Model

| Сущность | Где хранится | Назначение |
|---|---|---|
| `ingress_request` | off-chain | входной запрос пользователя |
| `canonical_form` | off-chain | нормализованная форма данных |
| `request_hash` | off-chain | hash канонизированных данных |
| `batch_manifest` | off-chain | полный состав batch |
| `inclusion_proof` | off-chain | путь от leaf к root |
| `finality_event` | off-chain | связь tx/block/irreversible |
| `receipt` | off-chain | пользовательское доказательство |

## State Machine

### Single Record Technical Lifecycle

Этот lifecycle относится к request/transaction pipeline, а не к business status.

| Состояние | Где живет | Переход |
|---|---|---|
| `received` | off-chain | запрос принят API |
| `canonicalized` | off-chain | данные нормализованы |
| `hashed` | off-chain | hash вычислен |
| `submitted` | off-chain | транзакция отправлена |
| `included` | off-chain/indexer | транзакция вошла в блок |
| `finalized` | off-chain/indexer | блок стал irreversible |
| `receipted` | off-chain | receipt выдан пользователю |

### Single Record Business Lifecycle

| Состояние | Где живет | Кто меняет |
|---|---|---|
| `active` | on-chain | создание записи |
| `superseded` | on-chain | submitter или governance flow |
| `revoked` | on-chain | governance flow |
| `expired` | on-chain | governance/maintenance flow |

Нормы для реализации:

- `active -> superseded` разрешен
- `active -> revoked` разрешен
- `active -> expired` разрешен
- обратные переходы запрещены
- `superseded`, `revoked`, `expired` являются terminal state

### Batch Technical Lifecycle

| Состояние | Где живет | Переход |
|---|---|---|
| `collecting` | off-chain | batch builder собирает leafs |
| `rooted` | off-chain | Merkle root построен |
| `submitted` | off-chain | `submitroot` отправлен |
| `included` | off-chain/indexer | транзакция включена в блок |
| `finalized` | off-chain/indexer | batch root стал irreversible |
| `manifest_linked` | hybrid | `manifest_hash` связан с batch |
| `closed` | on-chain | batch закрыт для изменений |

Норма для MVP:

- после `finalized` содержимое batch не меняется
- `manifest_hash` должен ссылаться на immutable manifest

## Auth Matrix

Рекомендуемые actor roles:

- `governance`
- `kyc_admin`
- `schema_admin`
- `policy_admin`
- `submitter`
- `finality_service`
- `proof_service`

### On-chain actions

| Action | Кто авторизует | Комментарий |
|---|---|---|
| `issuekyc` | `kyc_admin` | выпуск KYC записи |
| `renewkyc` | `kyc_admin` | продление KYC |
| `revoke` | `kyc_admin` или `governance` | отзыв KYC |
| `suspend` | `kyc_admin` или `governance` | временная блокировка KYC |
| `addschema` | `schema_admin` | публикация новой схемы |
| `updateschema` | `schema_admin` | обновление правил |
| `deprecate` | `schema_admin` или `governance` | вывод схемы из новых submit |
| `setpolicy` | `policy_admin` | создание/изменение policy |
| `enablezk` | `policy_admin` | включение optional capability |
| `disablezk` | `policy_admin` | выключение optional capability |
| `submit` | `submitter` | single anchoring |
| `supersede` | `submitter` | замена своей записи |
| `setstatus` | не рекомендуется как generic action | лучше заменить на явные переходы |
| `linkproof` | `proof_service` или `governance` | optional proof layer |
| `submitroot` | `submitter` | batch anchoring |
| `closebatch` | `submitter` или `governance` | закрытие batch |
| `linkmanifest` | `submitter` или service account | связывание immutable manifest |
| `submitproof` | `proof_service` | optional |
| `verify` | `proof_service` | optional |

### Сервисные права

| Сервис | Нужен ли отдельный chain auth | Назначение |
|---|---|---|
| `Ingress API` | нет для MVP | готовит и отправляет tx от имени submitter |
| `Canonicalization Service` | нет | чисто off-chain логика |
| `Batch Builder` | нет | готовит root и manifest |
| `Finality Watcher` | нет для MVP | читает chain state и node API |
| `Receipt Service` | нет | выдает receipts на основе index data |
| `Indexer / Audit API` | нет | read-only consumer |

Рекомендация:

- для MVP не записывать finality обратно on-chain
- не вводить chain-side сервисный аккаунт для `markfinal`, пока нет жесткой причины

## Архитектурные уточнения, зафиксированные на этапе 0

### 1. `setstatus` как generic mutation слишком опасен

Рекомендуемое решение:

- заменить generic `setstatus(uint64_t id, uint8_t status)` на явные действия lifecycle
- пример: `supersede`, `revoke`, `expire`

Причина:

- generic action затрудняет auth model
- увеличивает риск недопустимых переходов
- хуже тестируется и хуже аудируется

### 2. Finality state не смешивается с business status

Рекомендуемое решение:

- `status` в реестре хранит только business state
- inclusion/finality живут в off-chain index/read model

Причина:

- irreversible finality зависит от наблюдения за сетью
- бизнес-статус и finality отвечают на разные вопросы

### 3. Batch proof material не хранится целиком on-chain

Рекомендуемое решение:

- on-chain хранит `root_hash`, `manifest_hash`, `leaf_count` и базовые ссылки
- manifest и inclusion proof живут off-chain

Причина:

- экономия RAM/CPU/NET
- соответствие принципу `batch-first`
- лучший контроль размера данных

### 4. Policy и schema должны быть version-aware

Рекомендуемое решение:

- не перезаписывать смысл существующей схемы задним числом
- новая версия должна читаться как новый набор правил или как новая версия с новым hash

### 5. Идемпотентность нужна в single и batch потоках

Рекомендуемое решение:

- на этапе 1 определить canonical idempotency key
- использовать его в API, индексаторе и on-chain модели

## Артефакты, которые должны появиться после этапа 0

- backlog с эпиками и user stories
- ADR по finality model
- ADR по batch proof storage
- тестовая матрица для MVP
- контрактный data model draft для этапа 1
