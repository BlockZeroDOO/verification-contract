# Corporate Pricing Grid Proposal

This document proposes a starting corporate pricing grid for `verifbill`.

It is intended for:

- internal commercial planning
- initial on-chain tariff setup
- sales conversations with enterprise customers

## Pricing Basis

Assumptions:

- `1 DNLT = $0.01`
- `verif` charges for the canonical registry request size
- in normal enterprise usage, most requests will be billed as approximately `1 KiB`
- therefore `included_kib` is a practical proxy for the number of notarization operations

Reference market from the competitor analysis:

- SaaS mass market: `$0.05 - $0.50 / proof`
- Enterprise SaaS: `$0.01 - $0.10 / proof`
- Web3 API: `$0.01 - $0.05 / proof`
- private-chain / ultra-low-cost infrastructure: `$0.0005 - $0.01 / proof`

Recommended positioning for deNotary:

- cheaper than typical SaaS
- competitive with Web3 API
- not aggressively below the market floor

Target list-price range:

- `$0.008 - $0.020 / proof`

## Recommended Monthly Plans

These plans are designed to be competitive without hard dumping.

| Plan | Included KiB | Price DNLT | Price USD | Effective USD / proof |
| --- | ---: | ---: | ---: | ---: |
| `starter` | 5,000 | 100,000 DNLT | $1,000 | $0.0200 |
| `team` | 25,000 | 400,000 DNLT | $4,000 | $0.0160 |
| `business` | 100,000 | 1,300,000 DNLT | $13,000 | $0.0130 |
| `scale` | 500,000 | 5,000,000 DNLT | $50,000 | $0.0100 |
| `entplus` | 1,000,000 | 8,000,000 DNLT | $80,000 | $0.0080 |

Recommended duration for all monthly plans:

- `2,592,000` seconds (`30 days`)

## Recommended One-Time Packs

These are more expensive than monthly subscriptions on a per-proof basis and are intended for:

- burst capacity
- pilots
- seasonal overage
- pre-launch testing with real production conditions

| Pack | Included KiB | Price DNLT | Price USD | Effective USD / proof |
| --- | ---: | ---: | ---: | ---: |
| `pksmall` | 10,000 | 220,000 DNLT | $2,200 | $0.0220 |
| `pkmed` | 50,000 | 900,000 DNLT | $9,000 | $0.0180 |
| `pklarge` | 250,000 | 3,250,000 DNLT | $32,500 | $0.0130 |

## Why This Grid Works

This grid is designed to:

- stay below typical B2B SaaS proof pricing
- approach the Web3 API segment at scale
- keep enough margin for token discounts and partner incentives
- avoid signaling distressed or unsustainable pricing

Commercial interpretation:

- `starter` and `team` are onboarding plans
- `business` is the default commercial plan
- `scale` is the main high-volume plan
- `entplus` is the anchor plan for strategic enterprise contracts

## Token Sale Discounts

Because DNLT is not yet a market-priced token, deNotary can offer commercial discounts at the token sale layer without changing the public on-chain tariffs.

Recommended discount policy:

| Customer Type | Suggested Token Discount |
| --- | ---: |
| standard annual customer | 10% |
| committed enterprise customer | 15% - 20% |
| validator / strategic infrastructure partner | 25% - 35% |

Examples:

- `business` list price is `$0.013 / proof`
- with a `20%` token discount, effective price becomes about `$0.0104 / proof`
- `entplus` list price is `$0.008 / proof`
- with a `30%` token discount, effective price becomes about `$0.0056 / proof`

This means deNotary can publicly preserve a disciplined tariff ladder while privately matching or beating low-cost infrastructure competitors for strategic deals.

## Suggested Sales Positioning

Public positioning:

- enterprise-grade trustless anchoring
- predictable pricing
- lower cost than most SaaS proof providers
- no dependence on a centralized proof database

Commercial framing:

- list price starts from about `$0.02 / proof`
- enterprise volume pricing reaches about `$0.008 / proof`
- strategic customers can achieve lower effective pricing through token-sale and validator incentive programs

## `cleos` Setup Examples

These examples assume:

- contract account: `verifbill`
- token contract: `eosio.token`
- token symbol: `DNLT`

Before plans and packs:

```bash
cleos -u <rpc> push action verifbill settoken '["eosio.token","4,DNLT"]' -p verifbill@active
```

### Monthly Plans

```bash
cleos -u <rpc> push action verifbill setplan '["starter","eosio.token","100000.0000 DNLT",2592000,5000,true]' -p verifbill@active
cleos -u <rpc> push action verifbill setplan '["team","eosio.token","400000.0000 DNLT",2592000,25000,true]' -p verifbill@active
cleos -u <rpc> push action verifbill setplan '["business","eosio.token","1300000.0000 DNLT",2592000,100000,true]' -p verifbill@active
cleos -u <rpc> push action verifbill setplan '["scale","eosio.token","5000000.0000 DNLT",2592000,500000,true]' -p verifbill@active
cleos -u <rpc> push action verifbill setplan '["entplus","eosio.token","8000000.0000 DNLT",2592000,1000000,true]' -p verifbill@active
```

### One-Time Packs

```bash
cleos -u <rpc> push action verifbill setpack '["pksmall","eosio.token","220000.0000 DNLT",10000,true]' -p verifbill@active
cleos -u <rpc> push action verifbill setpack '["pkmed","eosio.token","900000.0000 DNLT",50000,true]' -p verifbill@active
cleos -u <rpc> push action verifbill setpack '["pklarge","eosio.token","3250000.0000 DNLT",250000,true]' -p verifbill@active
```

## Optional Annual Variants

If you want annual plans later, I recommend:

- same plan codes with suffixes such as `stannual`, `tmannual`, `bsannual`
- annual discount of `15% - 20%`
- longer duration instead of a larger monthly quota multiple

Example annual strategy:

- `12x` monthly quota
- `15% - 20%` lower total annual price than twelve monthly purchases

## Recommendation

Best initial rollout:

1. launch with `starter`, `team`, `business`, `scale`
2. keep `entplus` for negotiated deals
3. launch all three packs
4. preserve list-price discipline
5. use token-sale discounts and validator incentives as the real flexibility layer
