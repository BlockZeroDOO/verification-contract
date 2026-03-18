# Ricardian Clauses

## addwhuser

Adds an account to the wholesale pricing table maintained by `managementel`.

## rmwhuser

Removes an account from the wholesale pricing table maintained by `managementel`.

## addnporg

Adds an account to the nonprofit table maintained by `managementel`.

## rmnporg

Removes an account from the nonprofit table maintained by `managementel`.

## setpaytoken

Creates or updates a payment token configuration with retail and wholesale prices.
The configured token symbol and precision must exist in the token contract `stat` table.

## rmpaytoken

Removes a payment token configuration from `managementel`.

## submitfree

Creates a proof request without token payment for an account registered in the nonprofit table.
The request is checked against the 60-second nonprofit cooldown and the shared 24-hour free limit.

## setfreecfg

Creates or updates the nonprofit free-submission policy, including the contract-wide
24-hour sponsored submission limit.

## withdraw

Transfers tokens held by the `managementel` contract account to the specified recipient through
the selected token contract. The transfer does not require an active `paytokens` configuration row.
