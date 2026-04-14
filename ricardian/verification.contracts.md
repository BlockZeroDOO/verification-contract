# Ricardian Clauses

## issuekyc

Creates a KYC registry row for an account and marks it active until `expires_at`.

## renewkyc

Reactivates or extends an existing KYC registry row.

## revokekyc

Revokes an existing KYC registry row and marks it inactive.

## suspendkyc

Suspends an existing KYC registry row without deleting it.

## addschema

Creates a schema registry row with canonicalization and hash policy references.

## updateschema

Updates an active schema registry row.

## deprecate

Marks a schema registry row inactive for future submissions.

## setpolicy

Creates or updates a policy registry row for single, batch, and KYC rules.

## enablezk

Enables the optional ZK capability flag on a policy.

## disablezk

Disables the optional ZK capability flag on a policy.

## record

Appends a proof row to the immutable `verification` registry.

The action stores:

- the writing contract account in `writer`
- the end-user account in `submitter`
- the submitted `object_hash`
- the submitted `canonicalization_profile`
- the submitted `client_reference`
- the on-chain timestamp in `submitted_at`

The same `(submitter, client_reference)` pair cannot be recorded twice. This action is intended
for contract-internal writes.

## setpaytoken

Creates or updates a payment token configuration with one fixed price for all clients.

## rmpaytoken

Removes a payment token configuration from `verification`.

## withdraw

Transfers tokens already held by `verification` to another account.
