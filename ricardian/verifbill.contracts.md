<h1 class="contract">settoken</h1>

Registers or re-enables a token that can be used to purchase enterprise plans and packs.

<h1 class="contract">rmtoken</h1>

Removes an enterprise billing token when no active plan or pack depends on it.

<h1 class="contract">setplan</h1>

Creates or updates a plan definition with duration and included `KiB`.

<h1 class="contract">deactplan</h1>

Marks a plan inactive for future enterprise purchases.

<h1 class="contract">setpack</h1>

Creates or updates a usage-pack definition with included `KiB`.

<h1 class="contract">deactpack</h1>

Marks a usage pack inactive for future enterprise purchases.

<h1 class="contract">setverifacct</h1>

Configures which deployed `verif` account may consume enterprise usage authorizations after successful anchoring.

<h1 class="contract">submit</h1>

Performs atomic enterprise single-record billing and inline anchoring through `verif::billsubmit`.

<h1 class="contract">submitroot</h1>

Performs atomic enterprise batch billing and inline anchoring through `verif::billbatch`.

<h1 class="contract">use</h1>

Creates a one-time enterprise usage authorization bound to a request key and billable size.

<h1 class="contract">consume</h1>

Marks an enterprise usage authorization as consumed after a successful downstream anchoring flow and burns the matching `KiB` quota.

<h1 class="contract">cleanauths</h1>

Removes consumed or expired enterprise usage authorizations in bounded batches.

<h1 class="contract">cleanentls</h1>

Removes expired or exhausted enterprise entitlements that are no longer referenced by a live authorization.

<h1 class="contract">withdraw</h1>

Transfers tokens already held by `verifbill` to another account.
