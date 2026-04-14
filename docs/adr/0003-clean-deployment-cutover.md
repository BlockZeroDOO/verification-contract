# ADR 0003: Clean Deployment Cutover

## Status

Accepted for MVP planning.

## Context

В текущем репозитории уже существует контракт `verification` со старой моделью:

- таблица `proofs`
- action `record(...)`
- paid submit path через `ontransfer`

Однако целевая модель DeNotary L1 MVP существенно шире и требует новые реестры:

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`

Есть два варианта:

1. проектировать миграцию старых таблиц и compatibility layer
2. деплоить целевой контракт на новые аккаунты как fresh deployment

Пользовательский контекст для этого проекта позволяет второй вариант.

## Decision

Для MVP принимается fresh deployment модель:

- контракт DeNotary L1 деплоится на чистый аккаунт
- миграция `proofs` в `commitments` не проектируется
- совместимость с legacy action `record(...)` не требуется
- таблицы и actions называются по целевой модели, а не по legacy shape

## Consequences

Плюсы:

- можно проектировать чистую domain model без compatibility baggage
- упрощается stage 1 и stage 2
- снижается риск сохранить неудачные формы legacy API только ради совместимости

Минусы:

- старые deploy/runbook документы нужно пересмотреть под новую модель
- legacy flows нельзя считать поддержанными автоматически

## Rejected alternatives

### Alternative 1. Миграция legacy proof rows

Отклонено, потому что:

- не нужна при fresh deployment
- создает лишнюю сложность до появления реального migration use case

### Alternative 2. Сохранять `record(...)` как compatibility action

Отклонено, потому что:

- legacy action не знает о `schema_id`, `policy_id`, KYC и batch model
- compatibility path будет искажать целевой API контракта
