# Ricardian Clauses

## addwhuser

Adds an account to the wholesale pricing table maintained by the contract.

## rmwhuser

Removes an account from the wholesale pricing table maintained by the contract.

## addnporg

Adds an account to the nonprofit pricing table maintained by the contract.

## rmnporg

Removes an account from the nonprofit pricing table maintained by the contract.

## setpaytoken

Creates or updates a payment token configuration, including retail price, wholesale price,
and storage price.

## rmpaytoken

Removes a payment token configuration from the contract.

## submitfree

Creates a proof record without token payment for an account registered in the nonprofit table.

## setfreecfg

Creates or updates the nonprofit free-submission policy, including the contract-wide
24-hour sponsored submission limit. Nonprofit accounts are additionally limited by a
fixed 60-second cooldown between submissions.

## withdraw

Transfers tokens held by the contract account to the specified recipient through the selected token contract.
