# DFS Contract Hardening Plan

## Status

Implementation backlog for the first hardening pass of the `dfs` contract scaffold.

This document turns the current audit findings into an ordered patch plan for:

- `include/dfs.hpp`
- `src/dfs.cpp`

The goal is to close the highest-risk issues first:

1. RAM griefing
2. settlement double-credit risk
3. weak custody accounting
4. silent transfer acceptance
5. token/policy mutation hazards

## Hardening Order

### Patch Group 1. RAM payer model

Priority: critical

Files:

- `src/dfs.cpp`
- `include/dfs.hpp`

Changes:

- make owner-funded state use `owner_account` as RAM payer:
  - `regnode`
  - new `priceoffers` rows in `setprice`
  - first `stakes` row in `upsert_stake_after_deposit`
- for owner-driven `modify(...)`, use the owner as payer where growth is allowed
- if a row is contract-owned for a deliberate reason, document that explicitly in code comments and docs

Acceptance criteria:

- ordinary node operators can no longer force contract RAM growth through registration churn
- endpoint/public-key updates do not re-bill RAM to `dfs`

Tests:

- owner registration pays owner RAM
- owner update that grows string fields does not charge contract RAM
- new price offer row is owner-funded
- first stake row is owner-funded

## Patch Group 2. Settlement idempotency and uniqueness

Priority: critical

Files:

- `include/dfs.hpp`
- `src/dfs.cpp`

Changes:

- extend `settlements` with stronger uniqueness keys:
  - `payment_txid`
  - optionally `file_id`
- add secondary indexes so `settle(...)` rejects duplicate settlement by business event, not only by `settlement_id`
- decide canonical uniqueness rule:
  - preferred baseline: one settlement per `payment_txid`

Acceptance criteria:

- replaying `settle(...)` under a new `settlement_id` for the same payment cannot mint more balances

Tests:

- duplicate `settlement_id` rejected
- duplicate `payment_txid` rejected
- same `file_id` with different payment can still settle if intended

## Patch Group 3. Custody accounting and backing invariants

Priority: critical

Files:

- `include/dfs.hpp`
- `src/dfs.cpp`

Changes:

- introduce explicit receipt/custody tables:
  - `stakereceipts`
  - `payreceipts` or one generalized `receipts`
- classify receipts by type:
  - `stake_deposit`
  - `storage_payment`
- make `settle(...)` require a matching recorded storage payment receipt
- add backing checks so credited balances cannot exceed available undistributed custody
- add explicit fields for:
  - `claimed_quantity`
  - `distributed_quantity`
  - optional `protocol_reserved_quantity`

Acceptance criteria:

- claimable balances are always backed by prior custody
- `settle(...)` cannot create balances from thin air

Tests:

- settle without receipt rejected
- settle above receipt amount rejected
- settle twice against same receipt rejected
- protocol fee + payouts cannot exceed gross payment

## Patch Group 4. Strict transfer classification

Priority: high

Files:

- `src/dfs.cpp`

Changes:

- stop silently accepting non-stake transfers
- explicitly parse and branch on memo families:
  - `stake|<node_id>`
  - `storage|<quote_id>|<manifest_hash>` or staged equivalent
- reject unknown incoming transfers with a clear error
- only treat transfer as passive custody if a deliberate receipt path exists

Acceptance criteria:

- no arbitrary token transfer can land in `dfs` without being classified

Tests:

- unknown memo rejected
- malformed stake memo rejected
- malformed storage memo rejected
- valid stake memo accepted
- valid storage memo creates receipt

## Patch Group 5. Balance-table indexing

Priority: high

Files:

- `include/dfs.hpp`
- `src/dfs.cpp`

Changes:

- replace owner-only lookup with composite lookup:
  - `owner_account + token_contract + symbol_code`
- remove linear scan in `find_balance(...)`
- keep claim and settlement hot path logarithmic

Acceptance criteria:

- `claimrevenue(...)` and `settle(...)` no longer iterate over all owner balances

Tests:

- multiple balances for one owner stay addressable without scan-dependent behavior

## Patch Group 6. Node and offer state normalization

Priority: medium

Files:

- `include/dfs.hpp`
- `src/dfs.cpp`

Changes:

- reduce repeated `node_id` string storage across tables
- preferred options:
  - numeric row reference from `nodes`
  - or compact checksum key stored once and reused
- keep full `node_id` only where needed for public readability

Acceptance criteria:

- `stakes` and `priceoffers` do not duplicate large node identifiers unnecessarily

Tests:

- lookups still resolve node ownership and offers correctly after normalization

## Patch Group 7. Stronger semantic validation

Priority: medium

Files:

- `src/dfs.cpp`

Changes:

- add stronger endpoint validation
- add stronger public-key shape validation
- require role-compatible fields:
  - metadata-capable nodes need metadata endpoint
  - storage-capable nodes need storage endpoint
- reserve clearer node status transitions

Acceptance criteria:

- syntactically printable but semantically broken node metadata is rejected on-chain

Tests:

- metadata role without metadata endpoint rejected
- storage role without storage endpoint rejected
- malformed public key rejected

## Patch Group 8. Policy and token mutation guards

Priority: medium

Files:

- `src/dfs.cpp`

Changes:

- `setpolicy(...)` must not silently invalidate live stakes
- `rmtoken(...)` must not remove tokens still used by:
  - active balances
  - active price offers
  - live custody receipts
- operational default should prefer `enabled=false` over destructive delete

Acceptance criteria:

- governance actions cannot strand live user or operator state

Tests:

- cannot remove token with live balances
- cannot remove token with live offers
- cannot change stake token while active stakes exist

## Patch Group 9. Settlement authority model

Priority: medium

Files:

- `include/dfs.hpp`
- `src/dfs.cpp`

Changes:

- introduce explicit settlement authority configuration instead of hard-wiring `require_auth(get_self())`
- allow later migration to:
  - metadata authority account
  - multisig
  - governance authority

Acceptance criteria:

- settlement and governance authority boundaries are explicit in contract state

Tests:

- unauthorized settlement rejected
- configured settlement authority accepted

## Patch Group 10. Documentation and deploy runbooks

Priority: medium

Files:

- `README.md`
- `docs/testnet-deploy.md`
- `docs/mainnet-deploy.md`

Changes:

- document:
  - RAM payer model
  - supported memo families
  - stake deposit flow
  - storage payment receipt flow
  - settlement authority
  - claim flow

Acceptance criteria:

- operators can bootstrap and reason about custody without reading the source

## Suggested Implementation Sequence

1. Patch Group 1
2. Patch Group 2
3. Patch Group 3
4. Patch Group 4
5. Patch Group 5
6. Patch Group 8
7. Patch Group 7
8. Patch Group 9
9. Patch Group 6
10. Patch Group 10

Reason:

- start with money and RAM invariants
- then make transfer and governance behavior safe
- only after that optimize structure and polish docs

## Definition of Done for the first hardening milestone

The first hardening milestone is complete when:

- owner-driven writes no longer charge RAM to `dfs`
- settlement is idempotent by business event, not only request id
- `settle(...)` is backed by explicit custody receipts
- unknown transfers are rejected
- balance lookup is indexed
- token/policy mutation cannot strand live funds or stakes
- docs describe the operational contract clearly
