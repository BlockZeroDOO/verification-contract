# Mainnet Deploy

This runbook prepares `gfnotary` for deployment to GlobalForce mainnet at `https://history.globalforce.io`.

## Mainnet assumptions

- contract account already exists on mainnet and has enough RAM for the `paytokens`, `wholesale`, `nonprofit`, `freepolicy`, `freeusage`, and `proofsv2` tables
- wallet keys for the deployment authority are imported into `cleos`
- you have decided in advance which payment token contract and symbol will be accepted on mainnet
- you understand that this contract needs ongoing admin access for:
  - `setpaytoken`
  - `setfreecfg`
  - `addwhuser` / `rmwhuser`
  - `addnporg` / `rmnporg`
  - `withdraw`

## Preflight checklist

- build the release artifacts and archive the generated SHA-256 files
- confirm the contract account name matches the deployed contract name and respects the 12-character account limit
- make sure the account has `eosio.code` on `active`, because `withdraw` sends an inline token transfer
- estimate RAM growth for `proofsv2`, because the contract pays RAM for stored proofs
- make sure the client always sends a non-empty `client_reference` for both paid and free proof creation
- decide the post-deploy governance model before publishing the account name

## Build release artifacts

Linux / WSL:

```bash
./scripts/build-release.sh
```

PowerShell:

```powershell
./scripts/build-release.ps1
```

Expected artifacts:

- `dist/gfnotary/gfnotary.wasm`
- `dist/gfnotary/gfnotary.abi`
- `dist/gfnotary/gfnotary.wasm.sha256`
- `dist/gfnotary/gfnotary.abi.sha256`

## Deploy to mainnet

```powershell
cleos -u https://history.globalforce.io set contract gfnotary ./dist/gfnotary -p gfnotary@active
```

## Add or preserve `eosio.code`

`withdraw` uses an inline `transfer`, so `active` must keep `eosio.code`.

```powershell
cleos -u https://history.globalforce.io set account permission gfnotary active --add-code -p gfnotary@active
```

## Configure accepted payment tokens

```powershell
cleos -u https://history.globalforce.io push action gfnotary setpaytoken '[
  "eosio.token",
  "1.0000 GFT",
  "0.1000 GFT",
  "0.0100 GFT"
]' -p gfnotary@active
```

## Configure free submission policy

For mainnet, do not leave `submitfree` unbounded. A conservative starting point looks like this:

```powershell
cleos -u https://history.globalforce.io push action gfnotary setfreecfg '[
  true,
  100
]' -p gfnotary@active
```

This means:

- max `100` free submissions across all nonprofit accounts in the current 24-hour UTC window
- a fixed `60` second cooldown between free submissions from the same nonprofit account

## Idempotent request protection

`client_reference` is required and acts as an idempotency key per submitter.

Recommended client rule:

- reuse the same `client_reference` only when retrying the same logical request
- generate a new `client_reference` for every intentionally new proof
- allow the same `object_hash` to be notarized multiple times
- keep `client_reference` in printable ASCII and never include `|`

## Verify on-chain state

```powershell
cleos -u https://history.globalforce.io get table gfnotary gfnotary paytokens
cleos -u https://history.globalforce.io get table gfnotary gfnotary wholesale
cleos -u https://history.globalforce.io get table gfnotary gfnotary nonprofit
cleos -u https://history.globalforce.io get table gfnotary gfnotary freepolicy
cleos -u https://history.globalforce.io get table gfnotary gfnotary freeusage
cleos -u https://history.globalforce.io get table gfnotary gfnotary proofsv2
```

## Governance recommendation

The GlobalForce account model supports both immutable and producer-controlled contracts. For this contract, full immutability needs extra care:

- inference from the contract design: burning both `owner` and `active` to `eosio.null` would also remove the ability to run future admin actions such as `setpaytoken`, `setfreecfg`, and `withdraw`
- safer mainnet posture: move `owner` to a multisig or producer-controlled authority, keep `active` operational with `eosio.code`, and optionally delegate daily operations to a linked custom permission such as `ops`
- if you eventually want to freeze upgrades, do it only after payment-token configuration, withdrawal process, and long-term governance are finalized

Relevant GlobalForce documentation:

- https://docs.globalforce.io/globalforce-context.md
- https://docs.globalforce.io/read-only-actions
