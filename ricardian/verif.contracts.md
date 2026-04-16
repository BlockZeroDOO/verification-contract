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

<h1 class="contract">billsubmit</h1>

Creates a single anchored commitment through the contract-only enterprise path, callable only by the configured `verifbill` account.

<h1 class="contract">retailsub</h1>

Creates a single anchored commitment through the contract-only retail path, callable only by the configured `verifretpay` account.

<h1 class="contract">submitroot</h1>

Creates a finalized batch anchoring record with embedded manifest hash after schema, policy, and external usage-authorization validation.

<h1 class="contract">billbatch</h1>

Creates a finalized batch anchoring record through the contract-only enterprise path, callable only by the configured `verifbill` account.

<h1 class="contract">retailbatch</h1>

Creates a finalized batch anchoring record through the contract-only retail path, callable only by the configured `verifretpay` account.

<h1 class="contract">withdraw</h1>

Transfers tokens already held by `verif` to another account.
