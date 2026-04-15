<h1 class="contract">regnode</h1>

Registers a DFS node with ownership, role, endpoints, and public key metadata.

<h1 class="contract">updatenode</h1>

Updates mutable DFS node metadata for an existing node.

<h1 class="contract">suspendnode</h1>

Suspends an existing DFS node.

<h1 class="contract">retirenode</h1>

Retires an existing DFS node from active service.

<h1 class="contract">requestunstk</h1>

Starts the unstake cooldown flow for a node stake position.

<h1 class="contract">withdrawstk</h1>

Withdraws stake after the configured cooldown period has completed.

<h1 class="contract">setprice</h1>

Creates or updates the storage price offer for a DFS node.

<h1 class="contract">settoken</h1>

Creates or updates an accepted token configuration for DFS flows.

<h1 class="contract">rmtoken</h1>

Removes an accepted token configuration when no protected live state depends on it.

<h1 class="contract">setpolicy</h1>

Creates or updates the DFS pricing and settlement policy.

<h1 class="contract">claimrevenue</h1>

Withdraws available settled revenue for an owner account.

<h1 class="contract">mkstorquote</h1>

Creates a bounded storage payment quote that binds `payment_reference` to payer, manifest, token, amount, and expiry.

<h1 class="contract">cancelquote</h1>

Cancels an open storage payment quote before it is consumed by an incoming transfer.

<h1 class="contract">settle</h1>

Finalizes a storage payment receipt into distributable balances and protocol fee accounting.
