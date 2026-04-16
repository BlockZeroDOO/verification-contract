<h1 class="contract">addschema</h1>

Creates a schema registry row with canonicalization and hash policy references.

<h1 class="contract">updateschema</h1>

Updates an active schema registry row.

<h1 class="contract">deprecate</h1>

Marks a schema registry row inactive for future submissions.

<h1 class="contract">setpolicy</h1>

Creates or updates a minimal policy registry row for single and batch submit rules.

<h1 class="contract">setauthsrcs</h1>

Configures which enterprise billing contract and retail payment contract may supply one-time usage authorizations to `verif`.

<h1 class="contract">submit</h1>

Creates a single anchored commitment after schema, policy, and external usage-authorization validation.

<h1 class="contract">supersede</h1>

Moves an active commitment into the `superseded` business status and links it to a successor commitment.

<h1 class="contract">revokecmmt</h1>

Moves an active commitment into the `revoked` business status.

<h1 class="contract">expirecmmt</h1>

Moves an active commitment into the `expired` business status.

<h1 class="contract">submitroot</h1>

Creates a batch anchoring record after schema, policy, and external usage-authorization validation.

<h1 class="contract">linkmanifest</h1>

Links an immutable manifest hash to an open batch record.

<h1 class="contract">closebatch</h1>

Closes an open batch and prevents further mutable batch updates.

<h1 class="contract">withdraw</h1>

Transfers tokens already held by `verif` to another account.
