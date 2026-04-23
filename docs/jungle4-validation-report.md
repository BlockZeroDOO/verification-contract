# Jungle4 Validation Report

Date:

- 2026-04-23

## Scope

This report records the live Jungle4 validation of the current supported model:

- `verif`
- `verifbill`
- `verifretpay`

Validated runtime:

- `verif` is an internal-only registry
- `verif` exposes only `billsubmit`, `retailsub`, `billbatch`, and `retailbatch`
- `verifbill` performs atomic enterprise billing and inline anchoring
- `verifretpay` performs atomic retail payment and inline anchoring
- request size is computed by the contracts from the canonical registry request shape

## Deployed Accounts

The working Jungle4 account layout for this validation was:

- `decentrfstor` -> `verif`
- `vadim1111111` -> `verifbill`
- `verification` -> `verifretpay`

Operational test accounts:

- enterprise `payer/submitter`: `verification`
- retail `payer/submitter`: `decentrfstor`

## Deployment Result

Deployment completed successfully for:

- `verif` on `decentrfstor`
- `verifbill` on `vadim1111111`
- `verifretpay` on `verification`

Latest `verif` live upgrade:

- deploy transaction: `8d8d831d734b962dd22b65fa9ca0d6779d688c0840faa3b71321f69706a02a04`
- code hash before upgrade: `be66211abd84b5b006ea7e249a33ae3b7f44488b4dcea2952f49723547f894e5`
- code hash after upgrade: `976388cd22f49ece49afaf3324901f28f10a26302d7c31bcb066b403a3f3717c`
- on-chain ABI after upgrade exposes only the four runtime anchoring actions
- a live `setpolicy` call now fails with `Unknown action setpolicy in contract decentrfstor`

## Smoke Coverage

The following live smoke scenarios passed:

- `scripts/smoke-test-billing.sh`
- `scripts/smoke-test-retpay.sh`
- `scripts/smoke-test-onchain.sh`
- `scripts/smoke-test-unified-retail.sh`

Latest validated live inputs:

- `SCHEMA_ID = 1776342316`
- `POLICY_SINGLE_ID = 1776343316`
- `POLICY_BATCH_ID = 1776343317`
- enterprise `submitter = verification`
- retail `submitter = decentrfstor`

Validated behavior:

- enterprise token, plan, and pack configuration
- enterprise entitlement purchase
- enterprise atomic `submit`
- enterprise atomic `submitroot`
- nearest-expiry entitlement consumption
- duplicate enterprise request rejection
- zero-hash rejection
- retail token and tariff configuration
- retail atomic single transfer
- retail atomic batch transfer
- retail underpayment rejection
- retail wrong-token rejection
- retail invalid-policy rejection
- retail duplicate request rejection
- contract-computed `billable_bytes`
- contract-computed `billable_kib`

## Notes

- two smoke runs initially collided on reused `schema_id` / `policy_id` values because multiple scenarios started in the same second; rerunning them with explicit unique ids resolved the issue
- the final passing validation used unique ids per scenario and the account layout listed above
- the latest live upgrade preserved existing `schemas`, `policies`, `authsources`, `commitments`, and `batches` rows while removing the unused governance and treasury actions from the public `verif` surface

## Conclusion

The current Jungle4-validated model is:

- `verif` as the only registry
- `verifbill` as the enterprise payment contract
- `verifretpay` as the retail payment contract

Both enterprise and retail atomic flows completed successfully end-to-end on Jungle4 with contract-computed canonical request size.
