# Enterprise Verification Deploy

This runbook covers deployment of the enterprise pair:

- `verif`
- `verifbill`

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifbill`, and `verifretpay`
- `C:\projects\deNotary` owns the off-chain backend

## Build

```bash
./scripts/build-enterprise.sh
./scripts/build-billing.sh
```

## Deploy

```bash
./scripts/deploy-billing-denotary.sh
./scripts/deploy-denotary.sh
```

Or on Jungle4:

```bash
./scripts/deploy-billing-jungle4.sh
./scripts/deploy-jungle4.sh
```

## Wiring

```bash
cleos -u <rpc> push action verif setauthsrcs '["verifbill","verifretpay"]' -p verif@active
cleos -u <rpc> push action verifbill setverifacct '["verif"]' -p verifbill@active
```

Set `verifretpay::setverifacct` only when the retail payment contract is deployed in the same environment.
