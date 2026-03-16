# Verification Contract

This repository contains a minimal GlobalForce/Antelope-compatible smart contract for the
`verification` smart contract concept described in the provided documents.

## Why this contract shape

The roadmap document frames the product as a proof-of-existence registry with a commercial
model that distinguishes customer segments and volume-based pricing. Based on that, the
contract includes:

- configurable payment tokens in a `paytokens` table
- a dedicated `wholesale` table for special-price accounts
- a dedicated `nonprofit` table for free non-commercial organizations
- `addwhuser` and `rmwhuser` actions for wholesale account management
- `addnporg` and `rmnporg` actions for nonprofit account management
- `setpaytoken` and `rmpaytoken` for token pricing configuration
- `submitfree` for nonprofit proof submission without token payment
- automatic proof creation on incoming token payment

## Tables

- `paytokens`: accepted payment tokens with `token_contract`, `retail_price`, `wholesale_price`, and `storage_price`
- `wholesale`: list of accounts eligible for wholesale pricing
- `nonprofit`: list of accounts that can submit proofs for free
- `freepolicy`: singleton config for nonprofit free submissions, including the 24-hour global sponsor limit
- `freeusage`: per-account timestamp of the last nonprofit submission for 60-second cooldown enforcement
- `proofs`: submitted proof records with the effective price, pricing mode, payment token contract, and client reference

## Actions

- `addwhuser(name account, string note)`
- `rmwhuser(name account)`
- `addnporg(name account, string note)`
- `rmnporg(name account)`
- `setpaytoken(name token_contract, asset retail_price, asset wholesale_price, asset storage_price)`
- `rmpaytoken(name token_contract, symbol token_symbol)`
- `submitfree(name submitter, string object_hash, string hash_algorithm, string canonicalization_profile, string client_reference)`
- `setfreecfg(bool enabled, uint32_t daily_free_limit)`
- `withdraw(name token_contract, name to, asset quantity, string memo)`

## Internal helpers

- `quote(...)`, `iswhuser(...)`, `isnporg(...)` remain available as C++ contract helpers, but are not exposed as ABI actions because CDT 4.1.1 dispatcher support is limited to `void` actions.

## Example flow

```bash
cleos push action verification setpaytoken '["eosio.token", "1.0000 GFT", "0.1000 GFT", "0.0100 GFT"]' -p verification
cleos push action verification setfreecfg '[true, 100]' -p verification
cleos push action verification addwhuser '["studio.partner", "B2B wholesale client"]' -p verification
cleos push action verification addnporg '["charity.acc", "nonprofit organization"]' -p verification
cleos push action eosio.token transfer '[
  "retail.user",
  "verification",
  "1.0000 GFT",
  "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user

cleos push action eosio.token transfer '[
  "studio.partner",
  "verification",
  "0.1000 GFT",
  "2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|batch-2026-0001"
]' -p studio.partner

cleos push action verification submitfree '[
  "charity.acc",
  "3123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "SHA-256",
  "none",
  "charity-0001"
]' -p charity.acc
```

## Notes

- Contract listens to `*::transfer`, but only accepts tokens configured in `paytokens`.
- Retail and wholesale prices drive on-chain proof pricing. `storage_price` is stored in `paytokens` for external storage integration and does not change the on-chain proof price; nonprofit submissions are stored as `0.0000 FREE`.
- `setpaytoken` validates the configured symbol precision against the token contract `stat` table, so invalid token precision is rejected before users attempt paid transfers.
- `submitfree` is gated by `freepolicy`; nonprofit accounts can submit at most once every 60 seconds, and all nonprofit submissions share one contract-wide 24-hour sponsored limit.
- The 60-second cooldown applies only to `nonprofit` accounts using `submitfree`; paid retail and wholesale submissions have no time-based cooldown in the contract.
- `canonicalization_profile` must be non-empty printable ASCII up to 32 characters. The examples use `none`.
- `client_reference` is required on both paid and free flows, acts as an idempotency key per submitter, and must use printable ASCII without `|`.
- `object_hash` is not globally unique; the same document hash can be notarized multiple times as long as each request uses a new `client_reference`.
- New `proofs` rows are stored with `get_self()` as RAM payer, so storage is paid by the contract account.
- `withdraw` can transfer tokens already held by the contract account even if the corresponding `paytokens` config entry was later removed.
- CPU/NET of the user-signed transfer transaction are still paid by the signer unless you add an external sponsorship layer.
- The contract is intentionally small so it can be extended later with batching, Merkle roots, anchoring, and richer receipts.

## Testnet

- Build scripts: `scripts/build-testnet.sh`, `scripts/build-testnet.ps1`
- Smoke test: `scripts/smoke-test.sh`
- Deploy guide: `docs/testnet-deploy.md`

## Mainnet

- Release build scripts: `scripts/build-release.sh`, `scripts/build-release.ps1`
- Deploy guide: `docs/mainnet-deploy.md`

## Desktop App

- Windows environment check: `scripts/check-tauri-windows-env.ps1`
- Windows setup guide: `docs/tauri-windows-setup.md`
