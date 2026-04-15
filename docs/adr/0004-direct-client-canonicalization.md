# ADR 0004: Direct Client Canonicalization And Submission

## Status

Accepted

## Context

The current DeNotary baseline includes an `Ingress API` that:

- canonicalizes payloads
- computes deterministic hashes
- prepares `submit` and `submitroot` action payloads
- issues `request_id` and `trace_id`

That path is useful, but it must not be the only supported submission mode.

Trusted desktop and backend clients need to be able to:

- canonicalize data locally
- compute deterministic hashes locally
- derive the same `request_id` locally
- assemble `submit` and `submitroot` directly
- sign and broadcast without calling `Ingress API`

## Decision

DeNotary supports two equivalent preparation modes:

1. `Ingress-assisted mode`
   - a client sends business payloads to `Ingress API`
   - the service canonicalizes, hashes, and prepares the action payload

2. `Direct client mode`
   - the client canonicalizes locally
   - the client computes `object_hash`, `root_hash`, `manifest_hash`, and `external_ref_hash` locally
   - the client derives `request_id` and `trace_id` locally
   - the client constructs and broadcasts `submit` or `submitroot` directly

`Ingress API` remains a supported helper service, but it is not a mandatory gateway for all DeNotary submissions.

## Implications

### Canonicalization becomes a shared contract

Deterministic canonicalization cannot live only inside `Ingress API`.

It must be expressed as:

- versioned schema rules
- a stable published algorithm specification
- reusable client-side implementations or libraries

### Watcher / receipt / audit stay valid

The finality and receipt pipeline works in both modes.

The difference is only the source of preparation:

- either `Ingress API`
- or the client itself

### Request identifiers must be reproducible

To avoid fragmentation between modes, the `request_id` formula must stay deterministic and publicly specified.

Direct clients must use the same derivation rules as `Ingress API`.

## Consequences

Positive:

- lower dependency on a central preprocessing service
- better resilience when ingress is unavailable
- stronger desktop and enterprise autonomy
- clearer fit for local-first clients

Tradeoffs:

- more logic moves into client libraries
- canonicalization specs must stay strict and versioned
- integration testing must cover both ingress-assisted and direct-client flows

## Follow-up work

- publish canonicalization and request-id formulas as a reusable specification
- add direct-client integration tests
- update frontend plans so `Ingress API` is optional
- keep `Ingress API` as a convenience and standardization service, not a hard dependency
