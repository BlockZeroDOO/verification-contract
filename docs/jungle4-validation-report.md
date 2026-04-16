# Jungle4 Validation Report

Date:

- 2026-04-16

## Scope

This report records the live Jungle4 validation of the current supported model:

- `verif`
- `verifbill`
- `verifretpay`

Validated runtime:

- `verif` is an internal-only registry
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

Operational note:

- deployment to `managementel` for `verifbill` failed with `unsatisfied_authorization`, so the live billing validation was completed on `vadim1111111`

## Smoke Coverage

The following live smoke scenarios passed:

- `scripts/smoke-test-billing.sh`
- `scripts/smoke-test-retpay.sh`
- `scripts/smoke-test-onchain.sh`
- `scripts/smoke-test-unified-retail.sh`

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

## Conclusion

The current Jungle4-validated model is:

- `verif` as the only registry
- `verifbill` as the enterprise payment contract
- `verifretpay` as the retail payment contract

Both enterprise and retail atomic flows completed successfully end-to-end on Jungle4 with contract-computed canonical request size.
