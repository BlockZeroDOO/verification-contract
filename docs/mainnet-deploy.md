# Mainnet Deploy

This runbook prepares `verification` for deployment to GlobalForce mainnet at `https://history.globalforce.io`.

## Mainnet assumptions

- contract account already exists on mainnet and has enough RAM for the `paytokens`, `wholesale`, `nonprofit`, `freepolicy`, `freeusage`, and `proofs` tables
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
- estimate RAM growth for `proofs`, because the contract pays RAM for stored proofs
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

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`
- `dist/verification/verification.wasm.sha256`
- `dist/verification/verification.abi.sha256`

## Deploy to mainnet

```powershell
cleos -u https://history.globalforce.io set contract verification ./dist/verification -p verification@active
```

## Add or preserve `eosio.code`

`withdraw` uses an inline `transfer`, so `active` must keep `eosio.code`.

```powershell
cleos -u https://history.globalforce.io set account permission verification active --add-code -p verification@active
```

## Configure accepted payment tokens

```powershell
cleos -u https://history.globalforce.io push action verification setpaytoken '[
  "eosio.token",
  "1.0000 GFT",
  "0.1000 GFT",
  "0.0100 GFT"
]' -p verification@active
```

`storage_price` is stored for external storage integration and does not change the on-chain proof
price used by paid proof creation. `setpaytoken` also validates the configured symbol precision
against the token contract `stat` table, so a mismatched precision is rejected at configuration time.

## Configure free submission policy

For mainnet, do not leave `submitfree` unbounded. A conservative starting point looks like this:

```powershell
cleos -u https://history.globalforce.io push action verification setfreecfg '[
  true,
  100
]' -p verification@active
```

This means:

- max `100` free submissions across all nonprofit accounts in the current 24-hour UTC window
- a fixed `60` second cooldown between free submissions from the same nonprofit account

The 60-second cooldown applies only to `submitfree`; paid retail and wholesale transfers are not rate-limited by time.

## Idempotent request protection

`client_reference` is required and acts as an idempotency key per submitter.

Recommended client rule:

- reuse the same `client_reference` only when retrying the same logical request
- generate a new `client_reference` for every intentionally new proof
- allow the same `object_hash` to be notarized multiple times
- keep `client_reference` in printable ASCII and never include `|`
- keep `canonicalization_profile` in non-empty printable ASCII up to 32 characters

## Withdraw operations

`withdraw` is not tied to the presence of a `paytokens` config entry. If the contract account still
holds a token balance, the operator can withdraw it even after `rmpaytoken`.

## Verify on-chain state

```powershell
cleos -u https://history.globalforce.io get table verification verification paytokens
cleos -u https://history.globalforce.io get table verification verification wholesale
cleos -u https://history.globalforce.io get table verification verification nonprofit
cleos -u https://history.globalforce.io get table verification verification freepolicy
cleos -u https://history.globalforce.io get table verification verification freeusage
cleos -u https://history.globalforce.io get table verification verification proofs
```

## Governance recommendation

The GlobalForce account model supports both immutable and producer-controlled contracts. For this contract, full immutability needs extra care:

- inference from the contract design: burning both `owner` and `active` to `eosio.null` would also remove the ability to run future admin actions such as `setpaytoken`, `setfreecfg`, and `withdraw`
- safer mainnet posture: move `owner` to a multisig or producer-controlled authority, keep `active` operational with `eosio.code`, and optionally delegate daily operations to a linked custom permission such as `ops`
- if you eventually want to freeze upgrades, do it only after payment-token configuration, withdrawal process, and long-term governance are finalized

Relevant GlobalForce documentation:

- https://docs.globalforce.io/globalforce-context.md
- https://docs.globalforce.io/read-only-actions
