# Verification Contracts for DeNotary.io

This repository currently contains two Antelope-compatible smart contracts:

- `verification`: immutable proof registry with built-in payment handling
- `dfs`: work-in-progress DFS registry, stake, pricing, and settlement contract scaffold

`managementel` has been removed. Clients now send paid proof submissions directly to
`verification`.

## Contract roles

### `verification`

`verification` now handles both payment configuration and proof storage:

- accepted payment tokens in `paytokens`
- paid proof submissions via `*::transfer`
- treasury withdrawals
- immutable proof records in `proofs`

Each proof row stores:

- `writer`
- `submitter`
- `object_hash`
- `canonicalization_profile`
- `client_reference`
- `submitted_at`

The `writer` is now always the `verification` contract account itself.

### `dfs`

`dfs` remains a separate scaffold for the DFS economic and trust layer:

- node registry
- stake policy and stake custody
- storage price offers
- accepted token configuration
- revenue balances and settlements

The current hardening and security backlog for `dfs` is tracked in
`docs/dfs-hardening-plan.md`.

## Tables

### `verification`

- `proofs`: append-only proof records with `writer`, `submitter`, compact `checksum256 object_hash`,
  `canonicalization_profile`, `client_reference`, and `submitted_at`
- `paytokens`: accepted payment tokens with `token_contract` and a single fixed `price`

## Actions

### `verification`

- `record(name submitter, checksum256 object_hash, string canonicalization_profile, string client_reference)`
- `setpaytoken(name token_contract, asset price)`
- `rmpaytoken(name token_contract, symbol token_symbol)`
- `withdraw(name token_contract, name to, asset quantity, string memo)`

`record(...)` is intended for contract-internal writes. External clients should submit by sending a
token transfer directly to `verification`.

## Request model

Paid memo format:

```text
<64-char hex hash>|SHA-256|<canonicalization>|<client_reference>
```

Rules:

- every submission is paid; there are no wholesale or free flows
- `client_reference` is required and acts as the idempotency key per `submitter`
- the same `object_hash` may be submitted multiple times if `client_reference` is new
- `canonicalization_profile` must be non-empty printable ASCII up to 32 characters
- `client_reference` must be printable ASCII, max 128 chars, and cannot contain `|`
- only `SHA-256` is currently accepted
- transferred quantity must exactly match the configured fixed price for that token

## Example flow

```bash
cleos push action verification setpaytoken '["eosio.token", "1.0000 GFT"]' -p verification

cleos push action eosio.token transfer '[
  "retail.user",
  "verification",
  "1.0000 GFT",
  "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user

cleos get table verification verification proofs
cleos get table verification verification paytokens
```

## Notes

- `verification` is now both the proof source of truth and the pricing/treasury layer.
- `setpaytoken` validates the configured symbol precision against the token contract `stat` table.
- `verification` pays RAM for stored proof rows.
- `withdraw` transfers funds already held by `verification`.
- `verification` needs `eosio.code` on `active` if you want contract-triggered withdrawals to work.

## Build and deploy

- Testnet build scripts: `scripts/build-testnet.sh`, `scripts/build-testnet.ps1`
- Release build scripts: `scripts/build-release.sh`, `scripts/build-release.ps1`
- Linux bootstrap: `scripts/bootstrap-linux-antelope.sh`
- Jungle4 deploy script: `scripts/deploy-jungle4.sh`
- Jungle4 smoke test wrapper: `scripts/smoke-test-jungle4.sh`
- Smoke test: `scripts/smoke-test.sh`

## Desktop App

- Windows environment check: `scripts/check-tauri-windows-env.ps1`
- Windows setup guide: `docs/tauri-windows-setup.md`

## License

This project is licensed under the MIT License. See the `LICENSE` file.
