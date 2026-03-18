# Verification Legacy Cleanup

Use this temporary cleaner only when an old monolithic `verification` contract is already deployed
and you want to clear its legacy tables before upgrading to the new split architecture.

Legacy tables removed by the cleaner:

- `proofs`
- `paytokens`
- `wholesale`
- `nonprofit`
- `freeusage`
- `freepolicy`

## Build only the cleaner

Linux / WSL:

```bash
./scripts/build-testnet.sh verificationlegacywipe
```

PowerShell:

```powershell
./scripts/build-testnet.ps1 verificationlegacywipe
```

Expected artifacts:

- `dist/verificationlegacywipe/verificationlegacywipe.wasm`
- `dist/verificationlegacywipe/verificationlegacywipe.abi`

## Deploy cleaner to the old `verification` account

Even though the build artifact is named `verificationlegacywipe`, you deploy it to the account
that currently holds the old `verification` contract:

```powershell
cleos -u <RPC_URL> set contract verification ./dist/verificationlegacywipe -p verification@active
```

## Run cleanup in batches

```powershell
cleos -u <RPC_URL> push action verification wipeall '[50]' -p verification@active
```

Repeat until all legacy tables are empty.

## Verify cleanup

```powershell
cleos -u <RPC_URL> get table verification verification proofs
cleos -u <RPC_URL> get table verification verification paytokens
cleos -u <RPC_URL> get table verification verification wholesale
cleos -u <RPC_URL> get table verification verification nonprofit
cleos -u <RPC_URL> get table verification verification freeusage
cleos -u <RPC_URL> get table verification verification freepolicy
```

## After cleanup

Deploy the new split contracts in order:

1. deploy the new `verification` contract to account `verification`
2. deploy `managementel` to account `managementel`
3. add `eosio.code` to `managementel`
4. run the normal setup and smoke test
