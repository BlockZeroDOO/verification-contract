# Testnet Deploy

This repository deploys three contracts:

- `verification`: append-only proof registry
- `managementel`: pricing, nonprofit policy, role management, and treasury
- `dfs`: DFS registry, stake, pricing, and settlement layer

All user traffic goes through `managementel`. Proof rows are then written into `verification`.

## Prerequisites

- deployed testnet accounts `verification` and `managementel`
- `cleos`
- `cdt-cpp` or `eosio-cpp`
- imported keys for both contract accounts and test users

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
- `dist/managementel/managementel.wasm`
- `dist/managementel/managementel.abi`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## Deploy

Deploy `verification` first:

```powershell
cleos -u https://dev-history.globalforce.io set contract verification ./dist/verification -p verification@active
```

Then deploy `managementel`:

```powershell
cleos -u https://dev-history.globalforce.io set contract managementel ./dist/managementel -p managementel@active
```

## Add `eosio.code`

`managementel` sends inline actions to `verification` and inline token transfers during `withdraw`,
so it must allow `eosio.code` on `active`.

```powershell
cleos -u https://dev-history.globalforce.io set account permission managementel active --add-code -p managementel@active
```

`verification` does not need `eosio.code` for this design.

## Wholesale and nonprofit management

```powershell
cleos -u https://dev-history.globalforce.io push action managementel addwhuser '["studio.partner","B2B partner"]' -p managementel@active
cleos -u https://dev-history.globalforce.io push action managementel rmwhuser '["studio.partner"]' -p managementel@active
cleos -u https://dev-history.globalforce.io push action managementel addnporg '["charity.acc","Non-commercial organization"]' -p managementel@active
cleos -u https://dev-history.globalforce.io push action managementel rmnporg '["charity.acc"]' -p managementel@active
```

## Payment token configuration

```powershell
cleos -u https://dev-history.globalforce.io push action managementel setpaytoken '[
  "eosio.token",
  "1.0000 GFT",
  "0.1000 GFT"
]' -p managementel@active
```

`setpaytoken` validates the configured symbol precision against the token contract `stat` table.
If the token contract uses `4,GFT`, a config like `1.00000000 GFT` is rejected immediately.

Remove a payment token:

```powershell
cleos -u https://dev-history.globalforce.io push action managementel rmpaytoken '[
  "eosio.token",
  "4,GFT"
]' -p managementel@active
```

## Free submission limits

`submitfree` is disabled until a free-submission policy is configured.

```powershell
cleos -u https://dev-history.globalforce.io push action managementel setfreecfg '[
  true,
  100
]' -p managementel@active
```

Parameters:

- `enabled`: enables or disables `submitfree`
- `daily_free_limit`: max free submissions across all nonprofit accounts during the current 24-hour UTC window

The nonprofit cooldown is fixed at 60 seconds per account.
This cooldown applies only to `submitfree`; paid retail and wholesale transfers are not rate-limited by time.

## Record creation by payment

Paid memo format:

```text
<64-char hex hash>|SHA-256|<canonicalization>|<client_reference>
```

`client_reference` is the idempotency key per submitter. Reusing the same `client_reference`
from the same account is rejected. Reusing the same `object_hash` with a new `client_reference`
is allowed. `client_reference` must use printable ASCII and cannot contain `|`.
`canonicalization_profile` must be non-empty printable ASCII up to 32 characters.

Retail example:

```powershell
cleos -u https://dev-history.globalforce.io push action eosio.token transfer '[
  "retail.user",
  "managementel",
  "1.0000 GFT",
  "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user@active
```

Wholesale example:

```powershell
cleos -u https://dev-history.globalforce.io push action eosio.token transfer '[
  "studio.partner",
  "managementel",
  "0.1000 GFT",
  "2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|batch-2026-0001"
]' -p studio.partner@active
```

Nonprofit example:

```powershell
cleos -u https://dev-history.globalforce.io push action managementel submitfree '[
  "charity.acc",
  "3123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "SHA-256",
  "none",
  "charity-0001"
]' -p charity.acc@active
```

## Read tables

```powershell
cleos -u https://dev-history.globalforce.io get table managementel managementel paytokens
cleos -u https://dev-history.globalforce.io get table managementel managementel wholesale
cleos -u https://dev-history.globalforce.io get table managementel managementel nonprofit
cleos -u https://dev-history.globalforce.io get table managementel managementel freepolicy
cleos -u https://dev-history.globalforce.io get table managementel managementel freeusage
cleos -u https://dev-history.globalforce.io get table verification verification proofs
```

`verification.proofs` should show:

- `writer = managementel`
- `submitter = end-user account`
- the client-calculated `object_hash`
- the submitted `canonicalization_profile`
- the submitted `client_reference`

## Smoke test

Linux / WSL:

```bash
export OWNER_ACCOUNT=managementel
export MANAGEMENT_ACCOUNT=managementel
export VERIFICATION_ACCOUNT=verification
export RETAIL_ACCOUNT=yourretailacc
export WHOLESALE_ACCOUNT=yourwholesale
export NONPROFIT_ACCOUNT=yournonprofit
export PAYMENT_TOKEN_CONTRACT=eosio.token
export RETAIL_PRICE="1.0000 GFT"
export WHOLESALE_PRICE="0.1000 GFT"
export FREE_ENABLED=true
export FREE_DAILY_LIMIT=100
./scripts/smoke-test.sh
```

The script verifies:

- `managementel` pricing config can be created and updated
- token precision mismatches are rejected by `setpaytoken`
- wholesale and nonprofit role management works
- wholesale and retail paid flows create rows in `verification.proofs`
- the same retail account can submit two paid proofs back-to-back without a cooldown delay
- nonprofit free flow creates rows in `verification.proofs`
- nonprofit cooldown and daily limit are enforced
- disabling and re-enabling free submissions keeps same-day usage intact
- duplicate `client_reference` for the same submitter is rejected
- every created proof row shows `writer = managementel`

## Withdraw collected payments

```powershell
cleos -u https://dev-history.globalforce.io push action managementel withdraw '[
  "eosio.token",
  "owneraccount",
  "10.0000 GFT",
  "withdraw testnet revenue"
]' -p managementel@active
```

`withdraw` is not gated by the `paytokens` table, so it can recover tokens already held by
`managementel` even after `rmpaytoken`.

## Resource note

`verification` pays RAM for stored proof rows because `proofs.emplace` uses `get_self()` as payer.
CPU/NET for incoming user-signed transactions are still paid by the signer unless you add an
external sponsorship layer.
