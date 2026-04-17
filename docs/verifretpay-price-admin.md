# `verifretpay` Price Administration

This runbook explains how the contract administrator changes the retail `price_per_kib` tariff in `verifretpay`.

## Purpose

Use `setprice(...)` when you want to:

- create a retail tariff for single anchoring
- create a retail tariff for batch anchoring
- change the current `price_per_kib`
- reactivate an existing tariff by setting it again

## Preconditions

- `verifretpay` is already deployed
- the retail token is already configured in `rtltokens`
- you control `verifretpay@active`

If the token is not configured yet:

```bash
cleos -u <rpc> push action verifretpay settoken '["eosio.token","4,DNLT"]' -p verifretpay@active
```

## Action Shape

```text
setprice(mode, token_contract, price_per_kib)
```

Parameters:

- `mode`: `0` for single, `1` for batch
- `token_contract`: token contract account, for example `eosio.token`
- `price_per_kib`: exact tariff per `KiB`, for example `"0.0500 DNLT"`

Behavior:

- if the `(mode, token_contract, symbol)` tariff already exists, `verifretpay` updates it in place
- otherwise it creates a new tariff row

## Recommended Retail Tariffs

Current recommended live retail grid:

- `single` (`mode = 0`): `2.5000 DNLT / KiB`
- `batch` (`mode = 1`): `4.0000 DNLT / KiB`

At `1 DNLT = $0.01` this means:

- single request: about `$0.025`
- batch request: about `$0.040`

Recommended setup commands:

```bash
cleos -u <rpc> push action verifretpay settoken '["eosio.token","4,DNLT"]' -p verifretpay@active
cleos -u <rpc> push action verifretpay setprice '[0,"eosio.token","2.5000 DNLT"]' -p verifretpay@active
cleos -u <rpc> push action verifretpay setprice '[1,"eosio.token","4.0000 DNLT"]' -p verifretpay@active
```

## Set Single Price

Example: set single notarization tariff to `2.5000 DNLT` per `KiB`.

```bash
cleos -u <rpc> push action verifretpay setprice '[
  0,
  "eosio.token",
  "2.5000 DNLT"
]' -p verifretpay@active
```

## Set Batch Price

Example: set batch notarization tariff to `4.0000 DNLT` per `KiB`.

```bash
cleos -u <rpc> push action verifretpay setprice '[
  1,
  "eosio.token",
  "4.0000 DNLT"
]' -p verifretpay@active
```

## Change an Existing Price

Call `setprice` again with the same `mode` and token.

Example: change single price from `2.5000 DNLT` to `2.9000 DNLT`.

```bash
cleos -u <rpc> push action verifretpay setprice '[
  0,
  "eosio.token",
  "2.9000 DNLT"
]' -p verifretpay@active
```

## Verify

Read the tariff table:

```bash
cleos -u <rpc> get table verifretpay verifretpay rtltariffs
```

Things to check:

- `mode = 0` means single
- `mode = 1` means batch
- `token_contract` is correct
- `price_per_kib` is correct
- `active = true`

## Notes

- retail billing is exact: client payment must match computed `billable_kib * price_per_kib`
- if you change `price_per_kib`, all future client transfers must use the new exact amount
- `setprice` only works with an accepted token configured through `settoken`
