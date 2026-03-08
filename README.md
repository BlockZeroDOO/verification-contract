# GlobalForce Notary Contract

This repository contains a minimal GlobalForce/Antelope-compatible smart contract for the
`GlobalForce Notary` concept described in the provided documents.

## Why this contract shape

The roadmap document frames the product as a proof-of-existence registry with a commercial
model that distinguishes customer segments and volume-based pricing. Based on that, the
contract includes:

- fixed testnet pricing in `GFT`
- a dedicated `wholesale` table for special-price accounts
- `addwhuser` and `rmwhuser` actions for wholesale account management
- automatic proof creation on incoming token payment

## Tables

- `wholesale`: list of accounts eligible for wholesale pricing
- `proofs`: submitted proof records with the effective price and pricing mode

## Actions

- `addwhuser(name account, string note)`
- `rmwhuser(name account)`
- `withdraw(name to, asset quantity, string memo)`
- `quote(name account)` read-only helper that returns the current effective price
- `iswhuser(name account)` read-only helper that checks wholesale membership

## Example flow

```bash
cleos push action gfnotary addwhuser '["studio.partner", "B2B wholesale client"]' -p gfnotary
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
```

## Notes

- Contract listens only to `eosio.token::transfer` and accepts only `GFT`.
- Retail price is fixed to `1.0000 GFT`, wholesale price to `0.1000 GFT`.
- New `proofs` rows are stored with `get_self()` as RAM payer, so storage is paid by the contract account.
- CPU/NET of the user-signed transfer transaction are still paid by the signer unless you add an external sponsorship layer.
- The contract is intentionally small so it can be extended later with batching, Merkle roots, anchoring, and richer receipts.
