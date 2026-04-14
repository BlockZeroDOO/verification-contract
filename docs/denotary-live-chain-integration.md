# DeNotary Live-Chain Integration

## Purpose

This runbook covers the real-chain integration suite for `verification`.

Unlike the mock integration suite, this flow:

- starts local DeNotary services in-process
- prepares requests through `Ingress API`
- broadcasts real on-chain transactions with `cleos`
- waits for irreversible finality against a live Antelope RPC
- verifies `Receipt Service` and `Audit API` against actual chain data

Implementation:

- [tests/live_chain_integration.py](/c:/projects/verification-contract/tests/live_chain_integration.py:1)
- [scripts/run-live-chain-integration.sh](/c:/projects/verification-contract/scripts/run-live-chain-integration.sh:1)
- [scripts/run-live-chain-integration.ps1](/c:/projects/verification-contract/scripts/run-live-chain-integration.ps1:1)

## Covered flow

The suite currently verifies:

- KYC bootstrap or renewal for the submitter account
- creation of a fresh schema and fresh single/batch policies
- live single flow: `Ingress API -> submit -> watcher -> receipt -> audit`
- live batch flow: `Ingress API -> submitroot -> linkmanifest -> closebatch -> watcher -> receipt -> audit`
- irreversible finality detection through `Finality Watcher`
- audit lookups by `tx_id`, `commitment_id`, `batch_id`, and `external_ref_hash`

For the batch path, the watcher tracks the terminal `closebatch` transaction, while the suite separately verifies that `submitroot` and `linkmanifest` succeeded on-chain first.

## Prerequisites

- `cleos` is installed and available in `PATH`
- Python is available
- keys are imported for the `verification` governance account
- keys are imported for the test submitter account
- the target `verification` contract is already deployed

Required runtime values:

- `owner-account`
- `submitter-account`

## deNotary.io run

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/run-live-chain-integration.sh \
  --owner-account "${OWNER_ACCOUNT}" \
  --submitter-account "${SUBMITTER_ACCOUNT}"
```

Default network values:

- `rpc-url=https://history.denotary.io`
- `expected-chain-id=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`
- `network-label=deNotary.io`

## Jungle4 run

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/run-live-chain-integration.sh \
  --rpc-url https://jungle4.api.eosnation.io \
  --expected-chain-id 73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d \
  --network-label Jungle4 \
  --owner-account "${OWNER_ACCOUNT}" \
  --submitter-account "${SUBMITTER_ACCOUNT}"
```

## PowerShell run

```powershell
./scripts/run-live-chain-integration.ps1 --owner-account verification --submitter-account youruser
```

## Useful options

```bash
./scripts/run-live-chain-integration.sh \
  --owner-account verification \
  --submitter-account youruser \
  --wait-timeout-sec 240 \
  --poll-interval-sec 3
```

Available options:

- `--rpc-url`
- `--expected-chain-id`
- `--skip-chain-id-check`
- `--network-label`
- `--verification-account`
- `--owner-account`
- `--submitter-account`
- `--watcher-auth-token`
- `--wait-timeout-sec`
- `--poll-interval-sec`

## Notes

- this suite is intentionally separate from [docs/denotary-onchain-smoke.md](/c:/projects/verification-contract/docs/denotary-onchain-smoke.md:1)
- `smoke-test-onchain.sh` focuses on contract actions and lifecycle guards
- `live_chain_integration.py` focuses on real end-to-end reconciliation between chain state, finality, receipts, and audit reads
- current batch receipts are finalized against the `closebatch` transaction, not the earlier `submitroot` transaction
- if `--watcher-auth-token` is provided, the local watcher requires that token for its mutation endpoints during the run
