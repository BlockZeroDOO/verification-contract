# DFS Testnet Bootstrap

## Status

Bootstrap runbook for the first `dfs` testnet rollout.

This document is intentionally separate from the existing `verification` / `managementel`
deploy guides because `dfs` is a different contract family with different custody and governance
concerns.

## Purpose

Use this runbook to:

- deploy the `dfs` contract
- configure initial policy and accepted tokens
- register the first DFS nodes
- fund stake for those nodes
- publish initial storage price offers
- verify that the contract state is ready for metadata-side integration

## Current contract scope

The current `dfs` scaffold already includes:

- node registry
- stake state
- accepted token config
- price offers
- storage payment receipts
- settlements
- claimable balances
- pricing policy with explicit `settlement_authority`

This bootstrap does not yet assume:

- automatic slashing
- region-aware price weighting
- metadata-cluster integration

## Prerequisites

- deployed testnet account for `dfs`
- `cleos`
- `cdt-cpp` or `eosio-cpp`
- imported key for the `dfs` deployment authority
- imported keys for initial node owner accounts
- chosen testnet stake/payment token, expected to be a live Antelope symbol such as `EOS`
- a chosen settlement authority account

Recommended initial accounts:

- contract account: `dfs`
- settlement authority: dedicated metadata/governance account, not an end-user wallet
- node owners: one account per DFS node operator

## Build

Linux / WSL:

```bash
./scripts/build-testnet.sh
```

PowerShell:

```powershell
./scripts/build-testnet.ps1 -ContractName dfs
```

Expected artifacts:

- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## Deploy

```powershell
cleos -u https://history.denotary.io set contract dfs ./dist/dfs -p dfs@active
```

## Add `eosio.code`

`dfs` sends inline token transfers for:

- `withdrawstk`
- `claimrevenue`

So `dfs` must allow `eosio.code` on `active`.

```powershell
cleos -u https://history.denotary.io set account permission dfs active --add-code -p dfs@active
```

## Configure policy

Example baseline policy:

```powershell
cleos -u https://history.denotary.io push action dfs setpolicy '[
  "eosio.token",
  "100000.0000 EOS",
  "trimmedmed",
  "settleauth1",
  86400,
  3,
  0,
  604800
]' -p dfs@active
```

Parameter meaning:

- `stake_token_contract`: token contract used for node stake
- `stake_minimum`: minimum active stake per node
- `consensus_algorithm`: symbolic pricing-policy algorithm id
- `settlement_authority`: account allowed to submit `settle(...)`
- `max_price_age_sec`: price freshness budget
- `min_eligible_price_nodes`: minimum eligible offers before canonical pricing is valid
- `protocol_fee_bps`: protocol fee in basis points
- `unstake_cooldown_sec`: cooldown before stake withdrawal

Operational recommendation:

- do not use the same account for `dfs` and `settlement_authority`
- keep `protocol_fee_bps = 0` in the first rollout unless treasury accounting is already defined

## Configure accepted payment token

Example:

```powershell
cleos -u https://history.denotary.io push action dfs settoken '[
  "eosio.token",
  "4,EOS",
  true
]' -p dfs@active
```

This token must be accepted both for:

- storage payment receipts
- price offers

## Register initial nodes

Example metadata-capable node:

```powershell
cleos -u https://history.denotary.io push action dfs regnode '[
  "metadata-node-1",
  "nodeowner1111",
  "both",
  "eu-west",
  100,
  "https://metadata-node-1.example",
  "https://storage-node-1.example",
  "-----BEGIN PUBLIC KEY-----\nREPLACE_WITH_NODE_PUBLIC_KEY_PEM\n-----END PUBLIC KEY-----\n"
]' -p nodeowner1111@active
```

Validation notes:

- `metadata` or `both` roles require `metadata_endpoint`
- `storage` or `both` roles require `storage_endpoint`
- `node_public_key` can now be either:
  - an Antelope-style public key (`PUB_K1_`, `PUB_R1_`, `EOS`)
  - or a PEM `BEGIN/END PUBLIC KEY` block from the current storage-node runtime

## Fund stake

Stake is currently funded by token transfer with memo:

```text
stake|<node_id>
```

Example:

```powershell
cleos -u https://history.denotary.io push action eosio.token transfer '[
  "nodeowner1111",
  "dfs",
  "100000.0000 EOS",
  "stake|metadata-node-1"
]' -p nodeowner1111@active
```

Operational note:

- the node owner must fund its own node stake
- the funded symbol and token contract must match current policy

## Publish initial price offers

Example:

```powershell
cleos -u https://history.denotary.io push action dfs setprice '[
  "metadata-node-1",
  "eosio.token",
  "0.2500 EOS",
  "per_kib"
]' -p nodeowner1111@active
```

## Simulate a storage payment receipt

The current scaffold records a storage payment receipt when the incoming transfer memo is:

```text
storage|<payment_reference>|<manifest_hash>
```

Example:

```powershell
cleos -u https://history.denotary.io push action eosio.token transfer '[
  "retail.user",
  "dfs",
  "5.0000 EOS",
  "storage|quote-0001|manifest-sha256-example"
]' -p retail.user@active
```

This should create a `receipts` row with:

- `receipt_kind = storage`
- `payment_reference = quote-0001`
- `status = received`

## Submit a settlement

Example:

```powershell
cleos -u https://history.denotary.io push action dfs settle '[
  "settlement-0001",
  "file-0001",
  "quote-0001",
  "chain-tx-0001",
  "manifest-sha256-example",
  "eosio.token",
  "5.0000 EOS",
  "0.0000 EOS",
  [
    ["nodeowner1111", "2.5000 EOS"],
    ["nodeowner2222", "2.5000 EOS"]
  ]
]' -p settleauth1@active
```

Expected result:

- receipt moves from `received` to `settled`
- balances are created for each node owner
- the same `payment_reference` can no longer be settled again

## Claim revenue

Example:

```powershell
cleos -u https://history.denotary.io push action dfs claimrevenue '[
  "nodeowner1111",
  "eosio.token",
  "2.5000 EOS"
]' -p nodeowner1111@active
```

## Verify on-chain state

```powershell
cleos -u https://history.denotary.io get table dfs dfs pricepolicy
cleos -u https://history.denotary.io get table dfs dfs acpttokens
cleos -u https://history.denotary.io get table dfs dfs nodes
cleos -u https://history.denotary.io get table dfs dfs stakes
cleos -u https://history.denotary.io get table dfs dfs priceoffers
cleos -u https://history.denotary.io get table dfs dfs receipts
cleos -u https://history.denotary.io get table dfs dfs settlements
cleos -u https://history.denotary.io get table dfs dfs balances
```

## Resource notes

- node and price-offer rows are owner-funded
- stake rows are currently contract-funded because Antelope transfer notify handlers cannot increase another account's RAM usage
- `balances`, `receipts`, and `settlements` remain contract-funded in the current scaffold
- storage payment traffic can therefore still grow contract RAM through receipt retention
- before public rollout, define a retention/reconciliation policy for `receipts` and `settlements`

## Operator checklist before metadata integration

- policy exists
- accepted token exists and is enabled
- at least one `storage` or `both` node is registered
- each active node has stake at or above policy minimum
- each active storage-capable node has a price offer
- settlement authority is a dedicated operational account
- storage receipt flow and settlement flow were both exercised manually at least once
