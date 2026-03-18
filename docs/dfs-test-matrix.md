# DFS Test Matrix

## Purpose

This document defines the minimum test matrix required before `dfs` can be used as the
storage-trust and payment contract for metadata integration.

It complements:

- `docs/dfs-hardening-plan.md`
- `docs/dfs-testnet-bootstrap.md`

## Test layers

### 1. Contract unit / action tests

These tests validate contract invariants at the action level.

### 2. Deployment/bootstrap tests

These tests validate that a fresh testnet bootstrap can configure policy, register nodes,
fund stake, and accept storage receipts.

### 3. Economic safety tests

These tests validate custody and settlement invariants.

### 4. Integration-readiness tests

These tests validate that metadata-side consumers can rely on the on-chain model.

## Required test cases

### Registry and role validation

- register `metadata` node with valid metadata endpoint
- register `storage` node with valid storage endpoint
- register `both` node with both endpoints
- reject duplicate `node_id`
- reject unsupported role
- reject missing required endpoint for role
- reject malformed endpoint scheme
- reject malformed public key
- update node with valid owner auth
- reject update from non-owner
- reject update of retired node

### Stake lifecycle

- reject stake deposit before policy exists
- reject stake deposit for unknown node
- reject stake deposit from non-owner
- accept first stake deposit with exact minimum
- accept stake top-up
- reject stake deposit with wrong token contract
- reject stake deposit with wrong symbol
- request unstake from active stake
- reject `withdrawstk` before cooldown
- allow `withdrawstk` after cooldown
- reject top-up while unstake is pending

### Token and pricing policy

- create accepted token config
- update accepted token enable/disable flag
- reject invalid token precision mismatch
- create initial policy with valid settlement authority
- reject policy with non-existent settlement authority
- reject changing stake token while live stakes exist
- reject changing stake minimum while live stakes exist

### Price offers

- create price offer for active storage node
- update price offer for same owner
- reject price offer for metadata-only node
- reject price offer for suspended node
- reject price offer with disabled token

### Transfer classification

- accept `stake|<node_id>` memo and record stake state
- accept `storage|<payment_reference>|<manifest_hash>` memo and create storage receipt
- reject unknown memo type
- reject malformed storage memo
- reject duplicate `payment_reference`

### Receipts and custody

- storage receipt created with `received` status
- reject settlement without matching receipt
- reject settlement when receipt manifest hash mismatches
- reject settlement when gross quantity mismatches receipt
- reject settlement when token contract mismatches receipt
- reject second settlement for same `payment_reference`

### Settlement safety

- reject duplicate `settlement_id`
- reject duplicate `payment_txid`
- reject settlement where payouts + protocol fee exceed gross
- reject settlement where payouts + protocol fee are below gross
- accept settlement with exact accounting
- require configured settlement authority
- reject settlement from unauthorized actor

### Balances and claims

- create first balance row on settlement
- increment existing balance on repeated owner payout across different settlements
- reject claim above available balance
- allow exact claim
- allow partial claim
- verify balance is reduced after claim

### Token/policy mutation guards

- reject `rmtoken` with live balances
- reject `rmtoken` with live price offers
- reject `rmtoken` with unsettled receipts
- allow `rmtoken` only after state is drained or disabled path is used first

## Read-model assertions for metadata integration

The following shapes must be readable and stable from chain tables:

- `nodes`
  - role
  - owner
  - endpoints
  - status
- `stakes`
  - quantity
  - status
  - cooldown
- `priceoffers`
  - token
  - unit price
  - pricing unit
  - effective time
- `acceptedtokens`
  - token contract
  - symbol
  - enabled
- `pricingpolicy`
  - stake minimum
  - settlement authority
  - algorithm
- `receipts`
  - payment reference
  - receipt kind
  - amount
  - settlement status

## Release gates

`dfs` is not ready for metadata integration until all of these are true:

- contract compiles and emits ABI/WASM cleanly
- bootstrap runbook works end-to-end on testnet
- all critical and high-severity test cases above are covered
- duplicate settlement by business event is impossible
- unknown token transfers are not silently accepted
- governance cannot remove live token state or mutate live stake policy unsafely

## Nice-to-have tests after the first release

- RAM delta tracking for each action path
- large-owner balance fanout performance checks
- receipt retention / archival compatibility
- migration tests for future state normalization of `node_id`
