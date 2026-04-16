<h1 class="contract">settoken</h1>

Registers or re-enables a token that can be used to purchase enterprise plans and packs.

<h1 class="contract">rmtoken</h1>

Removes an enterprise billing token when no active plan or pack depends on it.

<h1 class="contract">setplan</h1>

Creates or updates a plan definition with duration and single or batch quotas.

<h1 class="contract">deactplan</h1>

Marks a plan inactive for future enterprise purchases.

<h1 class="contract">setpack</h1>

Creates or updates a usage-pack definition with single or batch units.

<h1 class="contract">deactpack</h1>

Marks a usage pack inactive for future enterprise purchases.

<h1 class="contract">grantdelegate</h1>

Allows a submitter account to consume enterprise usage on behalf of a payer.

<h1 class="contract">revokedeleg</h1>

Disables a delegated submitter mapping for a payer.

<h1 class="contract">use</h1>

Consumes one enterprise quota unit and creates a one-time usage authorization bound to a request key.

<h1 class="contract">consume</h1>

Marks an enterprise usage authorization as consumed after a successful downstream anchoring flow.

<h1 class="contract">withdraw</h1>

Transfers tokens already held by `verifbill` to another account.
