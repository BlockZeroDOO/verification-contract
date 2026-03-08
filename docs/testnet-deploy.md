# Testnet Deploy

This contract targets GlobalForce testnet and accepts only `GFT` from `eosio.token`.

## Prerequisites

- deployed account for the contract, for example `gfnotary`
- `cleos`
- `cdt-cpp` or `eosio-cpp`
- contract account keys imported into the wallet

## Build

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

## Pricing

- retail: `1.0000 GFT`
- wholesale: `0.1000 GFT`

Applicable price is determined by membership in the `wholesale` table.

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

## Read tables

```powershell
cleos -u https://dev-history.globalforce.io get table gfnotary gfnotary wholesale
cleos -u https://dev-history.globalforce.io get table gfnotary gfnotary proofs
```

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
