# DFS Settlement Operations

This note documents the operational trust boundary around `dfs::settle(...)`.

It does not change the current on-chain model. Its purpose is to make the current `settlement_authority` assumption explicit and operationally controlled.

## Current model

`dfs::settle(...)` still depends on `settlement_authority`.

The contract now enforces stronger payout eligibility, but the authority role still decides when settlement is submitted and which eligible payout set is used.

This means the remaining trust concentration is operational, not accidental.

## Required operating stance

- keep `settlement_authority` on a dedicated operational account
- do not reuse the DFS contract account for settlement authority
- do not reuse the same key for deploy and settlement
- keep settlement keys separate from hot user-facing infrastructure
- document who is allowed to trigger settlement

## Minimum controls

- separate key custody for:
  - DFS contract deployment
  - DFS settlement authority
- restricted access to the settlement execution environment
- auditable logging of every settlement run
- review of payout recipients before submission
- periodic rotation or re-issuance of settlement credentials when operators change

## Recommended environment split

- contract account: `decentrfstor` or the production DFS contract account
- settlement account: dedicated service account used only for `settle(...)`
- operational host: separate from public web/API nodes where possible

## Before enabling settlement

Confirm:

- `pricepolicy.settlement_authority` is the intended dedicated account
- accepted tokens are configured correctly
- storage nodes expected to participate are active
- stake thresholds are satisfied
- price offers are fresh enough for policy
- payout owners are unique and map to eligible storage-capable nodes

## During each settlement run

Check:

- the payout set matches the intended eligible node set
- the number of eligible nodes satisfies `min_eligible_price_nodes`
- no unexpected owner appears in payouts
- no payout is routed to a non-storage or inactive node owner

## After each settlement run

Record:

- settlement tx id
- settlement timestamp
- settlement operator
- payout recipients
- payout amounts
- policy snapshot used during the run

Recommended:

- archive the settlement input used by the operator
- keep a simple internal ledger linking settlement tx ids to operational reports

## Incident response

If a settlement key is suspected to be compromised:

- stop automated settlement immediately
- rotate or replace the settlement authority key
- review recent settlement transactions
- confirm the configured `settlement_authority` is still correct on-chain

If payout selection looks suspicious:

- suspend further settlement runs
- inspect active nodes, stake state, and price offers
- verify the recipient set against the on-chain eligibility rules

## Summary

The remaining DFS settlement risk is a documented trust assumption around `settlement_authority`.

Treat it like an operationally sensitive signing role:

- separate it
- monitor it
- log it
- rotate it
- do not mix it with general deployment or public-service credentials
