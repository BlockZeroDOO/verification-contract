# Verification Contracts for GlobalForce

This repository currently contains three Antelope-compatible smart contracts:

- `verification`: immutable proof registry
- `managementel`: pricing, access policy, nonprofit limits, and treasury
- `dfs`: work-in-progress DFS registry, stake, pricing, and settlement contract scaffold

The split keeps the proof ledger small and append-only while allowing pricing and operations
to evolve independently.

## Contract roles

### `verification`

`verification` stores only proof facts:

- `writer`
- `submitter`
- `object_hash`
- `canonicalization_profile`
- `client_reference`
- `submitted_at`

Only `managementel` is allowed to write proof rows. Clients calculate the hash locally, submit
through `managementel`, and then verify the stored row directly on-chain.

### `managementel`

`managementel` handles:

- payment token pricing in `paytokens`
- wholesale accounts in `wholesale`
- nonprofit accounts in `nonprofit`
- nonprofit free-submission policy in `freepolicy`
- nonprofit cooldown tracking in `freeusage`
- paid submissions via `*::transfer`
- free submissions via `submitfree`
- treasury withdrawals

Commercial history is intentionally not stored on-chain. File storage is fully decoupled from
these contracts, and `storage_price` is no longer part of `paytokens`.

### `dfs`

`dfs` is the early scaffold for the separate DFS economic and trust layer:

- node registry
- stake policy and stake custody
- storage price offers
- accepted token configuration
- revenue balances and settlements

It is intentionally separate from `managementel` and `verification`, because DFS storage must
not depend on the HASH/notary contracts for payment custody or node-trust decisions.

The current hardening and security backlog for `dfs` is tracked in
`docs/dfs-hardening-plan.md`.

Bootstrap and validation guides for `dfs`:

- `docs/dfs-testnet-bootstrap.md`
- `docs/dfs-test-matrix.md`

## Tables

### `verification`

- `proofs`: append-only proof records with `writer`, `submitter`, compact `checksum256 object_hash`,
  `canonicalization_profile`, `client_reference`, and `submitted_at`

### `managementel`

- `paytokens`: accepted payment tokens with `token_contract`, `retail_price`, and `wholesale_price`
- `wholesale`: accounts eligible for wholesale pricing
- `nonprofit`: accounts allowed to use `submitfree`
- `freepolicy`: singleton with `enabled`, `daily_free_limit`, `used_in_window`, and current UTC window start
- `freeusage`: last nonprofit submission timestamp per account for the fixed 60-second cooldown

## Actions

### `verification`

- `record(name submitter, checksum256 object_hash, string canonicalization_profile, string client_reference)`

### `managementel`

- `addwhuser(name account, string note)`
- `rmwhuser(name account)`
- `addnporg(name account, string note)`
- `rmnporg(name account)`
- `setpaytoken(name token_contract, asset retail_price, asset wholesale_price)`
- `rmpaytoken(name token_contract, symbol token_symbol)`
- `submitfree(name submitter, string object_hash, string hash_algorithm, string canonicalization_profile, string client_reference)`
- `setfreecfg(bool enabled, uint32_t daily_free_limit)`
- `withdraw(name token_contract, name to, asset quantity, string memo)`

Internal helpers such as `quote(...)`, `iswhuser(...)`, and `isnporg(...)` remain C++ helpers only.

## Request model

Paid memo format:

```text
<64-char hex hash>|SHA-256|<canonicalization>|<client_reference>
```

Rules:

- `client_reference` is required and acts as the idempotency key per `submitter`
- the same `object_hash` may be submitted multiple times if `client_reference` is new
- `canonicalization_profile` must be non-empty printable ASCII up to 32 characters
- `client_reference` must be printable ASCII, max 128 chars, and cannot contain `|`
- only `SHA-256` is currently accepted

## Example flow

```bash
cleos push action managementel setpaytoken '["eosio.token", "1.0000 GFT", "0.1000 GFT"]' -p managementel
cleos push action managementel setfreecfg '[true, 100]' -p managementel
cleos push action managementel addwhuser '["studio.partner", "B2B wholesale client"]' -p managementel
cleos push action managementel addnporg '["charity.acc", "nonprofit organization"]' -p managementel

cleos push action eosio.token transfer '[
  "retail.user",
  "managementel",
  "1.0000 GFT",
  "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user

cleos push action eosio.token transfer '[
  "studio.partner",
  "managementel",
  "0.1000 GFT",
  "2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|batch-2026-0001"
]' -p studio.partner

cleos push action managementel submitfree '[
  "charity.acc",
  "3123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "SHA-256",
  "none",
  "charity-0001"
]' -p charity.acc

cleos get table verification verification proofs
```

## Notes

- `verification` is the proof source of truth; `managementel` is the policy and treasury layer.
- `verification.writer` makes the writing path explicit on-chain and should always show `managementel`.
- `setpaytoken` validates the configured symbol precision against the token contract `stat` table.
- nonprofit submissions are limited to one submission every 60 seconds per account and share one contract-wide 24-hour limit.
- the 60-second cooldown applies only to nonprofit accounts using `submitfree`; paid retail and wholesale transfers are not rate-limited by time.
- `verification` pays RAM for stored proof rows.
- `managementel` can withdraw tokens already held by the contract even if the corresponding `paytokens` row was later removed.

## Build and deploy

- Testnet build scripts: `scripts/build-testnet.sh`, `scripts/build-testnet.ps1`
- Release build scripts: `scripts/build-release.sh`, `scripts/build-release.ps1`
- Smoke test: `scripts/smoke-test.sh`
- Testnet guide: `docs/testnet-deploy.md`
- Mainnet guide: `docs/mainnet-deploy.md`

## Desktop App

- Windows environment check: `scripts/check-tauri-windows-env.ps1`
- Windows setup guide: `docs/tauri-windows-setup.md`

## License

This project is licensed under the MIT License. See the `LICENSE` file.
