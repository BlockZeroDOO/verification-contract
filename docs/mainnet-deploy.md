# Mainnet Deploy

> Legacy note: this guide still describes the old `managementel -> verification` flow.
> The current codebase accepts paid submissions directly in `verification`; use `README.md`
> and the updated scripts as the source of truth until this document is rewritten.

This runbook prepares the three-contract architecture for GlobalForce mainnet at
`https://history.globalforce.io`:

- `verification`: immutable proof registry
- `managementel`: pricing, nonprofit policy, role management, and treasury
- `dfs`: DFS registry, stake, pricing, and settlement layer

## Mainnet assumptions

- both contract accounts already exist on mainnet and have enough RAM
- wallet keys for the deployment authorities are imported into `cleos`
- you have decided which payment token contract and symbol will be accepted on mainnet
- you understand that `managementel` needs ongoing admin access for:
  - `setpaytoken`
  - `setfreecfg`
  - `addwhuser` / `rmwhuser`
  - `addnporg` / `rmnporg`
  - `withdraw`

## Preflight checklist

- build the release artifacts and archive the generated SHA-256 files
- confirm the account names match the deployed contract names and respect the 12-character account limit
- make sure `managementel` will keep `eosio.code` on `active`
- estimate RAM growth for `verification.proofs`, because `verification` pays RAM for stored proofs
- make sure the client always sends a non-empty `client_reference`
- decide the long-term governance model for both contracts before publishing account names

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
- `dist/managementel/managementel.wasm`
- `dist/managementel/managementel.abi`
- `dist/managementel/managementel.wasm.sha256`
- `dist/managementel/managementel.abi.sha256`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`
- `dist/dfs/dfs.wasm.sha256`
- `dist/dfs/dfs.abi.sha256`

## Deploy to mainnet

The live mainnet `history.globalforce.io` endpoint does not support `/v1/chain/send_transaction2`,
so the examples below use `--use-old-rpc --return-failure-trace false`.

Deploy `verification` first:

```powershell
cleos -u https://history.globalforce.io set contract --use-old-rpc --return-failure-trace false verification ./dist/verification -p verification@active
```

Then deploy `managementel`:

```powershell
cleos -u https://history.globalforce.io set contract --use-old-rpc --return-failure-trace false managementel ./dist/managementel -p managementel@active
```

## Add or preserve `eosio.code`

`managementel` sends inline `verification::record` and inline token `transfer` actions, so
`active` must keep `eosio.code`.

```powershell
cleos -u https://history.globalforce.io set account permission --use-old-rpc --return-failure-trace false managementel active --add-code -p managementel@active
```

`verification` does not require `eosio.code` for this design.

## Configure accepted payment tokens

```powershell
cleos -u https://history.globalforce.io push action --use-old-rpc --return-failure-trace false managementel setpaytoken '[
  "eosio.token",
  "1.0000 GFL",
  "0.1000 GFL"
]' -p managementel@active
```

`setpaytoken` validates the configured symbol precision against the token contract `stat` table,
so a mismatched precision is rejected during configuration.

## Configure free submission policy

For mainnet, do not leave `submitfree` unbounded. A conservative starting point:

```powershell
cleos -u https://history.globalforce.io push action --use-old-rpc --return-failure-trace false managementel setfreecfg '[
  true,
  100
]' -p managementel@active
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

## Verify on-chain state

```powershell
cleos -u https://history.globalforce.io get table managementel managementel paytokens
cleos -u https://history.globalforce.io get table managementel managementel wholesale
cleos -u https://history.globalforce.io get table managementel managementel nonprofit
cleos -u https://history.globalforce.io get table managementel managementel freepolicy
cleos -u https://history.globalforce.io get table managementel managementel freeusage
cleos -u https://history.globalforce.io get table verification verification proofs
```

## Governance recommendation

The split architecture lets you govern the contracts differently:

- `verification`: once stable, you can move toward an immutable or heavily governed posture because it only stores append-only proofs
- `managementel`: keep operational governance, because it owns pricing, free policy, whitelist management, and treasury
- safer mainnet posture: move `owner` to multisig or producer-controlled authority and keep `active` operational on `managementel` with `eosio.code`

Relevant GlobalForce documentation:

- https://docs.globalforce.io/globalforce-context.md
- https://docs.globalforce.io/read-only-actions
