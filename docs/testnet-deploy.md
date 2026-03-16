# Testnet Deploy

This contract targets GlobalForce testnet and accepts payment tokens configured in the `paytokens` table.

## Prerequisites

- deployed account for the contract, for example `verification`
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

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`

## Deploy

```powershell
cleos -u https://dev-history.globalforce.io set contract verification ./dist/verification -p verification@active
```

## Add `eosio.code`

`withdraw` sends an inline `eosio.token::transfer`, so the contract account must allow `eosio.code`.

```powershell
cleos -u https://dev-history.globalforce.io set account permission verification active --add-code -p verification@active
```

## Wholesale management

```powershell
cleos -u https://dev-history.globalforce.io push action verification addwhuser '["studio.partner","B2B partner"]' -p verification@active
cleos -u https://dev-history.globalforce.io push action verification rmwhuser '["studio.partner"]' -p verification@active
```

## Nonprofit management

```powershell
cleos -u https://dev-history.globalforce.io push action verification addnporg '["charity.acc","Non-commercial organization"]' -p verification@active
cleos -u https://dev-history.globalforce.io push action verification rmnporg '["charity.acc"]' -p verification@active
```

## Payment token configuration

```powershell
cleos -u https://dev-history.globalforce.io push action verification setpaytoken '[
  "eosio.token",
  "1.0000 GFT",
  "0.1000 GFT",
  "0.0100 GFT"
]' -p verification@active
```

`setpaytoken` validates the configured symbol precision against the token contract `stat` table.
If the token contract uses `4,GFT`, a config like `1.00000000 GFT` is rejected immediately.

## Free submission limits

`submitfree` is disabled until a free-submission policy is configured.

```powershell
cleos -u https://dev-history.globalforce.io push action verification setfreecfg '[
  true,
  100
]' -p verification@active
```

Parameters:

- `enabled`: enables or disables `submitfree`
- `daily_free_limit`: max free submissions across all nonprofit accounts during the current 24-hour UTC window

The nonprofit cooldown is fixed in the contract at 60 seconds per account.
This cooldown applies only to `submitfree`; paid retail and wholesale transfers are not rate-limited by time.

Remove a payment token:

```powershell
cleos -u https://dev-history.globalforce.io push action verification rmpaytoken '[
  "eosio.token",
  "4,GFT"
]' -p verification@active
```

Applicable price is determined by:

- membership in the `nonprofit` and `wholesale` tables
- the selected token configuration in `paytokens`
- `storage_price` is stored for external storage integration and does not affect the on-chain proof price

Note:

- `quote`, `iswhuser`, and `isnporg` are not exposed as callable ABI actions in the current build because CDT 4.1.1 dispatcher support is limited to `void` actions.

## Record creation by payment

Memo format:

```text
<64-char hex hash>|SHA-256|<canonicalization>|<client_reference required>
```

`client_reference` is the idempotency key for that submitter. Reusing the same `client_reference`
from the same account rejects the request and prevents duplicate charging. Reusing the same
`object_hash` with a new `client_reference` is allowed. `client_reference` must use printable
ASCII characters and cannot contain `|`. `canonicalization_profile` must be non-empty printable
ASCII up to 32 characters.

Retail example:

```powershell
cleos -u https://dev-history.globalforce.io push action eosio.token transfer '[
  "retail.user",
  "verification",
  "1.0000 GFT",
  "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user@active
```

Wholesale example:

```powershell
cleos -u https://dev-history.globalforce.io push action eosio.token transfer '[
  "studio.partner",
  "verification",
  "0.1000 GFT",
  "2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|batch-2026-0001"
]' -p studio.partner@active
```

Nonprofit example:

```powershell
cleos -u https://dev-history.globalforce.io push action verification submitfree '[
  "charity.acc",
  "3123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "SHA-256",
  "none",
  "charity-0001"
]' -p charity.acc@active
```

## Idempotent request protection

Proof creation is deduplicated by `submitter + client_reference`.

Rules:

- same `object_hash` with a new `client_reference` is allowed
- same `client_reference` for the same submitter is rejected
- same `client_reference` used by a different submitter is allowed

## Read tables

```powershell
cleos -u https://dev-history.globalforce.io get table verification verification paytokens
cleos -u https://dev-history.globalforce.io get table verification verification wholesale
cleos -u https://dev-history.globalforce.io get table verification verification nonprofit
cleos -u https://dev-history.globalforce.io get table verification verification freepolicy
cleos -u https://dev-history.globalforce.io get table verification verification freeusage
cleos -u https://dev-history.globalforce.io get table verification verification proofs
```

## Smoke test

Linux / WSL:

```bash
export OWNER_ACCOUNT=verification
export RETAIL_ACCOUNT=yourretailacc
export WHOLESALE_ACCOUNT=yourwholesale
export NONPROFIT_ACCOUNT=yournonprofit
export PAYMENT_TOKEN_CONTRACT=eosio.token
export PAYMENT_TOKEN_SYMBOL=4,GFT
export RETAIL_PRICE="1.0000 GFT"
export WHOLESALE_PRICE="0.1000 GFT"
export STORAGE_PRICE="0.0100 GFT"
export FREE_ENABLED=true
export FREE_DAILY_LIMIT=100
./scripts/smoke-test.sh
```

The script verifies:

- wholesale account can be added and removed
- payment token configuration can be created or updated, including `storage_price`
- free submission config can be applied before nonprofit usage
- nonprofit usage increments the global 24-hour sponsored counter in `freepolicy`
- the same `object_hash` can be submitted by different accounts with different `client_reference` values
- wholesale payment of `0.1000 GFT` creates a proof with `wholesale_pricing=true`
- retail payment of `1.0000 GFT` creates a proof with `wholesale_pricing=false`
- the same retail account can submit two paid proofs back-to-back without a cooldown delay
- invalid paid `client_reference` is rejected
- nonprofit account can be added and submit a free proof
- invalid nonprofit `client_reference` is rejected
- nonprofit cooldown rejects an immediate second `submitfree`
- lowering `daily_free_limit` to the current usage blocks new nonprofit submissions on the same UTC day
- `setfreecfg(false, ...)` disables free submissions immediately
- re-enabling `setfreecfg(true, ...)` on the same UTC day does not reset `used_in_window`
- duplicate `client_reference` for the same submitter is rejected
- total row count in `proofs` increases by 4

Requirements:

- `cleos`
- `jq`
- imported keys for `OWNER_ACCOUNT`, `RETAIL_ACCOUNT`, `WHOLESALE_ACCOUNT`, and `NONPROFIT_ACCOUNT`
- enough balance in the configured payment token on both payer accounts

## Withdraw collected payments

```powershell
cleos -u https://dev-history.globalforce.io push action verification withdraw '[
  "eosio.token",
  "owneraccount",
  "10.0000 GFT",
  "withdraw testnet revenue"
]' -p verification@active
```

`withdraw` is not gated by the `paytokens` table, so it can recover tokens already held by the
contract even after `rmpaytoken`.

## Resource note

The contract pays RAM for stored rows because `proofs.emplace` uses `get_self()` as payer in the `proofs` table.
CPU/NET for the incoming transfer transaction are still paid by the signing user unless you add
an external sponsorship layer.
