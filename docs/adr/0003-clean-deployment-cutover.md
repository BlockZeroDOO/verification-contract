# ADR 0003: Clean Deployment Cutover

## Status

Accepted.

## Context

The earlier contract lineage included a legacy proof-oriented payment model with:

- a `proofs` table
- a `record(...)` action
- a transfer-triggered paid submit path

The target DeNotary L1 model for the current contract family is different and is centered on:

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`

At the time of the redesign there were two options:

1. design a compatibility and migration layer from the old proof model
2. deploy the new model to fresh contract accounts and avoid legacy migration entirely

The project context allowed the second option.

## Decision

For the current product line we use a fresh-deployment model:

- new contract surfaces are deployed to clean accounts
- no migration from `proofs` to `commitments` is designed
- no compatibility path for the old proof-payment actions is required
- the contract surface follows the target model directly instead of preserving legacy shapes

## Consequences

Benefits:

- cleaner domain model
- lower implementation risk
- no compatibility baggage in the enterprise surface
- easier split between enterprise and retail products

Costs:

- older deploy and runbook docs must be updated
- previous proof-payment flows are not preserved

## Rejected Alternatives

### Alternative 1. Migrate legacy proof rows

Rejected because:

- there was no active migration need for the target rollout
- it would add complexity before there was a real production use case

### Alternative 2. Keep `record(...)` as a compatibility action

Rejected because:

- it does not match the target schema/policy/KYC/batch model
- it would distort the new contract API for the sake of backward compatibility
