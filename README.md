# GlobalForce Notary Contract

This repository contains a minimal GlobalForce/Antelope-compatible smart contract for the
`GlobalForce Notary` concept described in the provided documents.

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

- `paytokens`: accepted payment tokens with `token_contract`, `retail_price`, and `wholesale_price`
- `wholesale`: list of accounts eligible for wholesale pricing
- `nonprofit`: list of accounts that can submit proofs for free
- `proofsv2`: submitted proof records with the effective price, pricing mode, and payment token contract

## Actions

- `addwhuser(name account, string note)`
- `rmwhuser(name account)`
- `addnporg(name account, string note)`
- `rmnporg(name account)`
- `setpaytoken(name token_contract, asset retail_price, asset wholesale_price)`
- `rmpaytoken(name token_contract, symbol token_symbol)`
- `submitfree(name submitter, string object_hash, string hash_algorithm, string canonicalization_profile, string client_reference)`
- `withdraw(name token_contract, name to, asset quantity, string memo)`

## Internal helpers

- `quote(...)`, `iswhuser(...)`, `isnporg(...)` remain available as C++ contract helpers, but are not exposed as ABI actions because CDT 4.1.1 dispatcher support is limited to `void` actions.

## Example flow

```bash
cleos push action gfnotary setpaytoken '["eosio.token", "1.0000 GFT", "0.1000 GFT"]' -p gfnotary
cleos push action gfnotary addwhuser '["studio.partner", "B2B wholesale client"]' -p gfnotary
cleos push action gfnotary addnporg '["charity.acc", "nonprofit organization"]' -p gfnotary
cleos push action eosio.token transfer '[
  "retail.user",
  "gfnotary",
  "1.0000 GFT",
  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|retail-0001"
]' -p retail.user

cleos push action eosio.token transfer '[
  "studio.partner",
  "gfnotary",
  "0.1000 GFT",
  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef|SHA-256|none|batch-2026-0001"
]' -p studio.partner

cleos push action gfnotary submitfree '[
  "charity.acc",
  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "SHA-256",
  "none",
  "charity-0001"
]' -p charity.acc
```

## Notes

- Contract listens to `*::transfer`, but only accepts tokens configured in `paytokens`.
- Retail and wholesale prices are configured per token in `paytokens`; nonprofit submissions are stored as `0.0000 FREE`.
- New `proofsv2` rows are stored with `get_self()` as RAM payer, so storage is paid by the contract account.
- CPU/NET of the user-signed transfer transaction are still paid by the signer unless you add an external sponsorship layer.
- The contract is intentionally small so it can be extended later with batching, Merkle roots, anchoring, and richer receipts.

## Testnet

- Build scripts: `scripts/build-testnet.sh`, `scripts/build-testnet.ps1`
- Smoke test: `scripts/smoke-test.sh`
- Deploy guide: `docs/testnet-deploy.md`

## Desktop App

- Windows environment check: `scripts/check-tauri-windows-env.ps1`
- Windows setup guide: `docs/tauri-windows-setup.md`
