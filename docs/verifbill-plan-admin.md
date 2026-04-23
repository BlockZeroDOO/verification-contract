# `verifbill` Plan Administration

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

This runbook explains how the contract administrator creates or updates an enterprise tariff plan in `verifbill`.

## Purpose

Use `setplan(...)` when you want to:

- create a new enterprise subscription plan
- update the price of an existing plan
- update included `KiB`
- update duration
- reactivate a plan by setting `active = true`

Use `deactplan(plan_id)` when you want to disable an existing plan without deleting historical entitlements.

## Preconditions

- `verifbill` is already deployed
- the billing token is already configured in `billtokens`
- you control `verifbill@active`

If the billing token is not configured yet:

```bash
cleos -u <rpc> push action verifbill settoken '["eosio.token","4,DNLT"]' -p verifbill@active
```

## Action Shape

```text
setplan(plan_code, token_contract, price, duration_sec, included_kib, active)
```

Parameters:

- `plan_code`: Antelope `name`, up to 12 chars, for example `starter`, `business`, `annual`
- `token_contract`: token contract account, for example `eosio.token`
- `price`: exact purchase price, for example `"25.0000 DNLT"`
- `duration_sec`: duration in seconds, for example `2592000` for 30 days
- `included_kib`: positive `KiB` quota included in the plan
- `active`: `true` or `false`

Behavior:

- if `plan_code` does not exist, `verifbill` creates a new plan row
- if `plan_code` already exists, `verifbill` updates that plan in place

## Create a New Plan

Example: create a 30-day plan with `50000 KiB` for `25.0000 DNLT`.

```bash
cleos -u <rpc> push action verifbill setplan '[
  "starter",
  "eosio.token",
  "25.0000 DNLT",
  2592000,
  50000,
  true
]' -p verifbill@active
```

## Update an Existing Plan

Call the same `setplan` action again with the same `plan_code`.

Example: change the price to `29.0000 DNLT` and increase quota to `60000 KiB`.

```bash
cleos -u <rpc> push action verifbill setplan '[
  "starter",
  "eosio.token",
  "29.0000 DNLT",
  2592000,
  60000,
  true
]' -p verifbill@active
```

## Disable a Plan

First find the numeric `plan_id`:

```bash
cleos -u <rpc> get table verifbill verifbill plans
```

Then deactivate it:

```bash
cleos -u <rpc> push action verifbill deactplan '[123]' -p verifbill@active
```

## Verify

Read the plans table:

```bash
cleos -u <rpc> get table verifbill verifbill plans
```

Things to check:

- `plan_code` is correct
- `token_contract` is correct
- `price` is correct
- `duration_sec` is correct
- `included_kib` is correct
- `active` is correct

## Notes

- `plan_code` must be a valid Antelope `name`
- `price` must use a configured and accepted billing token
- `duration_sec` must be greater than zero
- `included_kib` must be greater than zero
- `setplan` is idempotent by `plan_code`, not by `plan_id`
