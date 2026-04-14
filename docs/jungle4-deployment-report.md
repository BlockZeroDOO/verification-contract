# Jungle4 Deployment Report

Date: `2026-04-14`

## Target

- network: `Jungle4`
- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`
- contract account: `verification`
- deployed scope: `verification` only

## Repository State

- branch: `main`
- deploy baseline included the live-chain integration and rollout hardening work from `denotary/main`

## Deployment Result

Contract deployment completed successfully.

- deploy transaction: `77d80180e019d24a580578df6512ced0a9c5c0775d5b8f6b75e10f0cfbb78ab1`
- deployed code hash: `28704acfd3ef748ff7655ecc02a33838f97768f79b5b53952a37d955746ea0be`

ABI verification confirmed the expected DeNotary model, including:

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`
- `counters`
- legacy `proofs` and `paytokens`

## On-Chain Validation

The following checks were completed successfully:

- `cleos get code verification`
- `cleos get abi verification`
- table reads for `kyc`, `schemas`, `policies`, `commitments`, and `batches`
- `./scripts/smoke-test-jungle4.sh`

Smoke test result:

- status: `passed`

## Live-Chain Integration Validation

The following command completed successfully:

```bash
./scripts/run-live-chain-integration.sh \
  --rpc-url https://jungle4.api.eosnation.io \
  --expected-chain-id 73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d \
  --network-label Jungle4 \
  --owner-account verification \
  --submitter-account verification
```

Validated live single flow:

- single transaction id: `b40fcdede4f0785d41d8a903bca85fbae7e2dcd90361026f900df1e2ea5a8b1f`
- resulting commitment id: `5`

Validated live batch flow:

- `submitroot` transaction id: `e3338678d459652046791b0d752496dba98e1c365bfc6e651998ae5ee658c69c`
- `linkmanifest` transaction id: `2984db871c45d0695ca36b3e10b5f6323552def2e1be01352c5e707225722de2`
- `closebatch` transaction id: `af781810bc258d1d843641e50dd157f66e12045574b5f6fa7bc3a5b36c91f0c0`
- resulting batch id: `2`

## Operational Notes

- initial deploy attempts hit Jungle4 `tx_net_usage_exceeded`; deploy succeeded after increasing available `NET`
- WSL launcher scripts were adjusted to prefer POSIX Python interpreters over Windows `.venv/Scripts/python.exe`
- the on-chain smoke script was hardened to tolerate eventual consistency on public testnets and to reuse an existing KYC row

## Outcome

`verification` is successfully deployed and validated on Jungle4 as an external DeNotary test environment.
