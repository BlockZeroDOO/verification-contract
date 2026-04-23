# `verifbill` Plan Purchase

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

This runbook explains how an enterprise client buys a tariff plan in `verifbill`.

## Purpose

A client buys a plan by sending an exact token transfer to `verifbill`.

That purchase creates an `entitlement` in `verifbill`, which later allows atomic enterprise anchoring through:

- `verifbill::submit(...)`
- `verifbill::submitroot(...)`

## Preconditions

- the plan already exists and is active
- the billing token is accepted by `verifbill`
- the client controls the payer account and has enough balance

## How Purchase Works

The client sends:

- `to = verifbill`
- exact plan price
- memo format:

```text
plan|payer|plan_code
```

Example:

- `payer = acmeclient`
- `plan_code = starter`

Memo:

```text
plan|acmeclient|starter
```

Important rules:

- transfer sender must equal `payer` in the memo
- quantity must match the configured plan price exactly
- token contract must match the configured plan token

## Verify the Plan Before Purchase

Read available plans:

```bash
cleos -u <rpc> get table verifbill verifbill plans
```

Find:

- `plan_code`
- `price`
- `token_contract`
- `active = true`

## Buy the Plan

Example: buy the `starter` plan for account `acmeclient` at `25.0000 DNLT`.

```bash
cleos -u <rpc> push action eosio.token transfer '[
  "acmeclient",
  "verifbill",
  "25.0000 DNLT",
  "plan|acmeclient|starter"
]' -p acmeclient@active
```

## Verify the Purchase

Read entitlements:

```bash
cleos -u <rpc> get table verifbill verifbill entitlements
```

Things to check:

- a new row exists for `payer = acmeclient`
- `kind` is the plan kind
- `kib_remaining` matches the plan quota
- `status` is active
- `expires_at` is set from the plan duration

## What Happens Next

After the plan is purchased, the same payer can use `verifbill` for atomic enterprise anchoring.

Single:

```bash
cleos -u <rpc> push action verifbill submit '[
  "acmeclient",
  "acmeclient",
  <schema_id>,
  <policy_id>,
  "<object_hash>",
  "<external_ref>"
]' -p acmeclient@active
```

Batch:

```bash
cleos -u <rpc> push action verifbill submitroot '[
  "acmeclient",
  "acmeclient",
  <schema_id>,
  <policy_id>,
  "<root_hash>",
  <leaf_count>,
  "<manifest_hash>",
  "<external_ref>"
]' -p acmeclient@active
```

`verifbill` computes the canonical registry request size itself and subtracts the required `KiB` from the payer entitlement after successful inline anchoring into `verif`.

## Notes

- current supported enterprise runtime requires `payer == submitter`
- a plan purchase creates a time-limited entitlement
- if you need a non-expiring quota bucket instead, buy a `pack` instead of a `plan`
