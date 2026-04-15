# Verification Enterprise/Retail Technical Roadmap

## Purpose

This document translates the enterprise/retail split plan into a concrete repository-level implementation roadmap.

Final deployment targets:

- enterprise contract/account: `verifent`
- retail contract/account: `verifretail`

Recommended future enterprise billing target:

- billing contract/account: `verifbill`

It focuses on:

- target file layout
- refactor boundaries
- ABI ownership
- deployment split
- testing split
- recommended execution order

## Current Starting Point

The repository currently contains one canonical contract:

- `include/verification.hpp`
- `include/request_key.hpp`
- `src/verification.cpp`
- `ricardian/verification.contracts.md`
- `ricardian/verification.clauses.md`

This contract already represents the cleanest base for the future enterprise variant because legacy payment flow has already been removed.

## Target Repository Structure

Recommended future structure:

```text
include/
  request_key.hpp
  verification_tables.hpp
  verification_validators.hpp
  verification_core.hpp
  verification_enterprise.hpp
  verification_retail.hpp
  verification_billing.hpp

src/
  verification_core.cpp
  verification_enterprise.cpp
  verification_retail.cpp
  verification_billing.cpp

ricardian/
  verification_enterprise.contracts.md
  verification_enterprise.clauses.md
  verification_retail.contracts.md
  verification_retail.clauses.md
  verification_billing.contracts.md
  verification_billing.clauses.md

scripts/
  build-enterprise.sh
  build-retail.sh
  build-billing.sh
  deploy-enterprise-*.sh
  deploy-retail-*.sh
  deploy-billing-*.sh
  smoke-test-enterprise-*.sh
  smoke-test-retail-*.sh
  smoke-test-billing-*.sh
```

## File Ownership Plan

### Keep As-Is

- `include/request_key.hpp`

This remains a shared helper and should not be duplicated.

### Create Shared Contract Headers

#### `include/verification_tables.hpp`

Should own all shared table definitions:

- `kyc`
- `schemas`
- `policies`
- `commitments`
- `batches`
- `counters`

Goal:

- keep the data model shared between enterprise and retail

#### `include/verification_validators.hpp`

Should own shared helper functions and validation rules:

- checksum validation
- request key validation
- KYC and policy guard helpers
- shared business-status guards

Goal:

- prevent validator divergence between the two contracts

#### `include/verification_core.hpp`

Should define a shared core class or shared implementation surface for:

- schema operations
- policy operations
- KYC operations
- commitment lifecycle
- batch lifecycle

Goal:

- centralize business logic and make contract wrappers thin

### Create Enterprise Wrapper

#### `include/verification_enterprise.hpp`

Enterprise wrapper-specific contract declaration.

Should expose:

- governance actions
- enterprise `submit`
- enterprise `submitroot`
- lifecycle actions

Should not expose any token payment surface.

#### `src/verification_enterprise.cpp`

Thin wrapper around shared core.

Responsibilities:

- EOSIO action dispatch
- enterprise-specific gating
- any enterprise-only admission rules

### Create Retail Wrapper

#### `include/verification_retail.hpp`

Retail wrapper-specific contract declaration.

Should expose:

- all shared governance and lifecycle actions that retail needs
- retail payment actions or notification entrypoints

Additional retail-only tables may live here or in a separate retail billing header if cleaner.

#### `src/verification_retail.cpp`

Thin wrapper around shared core plus retail payment admission layer.

Responsibilities:

- token notification handling
- payment receipt creation
- exact tariff validation
- one-time consumption before `submit` or `submitroot`

### Replace Monolithic Contract

#### `src/verification.cpp`

Planned outcome:

- temporary compatibility file during refactor
- then removed after enterprise wrapper becomes canonical

#### `include/verification.hpp`

Planned outcome:

- temporary compatibility wrapper
- then replaced or deprecated once enterprise and retail headers are adopted

## Retail-Specific Additions

Recommended retail-only headers if the wrapper becomes too large:

- `include/verification_retail_billing.hpp`
- `include/verification_retail_tables.hpp`

Retail-only tables may include:

- accepted tokens
- tariff config
- payment receipts

Retail-only helpers may include:

- transfer memo parsing
- exact payment matching
- payment receipt consume logic

## Enterprise Billing Additions

Recommended billing-specific files:

- `include/verification_billing.hpp`
- `include/verification_billing_tables.hpp`
- `src/verification_billing.cpp`

Recommended billing-only tables:

- accepted tokens
- plan definitions
- pack definitions
- entitlements
- delegates
- usage authorizations

Recommended billing-only helpers:

- purchase memo parsing
- entitlement matching
- delegate checks
- one-time usage authorization creation
- usage consumption

## Ricardian Split

Current Ricardian files should eventually be split into:

- `ricardian/verification_enterprise.contracts.md`
- `ricardian/verification_enterprise.clauses.md`
- `ricardian/verification_retail.contracts.md`
- `ricardian/verification_retail.clauses.md`

Reason:

- enterprise and retail product promises are materially different
- payment semantics must not appear in enterprise documentation

## Build System Changes

### CMake

Current `CMakeLists.txt` should evolve to build two WASM targets:

- `verification_enterprise`
- `verification_retail`

Likely shape:

- one shared library or shared source list for the core
- two contract targets pointing to different wrapper entry files

### Build Scripts

Current generic scripts should be split or parameterized for clarity.

Recommended script set:

- `scripts/build-enterprise.sh`
- `scripts/build-enterprise.ps1`
- `scripts/build-retail.sh`
- `scripts/build-retail.ps1`

Optional later:

- retain one generic build script with explicit contract target argument

## Deployment Split

Need separate deployment surfaces for:

- enterprise contract accounts
- retail contract accounts

Recommended docs and scripts:

- `docs/enterprise-deploy.md`
- `docs/retail-deploy.md`
- `scripts/deploy-enterprise-denotary.sh`
- `scripts/deploy-enterprise-jungle4.sh`
- `scripts/deploy-retail-denotary.sh`
- `scripts/deploy-retail-jungle4.sh`

## Testing Split

### Enterprise Tests

Should cover:

- schema and policy governance
- KYC flow
- single submit
- batch submit
- lifecycle actions
- no token payment surface

Recommended files:

- `scripts/smoke-test-enterprise.sh`
- `scripts/smoke-test-enterprise-jungle4.sh`

### Retail Tests

Should cover:

- exact payment
- wrong token rejection
- underpayment rejection
- overpayment rejection
- replay rejection
- duplicate consume rejection
- atomic `transfer + submit`
- atomic `transfer + submitroot`

Recommended files:

- `scripts/smoke-test-retail.sh`
- `scripts/smoke-test-retail-jungle4.sh`

## Recommended Refactor Order

### Stage 1. Prepare Shared Building Blocks

Files to create first:

- `include/verification_tables.hpp`
- `include/verification_validators.hpp`
- `include/verification_core.hpp`

Files to update:

- `src/verification.cpp`
- `include/verification.hpp`

Goal:

- move shared structures out of the monolith without changing behavior

### Stage 2. Extract Shared Core Implementation

Files to create:

- `src/verification_core.cpp`

Files to update:

- `src/verification.cpp`

Goal:

- move shared implementation out while keeping the current contract functional

### Stage 3. Introduce Enterprise Wrapper

Files to create:

- `include/verification_enterprise.hpp`
- `src/verification_enterprise.cpp`

Files to update:

- `CMakeLists.txt`
- build scripts

Goal:

- compile enterprise contract from the extracted core

### Stage 4. Rebind Existing Docs And Smoke To Enterprise

Files to update:

- current deploy docs
- current smoke scripts
- current Ricardian files

Goal:

- make enterprise the explicit successor of the current verification contract

### Stage 5. Introduce Retail Wrapper Shell

Files to create:

- `include/verification_retail.hpp`
- `src/verification_retail.cpp`

Potential support files:

- `include/verification_retail_tables.hpp`
- `include/verification_retail_billing.hpp`

Goal:

- compile a retail contract with the same shared verification core

### Stage 6. Add Retail Atomic Payment

Files to update:

- `src/verification_retail.cpp`
- retail headers
- retail Ricardian

Goal:

- support atomic `transfer + submit`
- support atomic `transfer + submitroot`

### Stage 7. Split Deployment And Smoke Surface

Files to create:

- enterprise deploy scripts
- retail deploy scripts
- enterprise smoke scripts
- retail smoke scripts

Goal:

- independent release and validation pipelines

## ABI Ownership Rules

### Enterprise ABI

Must remain stable around:

- governance
- KYC
- schemas
- policies
- single and batch anchoring
- lifecycle actions

Must not reintroduce:

- token acceptance
- payment receipts
- retail-only tariff tables

### Retail ABI

Will extend the shared verification surface with:

- accepted token configuration
- tariff configuration
- payment receipt mechanics

Need to keep the payment surface clearly isolated from enterprise ABI.

### Billing ABI

Should own:

- token acceptance
- plan and pack governance
- enterprise purchase flow
- delegate mapping
- usage authorization flow

Should not own:

- anchoring state
- schema tables
- policy tables
- commitments
- batches

## Recommended First Real Coding Slice

The best first coding slice is:

1. extract `verification_tables.hpp`
2. extract `verification_validators.hpp`
3. extract `verification_core.hpp`
4. move shared code into `verification_core.cpp`
5. make the existing contract compile unchanged

This gives a low-risk refactor foundation before introducing new contract names and retail payment semantics.

## Short-Term Working Assumptions

Until implementation starts, assume:

- current `verification` behavior maps to enterprise
- retail pricing starts with exact fixed pricing
- retail batch pricing is fixed per batch in the first version
- enterprise billing will be added as separate `verifbill`, not inside `verifent`

## Deliverables Checklist

The split should be considered structurally complete when the repository contains:

- shared core headers and source
- separate enterprise wrapper
- separate retail wrapper
- split Ricardian
- split build targets
- split deploy scripts
- split smoke suites
- updated contract-only documentation
- documented enterprise billing architecture
