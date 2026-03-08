# Testnet Deploy

This contract targets GlobalForce testnet and accepts only `GFT` from `eosio.token`.

## Prerequisites

- deployed account for the contract, for example `gfnotary`
- `cleos`
- `cdt-cpp` or `eosio-cpp`
- contract account keys imported into the wallet

## Build

Linux / WSL:

```bash
./scripts/build-testnet.sh
```

PowerShell:

```powershell
./scripts/build-testnet.ps1
```

Expected artifacts:

- `dist/gfnotary/gfnotary.wasm`
- `dist/gfnotary/gfnotary.abi`

## Deploy

```powershell
cleos -u https://dev-history.globalforce.io set contract gfnotary ./dist/gfnotary -p gfnotary@active
```

## Add `eosio.code`

`withdraw` sends an inline `eosio.token::transfer`, so the contract account must allow `eosio.code`.

```powershell
cleos -u https://dev-history.globalforce.io set account permission gfnotary active --add-code -p gfnotary@active
```

## Wholesale management

```powershell
cleos -u https://dev-history.globalforce.io push action gfnotary addwhuser '["studio.partner","B2B partner"]' -p gfnotary@active
cleos -u https://dev-history.globalforce.io push action gfnotary rmwhuser '["studio.partner"]' -p gfnotary@active
```

## Nonprofit management

```powershell
cleos -u https://dev-history.globalforce.io push action gfnotary addnporg '["charity.acc","Non-commercial organization"]' -p gfnotary@active
cleos -u https://dev-history.globalforce.io push action gfnotary rmnporg '["charity.acc"]' -p gfnotary@active
```

## Pricing

- retail: `1.0000 GFT`
- wholesale: `0.1000 GFT`
- nonprofit: `0.0000 GFT`

Applicable price is determined by membership in the `nonprofit` and `wholesale` tables.

## Record creation by payment

Memo format:

```text
<64-char hex hash>|SHA-256|<canonicalization>|<client_reference optional>
```

Retail example:

```powershell
cleos -u https://dev-history.globalforce.io push action eosio.token transfer '[
  "retail.user",
  "gfnotary",
  "1.0000 GFT",
  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user@active
```

Wholesale example:

```powershell
cleos -u https://dev-history.globalforce.io push action eosio.token transfer '[
  "studio.partner",
  "gfnotary",
  "0.1000 GFT",
  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|batch-2026-0001"
]' -p studio.partner@active
```

Nonprofit example:

```powershell
cleos -u https://dev-history.globalforce.io push action gfnotary submitfree '[
  "charity.acc",
  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "SHA-256",
  "none",
  "charity-0001"
]' -p charity.acc@active
```

## Read tables

```powershell
cleos -u https://dev-history.globalforce.io get table gfnotary gfnotary wholesale
cleos -u https://dev-history.globalforce.io get table gfnotary gfnotary nonprofit
cleos -u https://dev-history.globalforce.io get table gfnotary gfnotary proofs
```

## Smoke test

Linux / WSL:

```bash
export OWNER_ACCOUNT=globalnotary
export RETAIL_ACCOUNT=yourretailacc
export WHOLESALE_ACCOUNT=yourwholesale
export NONPROFIT_ACCOUNT=yournonprofit
./scripts/smoke-test.sh
```

The script verifies:

- wholesale account can be added and removed
- wholesale payment of `0.1000 GFT` creates a proof with `wholesale_pricing=true`
- retail payment of `1.0000 GFT` creates a proof with `wholesale_pricing=false`
- nonprofit account can be added and submit a free proof
- total row count in `proofs` increases by 3

Requirements:

- `cleos`
- `jq`
- imported keys for `OWNER_ACCOUNT`, `RETAIL_ACCOUNT`, `WHOLESALE_ACCOUNT`, and `NONPROFIT_ACCOUNT`
- enough `GFT` balance on both payer accounts

## Withdraw collected payments

```powershell
cleos -u https://dev-history.globalforce.io push action gfnotary withdraw '[
  "owneraccount",
  "10.0000 GFT",
  "withdraw testnet revenue"
]' -p gfnotary@active
```

## Resource note

The contract pays RAM for stored rows because `proofs.emplace` uses `get_self()` as payer.
CPU/NET for the incoming transfer transaction are still paid by the signing user unless you add
an external sponsorship layer.
