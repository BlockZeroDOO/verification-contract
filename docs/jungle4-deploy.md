# Jungle4 Deploy

Supported deploy model on Jungle4:

- `verif`
- `verifbill`
- optional `verifretpay` for retail traffic

## Network

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`

## Build

```bash
./scripts/build-enterprise.sh
./scripts/build-billing.sh
./scripts/build-retpay.sh
```

## Deploy

```bash
./scripts/deploy-billing-jungle4.sh
./scripts/deploy-jungle4.sh
```

Retail payment companion:

```bash
./scripts/deploy-retpay-jungle4.sh
```

## Wiring

```bash
cleos -u https://jungle4.api.eosnation.io push action verif setauthsrcs '["verifbill","verifretpay"]' -p verif@active
cleos -u https://jungle4.api.eosnation.io push action verifbill setverifacct '["verif"]' -p verifbill@active
cleos -u https://jungle4.api.eosnation.io push action verifretpay setverifacct '["verif"]' -p verifretpay@active
```

## Smoke

Enterprise:

```bash
export OWNER_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
export VERIFICATION_BILLING_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-jungle4.sh
```

Retail end-to-end:

```bash
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export RETPAY_ACCOUNT=verifretpay
export OWNER_ACCOUNT=verif
export RETPAY_OWNER_ACCOUNT=verifretpay
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-unified-retail-jungle4.sh
```
