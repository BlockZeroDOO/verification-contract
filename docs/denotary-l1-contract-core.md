# Verification Contract Core

This document describes the canonical on-chain scope of the `verifent` contract.

## Repository Boundary

- `C:\projects\verification-contract` owns the `verifent` and `verifretail` smart contracts
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

The `verifent` contract anchors hashes and batch roots on-chain under explicit governance rules.

It is responsible for:

- KYC-gated submit access
- schema registry
- policy registry
- single commitment anchoring
- batch anchoring
- lifecycle transitions for commitments and batches

It is not responsible for:

- finality observation
- receipt generation
- audit indexing
- ingress request preparation
- DFS storage payments

## On-Chain Tables

### `kyc`

Stores submitter access state.

Fields:

- `account`
- `level`
- `provider`
- `jurisdiction`
- `active`
- `issued_at`
- `expires_at`

### `schemas`

Stores canonicalization and hashing rules.

Fields:

- `id`
- `version`
- `canonicalization_hash`
- `hash_policy`
- `active`
- `created_at`
- `updated_at`

### `policies`

Stores single/batch/KYC/ZK rules.

Fields:

- `id`
- `allow_single`
- `allow_batch`
- `require_kyc`
- `min_kyc_level`
- `allow_zk`
- `active`
- `created_at`
- `updated_at`

### `commitments`

Stores single-record anchors.

Fields:

- `id`
- `submitter`
- `schema_id`
- `policy_id`
- `object_hash`
- `external_ref`
- `request_key`
- `block_num`
- `created_at`
- `status_changed_at`
- `status`
- `superseded_by`

### `batches`

Stores batch anchors.

Fields:

- `id`
- `submitter`
- `root_hash`
- `leaf_count`
- `schema_id`
- `policy_id`
- `manifest_hash`
- `external_ref`
- `request_key`
- `block_num`
- `created_at`
- `manifest_linked_at`
- `status_changed_at`
- `status`

### `counters`

Stores monotonic IDs for anchored entities.

Fields:

- `next_commitment_id`
- `next_batch_id`

## Core Actions

### Governance

- `issuekyc`
- `renewkyc`
- `revokekyc`
- `suspendkyc`
- `addschema`
- `updateschema`
- `deprecate`
- `setpolicy`
- `enablezk`
- `disablezk`

### Anchoring

- `submit`
- `supersede`
- `revokecmmt`
- `expirecmmt`
- `submitroot`
- `linkmanifest`
- `closebatch`

### Treasury

- `withdraw`

## Business Status Model

### Commitments

- `0 = active`
- `1 = superseded`
- `2 = revoked`
- `3 = expired`

### Batches

- `0 = open`
- `1 = closed`

Finality is intentionally not stored as a business status in the contract.

## Validation Rules

### `submit`

Must satisfy:

- existing active schema
- existing active policy with `allow_single = true`
- non-zero `object_hash`
- non-zero `external_ref`
- unique `request_key`
- valid KYC when required by policy

### `submitroot`

Must satisfy:

- existing active schema
- existing active policy with `allow_batch = true`
- non-zero `root_hash`
- non-zero `external_ref`
- `leaf_count > 0`
- unique `request_key`
- valid KYC when required by policy

### `supersede`

Must satisfy:

- source commitment exists
- source commitment is active
- successor commitment exists
- successor is different from source

### `closebatch`

Must satisfy:

- batch exists
- batch is open
- manifest is already linked

## Deployment Assumption

The contract is deployed to a clean account and does not perform in-place migration from the previous proof-payment design.

That means:

- the current on-chain model is `kyc + schemas + policies + commitments + batches`
- legacy proof-payment state and actions are removed
- off-chain read services are external to this repository
