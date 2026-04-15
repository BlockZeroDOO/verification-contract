<h1 class="contract">issuekyc</h1>

Creates a KYC registry row for an account and marks it active until `expires_at`.

<h1 class="contract">renewkyc</h1>

Reactivates or extends an existing KYC registry row.

<h1 class="contract">revokekyc</h1>

Revokes an existing KYC registry row and marks it inactive.

<h1 class="contract">suspendkyc</h1>

Suspends an existing KYC registry row without deleting it.

<h1 class="contract">addschema</h1>

Creates a schema registry row with canonicalization and hash policy references.

<h1 class="contract">updateschema</h1>

Updates an active schema registry row.

<h1 class="contract">deprecate</h1>

Marks a schema registry row inactive for future submissions.

<h1 class="contract">setpolicy</h1>

Creates or updates a retail policy registry row for single, batch, and KYC rules.

<h1 class="contract">enablezk</h1>

Enables the optional ZK capability flag on a policy.

<h1 class="contract">disablezk</h1>

Disables the optional ZK capability flag on a policy.

<h1 class="contract">submit</h1>

Creates a single anchored commitment after schema, policy, and optional KYC validation, and consumes an exact one-time retail payment receipt from the same transaction flow.

<h1 class="contract">supersede</h1>

Moves an active commitment into the `superseded` business status and links it to a successor commitment.

<h1 class="contract">revokecmmt</h1>

Moves an active commitment into the `revoked` business status.

<h1 class="contract">expirecmmt</h1>

Moves an active commitment into the `expired` business status.

<h1 class="contract">submitroot</h1>

Creates a batch anchoring record after schema, policy, and optional KYC validation, and consumes an exact one-time retail payment receipt from the same transaction flow.

<h1 class="contract">linkmanifest</h1>

Links an immutable manifest hash to an open batch record.

<h1 class="contract">closebatch</h1>

Closes an open batch and prevents further mutable batch updates.

<h1 class="contract">settoken</h1>

Registers or re-enables a token that can be used for retail atomic payment.

<h1 class="contract">rmtoken</h1>

Removes a retail payment token when no active retail tariff depends on it.

<h1 class="contract">setprice</h1>

Creates or updates an exact retail tariff for `single` or `batch` mode.

<h1 class="contract">withdraw</h1>

Transfers tokens already held by `verifretail` to another account.
