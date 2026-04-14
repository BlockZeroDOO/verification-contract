# DeNotary On-Chain Contracts

This repository currently contains two Antelope-compatible smart contracts:

- `verification`: DeNotary L1 on-chain registry and anchoring core
- `dfs`: DFS registry, stake, pricing, receipts, and settlement scaffold

## `verification` scope

`verification` now contains the DeNotary on-chain baseline for:

- KYC access control
- schema registry
- policy registry
- single-record anchoring
- batch anchoring
- business lifecycle tracking for commitments and batches
- legacy paid proof ingestion and treasury handling

## Tables

### Core registry tables

- `kyc`: KYC state by account
- `schemas`: canonicalization and hash-policy references
- `policies`: single/batch/KYC/ZK capability flags
- `commitments`: single-record anchoring rows
- `batches`: batch anchoring rows
- `counters`: monotonic IDs for anchored entities

### Legacy/payment tables

- `proofs`: legacy append-only proof rows used by the paid transfer flow
- `paytokens`: accepted payment tokens with fixed prices

## Actions

### Registry governance

- `issuekyc(name account, uint8_t level, string provider, string jurisdiction, time_point_sec expires_at)`
- `renewkyc(name account, time_point_sec expires_at)`
- `revokekyc(name account)`
- `suspendkyc(name account)`
- `addschema(uint64_t id, string version, checksum256 canonicalization_hash, checksum256 hash_policy)`
- `updateschema(uint64_t id, string version, checksum256 canonicalization_hash, checksum256 hash_policy)`
- `deprecate(uint64_t id)`
- `setpolicy(uint64_t id, bool allow_single, bool allow_batch, bool require_kyc, uint8_t min_kyc_level, bool active)`
- `enablezk(uint64_t id)`
- `disablezk(uint64_t id)`

### Anchoring core

- `submit(name submitter, uint64_t schema_id, uint64_t policy_id, checksum256 object_hash, checksum256 external_ref)`
- `supersede(uint64_t id, uint64_t successor_id)`
- `revokecmmt(uint64_t id)`
- `expirecmmt(uint64_t id)`
- `submitroot(name submitter, uint64_t schema_id, uint64_t policy_id, checksum256 root_hash, uint32_t leaf_count, checksum256 external_ref)`
- `linkmanifest(uint64_t id, checksum256 manifest_hash)`
- `closebatch(uint64_t id)`

### Legacy/payment layer

- `record(name submitter, checksum256 object_hash, string canonicalization_profile, string client_reference)`
- `setpaytoken(name token_contract, asset price)`
- `rmpaytoken(name token_contract, symbol token_symbol)`
- `withdraw(name token_contract, name to, asset quantity, string memo)`
- `*::transfer` notify handler for the paid legacy flow

## On-chain model notes

- `commitments.status` is a business status, not a finality status
- `batches.status` tracks open/closed business lifecycle only
- irreversible finality stays in the off-chain read model by design
- `supersede(...)` now links the original commitment to a successor via `superseded_by`
- batch closure requires a linked `manifest_hash`

## Build

Linux / WSL:

```bash
./scripts/build-testnet.sh
./scripts/build-release.sh
```

PowerShell:

```powershell
./scripts/build-testnet.ps1
./scripts/build-release.ps1
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## On-chain smoke test

The new registry and anchoring flow can be validated with:

```bash
export RPC_URL=https://your-rpc
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export SUBMITTER_ACCOUNT=someuser
./scripts/smoke-test-onchain.sh
```

The script checks:

- KYC issuance and renewal path
- schema and policy creation
- single commitment creation
- duplicate single request rejection
- supersede flow with explicit successor
- revoke and expire lifecycle transitions
- batch creation
- duplicate batch request rejection
- manifest linking
- batch close guard before manifest
- successful batch close after manifest linking

Detailed usage is documented in [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1).

## Off-chain baseline

The stage-6 ingestion scaffold lives in:

- [services/ingress_api.py](/c:/projects/verification-contract/services/ingress_api.py:1)
- [docs/denotary-ingress-api.md](/c:/projects/verification-contract/docs/denotary-ingress-api.md:1)

It currently prepares deterministic single and batch payloads for `submit` and `submitroot`.

## Legacy note

Some older deploy and smoke documents still describe the removed `managementel` flow. Treat the
current `README`, the `denotary-*` docs, and the updated scripts as the source of truth for the
current contract model.

## License

This project is licensed under the MIT License. See the `LICENSE` file.
