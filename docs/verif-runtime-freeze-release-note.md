# `verif` Runtime Freeze Release Note

## Summary

`verif` has been reduced to the live runtime anchoring surface required by the supported payment contracts.

Removed public actions:

- `addschema`
- `updateschema`
- `deprecate`
- `setpolicy`
- `setauthsrcs`
- `withdraw`

Remaining public actions:

- `billsubmit`
- `retailsub`
- `billbatch`
- `retailbatch`

## Why This Change Was Made

The live contract already contains production-style data and no longer needs self-managed governance or treasury actions on its public surface after key burning.

The goal of this change is to:

- reduce the attack surface of `verif`
- keep the runtime limited to internal anchoring entrypoints
- preserve existing `schemas`, `policies`, `authsources`, `commitments`, `batches`, and counters

## Compatibility

Storage layout was preserved:

- no table names changed
- no field names changed
- no index names changed
- no counter layout changed

This is a runtime-surface reduction, not a table migration.

## Jungle4 Live Upgrade

Validated Jungle4 layout:

- `decentrfstor` -> `verif`
- `vadim1111111` -> `verifbill`
- `verification` -> `verifretpay`

Latest `verif` upgrade details:

- deploy transaction: `8d8d831d734b962dd22b65fa9ca0d6779d688c0840faa3b71321f69706a02a04`
- code hash before: `be66211abd84b5b006ea7e249a33ae3b7f44488b4dcea2952f49723547f894e5`
- code hash after: `976388cd22f49ece49afaf3324901f28f10a26302d7c31bcb066b403a3f3717c`

## Live Validation Result

The updated contract was tested on Jungle4 after deployment.

Validated:

- enterprise runtime path through `vadim1111111 -> decentrfstor`
- retail runtime path through `verification -> decentrfstor`
- duplicate rejection
- invalid policy rejection
- zero-hash rejection
- underpayment rejection
- wrong-token rejection

The live ABI also confirms that removed governance actions are no longer available.

Observed removal check:

- a live `setpolicy` call now fails with `Unknown action setpolicy in contract decentrfstor`

## Operator Notes

- `verif` now assumes `schemas` and `policies` are already provisioned
- `authsources` remains readable on-chain and still controls allowed internal callers
- if `authsources` is absent, `verif` still defaults to `verifbill` and `verifretpay`

## Related Docs

- [docs/contract-reference.md](/c:/projects/verification-contract/docs/contract-reference.md:1)
- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
- [docs/jungle4-validation-report.md](/c:/projects/verification-contract/docs/jungle4-validation-report.md:1)
