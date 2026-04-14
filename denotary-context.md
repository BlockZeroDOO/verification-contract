# Accounts

A deNotary account is a digital container for holding deNotary tokens, resources, permissions, and more. 

## Token mapping

This document follows a strict token notation:

- `DNLT` is the native token symbol for the deNotary chain and must be used in all deNotary-specific examples.
- `EOS` is kept only for Jungle4 or other EOS public testnet examples.
- Technical references such as `EOSIO`, legacy `EOS...` public key prefixes, and proper names like `EOS Rio` remain unchanged.

Smart Contracts are also deployed on top of accounts, and the account owner can control the smart contract unless
control is relinquished.

## Account names

deNotary accounts have human-readable names. 

However, in order to keep account names efficient on the blockchain, a few restrictions apply: 

* All characters must be lowercase
* Every name must be 12 characters long (or less with a suffix/premium name)
* Only letters `a-z`, numbers `1-5`, and period (`.`) are supported characters. 
* Names cannot start with a number or a period. 
* Names cannot end with a period.

Periods have a special meaning for deNotary accounts. They specify that an account has a **suffix** (similar to a top-level domain like .com), also known as a **premium name**. Accounts with a suffix can only be created by the **suffix owner**. 

For instance, if someone owns the suffix `.bar` then only that person can create `foo.bar`. 
 
### Regex Validation

The following regex can be used to validate a deNotary account name: 

```regex
(^[a-z1-5.]{1,11}[a-z1-5]$)|(^[a-z1-5.]{12}[a-j1-5]$)
```

## Public/private keys

Every deNotary account is ultimately controlled by a key pair (public and corresponding private key).
While the public key is used to identify the account on the blockchain and can be publicly known, the private key which is used 
to sign each transaction must be kept secret at all times.

If you lose your private key, you will lose access to your account and all of its assets, smart contracts, and any other
data associated with it.

Examples of private and public keys:

| Type              | Key |
|-------------------| --- |
| Private Key       | `5KSdyAiFzYQAtBKDBKCCF28KMMhZ4EmXUxSg8B3nSkHKutT15rY` |
| Public Key        | `PUB_K1_5d7eRKgCCiEdsbBdxxnZdFWnGYS64uWZPZgTcTU1xnB2aESxqR` |
| Legacy Public Key | `EOS5d7eRKgCCiEdsbBdxxnZdFWnGYS64uWZPZgTcTU1xnB2cq4JMD` |


## Permissions system

deNotary offers extra security mechanisms for accounts out of the box, using what we call the *permissions system*.

Each account has a set of hierarchical permissions that control what that account can do, and comes with two base permissions by default. These two permissions cannot be removed as they are required for your account to function properly. 

The mandatory permissions are `owner` and `active`.

A permission can only ever change what controls it (keys or accounts) or what controls its children. It can never change what controls its parent.

![Who can change permissions?](image-accts_who_can_change_permissions.png)


What controls a permission is either a **public key** or another **account**. 
This allows for the creation of complex account control structures, where multiple parties may control a single account 
while still having full autonomy over their own account's security. 

Take the following diagram as an example, where the account `alice` is controlled by both `bob` and `charlie`, 
while `charlie` is _also_ controlled by `tom`. 

But remember, all accounts are eventually controlled by keys. 


![Delegated account ownership](image-accts_delegated_account_ownership.png)


You can add custom permissions underneath the `active` permission which allows you to limit that permission's access to 
only a specific contract's action (callable function). That permission will then only ever be able to interact with the 
contract action you specified. 

This means you are able to create granular access permissions across accounts and have hierarchical ownership and 
usage of them. 


![Custom permissions](image-accts_custom_permissions.png)


Most importantly, the permission system has built-in support for multi-signature transactions (transactions that require 
multiple parties to sign them). Every linked account or key associated with a permission has a **weight** assigned to it, 
and the permission itself has a **threshold**. 

As you can see in the example below, `bob` alone does not have enough power to sign using the `active` permission. 
He needs either `charlie` or `jenny` to co-sign with him for any transaction that `alice@active` makes. On the other 
hand, `charlie` and `jenny` cannot sign a transaction alone, they need `bob`. 


![Weights and thresholds](image-accts_weights_and_thresholds.png)


## Smart contracts

Smart Contracts allow you to add functionality to an account. They can be anything 
from simple things like a todo application to a fully-fledged RPG game running entirely on the blockchain. 

Every account has the ability to have one single smart contract deployed to it, however, that smart contract can be 
updated and replaced at will. 


## Creating accounts costs deNotary

Because RAM is a limited resource, creating an account requires you to spend DNLT to buy the RAM needed to store the
account's data. This means that in order to create an account, someone else who already has an account must
create it for you.

Most deNotary wallets will allow you to create an account for yourself, but will require you to pay for the RAM needed to
store your account. Some wallets will pay for the RAM for you like apps deNotary Wallet or BlockZero Wallet.

## Relinquishing ownership of an account

Upgrade-ability has significant benefits for smart contract development, but isn't always wanted. 
At some point, the community you are building for might request that you relinquish control of the smart contract, and make 
it immutable, or semi-immutable.

You have a few options to achieve that goal.

> рџ’Ђ **Don't forget the code permission!**
>
> If you relinquish the account's ownership, do not forget to keep the `eosio.code` permission
> on the account's `active` permission. Otherwise, the account will be unable to execute any inline actions on the blockchain, 
> which might **kill your contract**.

### NULL account

You may set the contract account's owner and active permissions to `eosio.null@active`. This is a `NULL` account that is specifically designed for these purposes. It has no private key or owner. 

This is a good option if you want to **burn** control of this account **forever**.


### Producer controlled

Alternatively, you may set the contract account's `owner` and `active` permissions to three different types of producer-controlled (network consensus-controlled) accounts, so that if there is ever an issue with this contract you can request the help of the producers to upgrade the contract. 

This is a good option if you are dealing with intricate and complex contracts that might have bugs that could impact the users negatively. 

#### gf.prods

The `gf.prods` account is controlled by в…”+1 of the actively producing producers on the network. This means that if there are 21 active producers then you would need 15 of them to sign off on all upgrades.

#### gf.major

The `gf.major` account is controlled by ВЅ+1, meaning that if there are 30 active producers then you would need 16 of them to sign off on all upgrades.

#### gf.minor

The `gf.minor` account is controlled by в…“+1, meaning that if there are 30 active producers, then you would need 11 of them to sign off on all upgrades.

# Decentralization

Decentralization means giving power to many people instead of just one group. For example, with blockchain technology, 
there's no one person or group that controls everything. Instead, the network is looked after by many people 
who work together to keep it safe and reliable.

### Decentralization is a spectrum

Though the determination of something being centralized versus decentralized is binary,
the degree of decentralization is not. Decentralization is a spectrum, and the degree of
decentralization can be measured by the number of nodes in the network. The more nodes
in the network, the more decentralized it is. 

This does not mean that a network with more nodes is more secure than a network with fewer
nodes. In most decentralized networks nodes group together to form a "pool" of nodes that
work together to secure the network. In this case, the number of pools in the network is
a better measure of decentralization than the number of nodes.

## Why it matters

Decentralized systems are typically more resilient, fault-tolerant, secure, and transparent than centralized systems. 
Because there is no single entity running and controlling the network, there is also no single point of failure. 
The network can continue to function to the standards that its users expect even if some nodes are compromised or go offline.

This makes it much more difficult for bad actors to manipulate or corrupt the system.

In addition, decentralization can enable greater innovation and collaboration. Because the network is open and 
accessible to anyone, it can be used to develop new applications and services that would not be possible in a 
centralized system.

## What is blockchain

Blockchain is a type of decentralized distributed ledger technology that is used to maintain a secure and tamper-proof 
record of transactions. It consists of a chain of blocks, where each block contains a set of transactions that have 
been verified and added to the chain.

In a blockchain network, the ledger is maintained by a distributed network of nodes that work together to validate 
transactions and ensure the security of the network. Each node in the network has a copy of the ledger, and block producing 
nodes must agree on the contents of new blocks being added to the ledger. 

One of the key features of blockchain technology is that it is immutable, meaning that once a transaction has been 
added to the ledger, it cannot be modified or deleted. This provides a high degree of transparency and accountability, 
as all transactions are recorded in a permanent and tamper-proof manner.

Blockchain technology has a wide range of potential applications, from financial services and supply chain management 
to voting and identity verification.
# Consensus

Consensus is the fundamental process in blockchain technology by which a distributed network of 
nodes reaches agreement on the state of the ledger. Every time a new block is added to the chain,
the nodes must agree on the contents of the block. This is done by a consensus algorithm.

## What is a consensus algorithm?

A consensus algorithm is a rigid set of rules that are used to ensure that all nodes on the 
network agree on the current state of the ledger. These rules must be deterministic, meaning
that they will always produce the same result given the same input. This is important because
it ensures that all nodes on the network will reach the same conclusion about the state of the
blocks being applied to the blockchain.

There are different types of consensus algorithms used in blockchain networks, such as proof-of-work (PoW), 
proof-of-stake (PoS), delegated proof-of-stake (DPoS), and more. Each algorithm has its own unique set of 
rules and incentives for how nodes on the network participate in reaching consensus.


## What consensus algorithms are used in deNotary?

deNotary uses a delegated proof-of-stake (DPoS) consensus algorithm. 

Token holders elect a group of block producers who are responsible for maintaining the network and reaching consensus 
on new blocks. These block producers are incentivized to act honestly, as they can be voted out if they don't perform 
their duties properly. This system is designed to be more efficient than PoW, as it doesn't require as much computational 
power to maintain the network.

This allows deNotary to be more efficient and greener than other blockchains that use consensus algorithms like proof-of-work.

### Block producers

Block producers in deNotary are nodes in the network that are responsible for maintaining the network and reaching consensus on new blocks. At any given time, there are 16 active block producers and a long list of backup block producers that are ready to step in if one of the active block producers goes offline. The selection of active block producers is randomly selected from the full list of block producers every 192 blocks. A new block producer is also randomly selected every 12 blocks to produce the next batch of blocks.
# Cryptography

Cryptography is the practice of using mathematical algorithms to secure information and communications. 
It is a fundamental part of modern technology and plays an integral role in blockchain technology.

## How is cryptography used in a blockchain?

All interactions with a blockchain are secured using cryptography. This prevents the interactions from being tampered with or altered.
Blocks that make up the blockchain are also signed by the nodes that produce them, which allows other nodes to verify
that they came from a valid source.

## What are hashes?

Hashes are unique digital fingerprints generated from input data using complex mathematical algorithms. 
Hashes are one-way functions, which means that it's practically impossible to reverse-engineer the input data from the hash output.

## What are keys?

There are two types of keys used in blockchain technology: public keys and private keys.

The two keys are directly linked to each other, but you can only derive the public key from the private key, not the other way around.
This means that you can share your public key with others safely, but should **never** share your private key with anyone.

### Public Keys

Public keys are like your digital address. They are used to identify you on a blockchain, and can be shared with others safely.

### Private Keys

Private keys are like your digital pen. They can sign information to prove that it came from you, and the signature can be 
traced back to your public key. Private keys should be kept secret at all times, as anyone who has access to your private key
can sign transactions on your behalf, effectively stealing your identity (and everything you own on the blockchain).


## What are signatures?

Signatures are the backbone of blockchain security. They are used to prove that a transaction came from a specific account,
and that the transaction has not been tampered with. If someone tried to alter the data of a transaction, the signature would
become invalid and the transaction would be rejected by the network.

## What is encryption?

Encryption is the process of encoding information so that only authorized parties can access it. It is used to protect sensitive
data which is stored on private networks. You use encryption every day without noticing it every time you visit a website. 
Even this website uses encryption to protect your connection so that no one can intercept the data as it comes from the server to 
your browser and vice versa.

> вљ  **Warning:**
> 
> Never store encrypted data on a blockchain if it contains sensitive information. Blockchains are public by nature, and anyone
> can view the contents of a transaction. This means that any encrypted data stored on a blockchain can be viewed by anyone.
> Encryption algorithms become obsolete over time as computers become more powerful, so it is innevitable that the data will
> eventually be decrypted and exposed to the public.
# Transactions and Blocks

Transactions and blocks are fundamental pieces of a blockchain. Understanding how they work is essential to
understanding how a blockchain functions.

## What are transactions?

When you want to interact with a blockchain you submit a transaction to the network, which is then processed by the network
and added to the blockchain via blocks. Transactions are made up of **actions**.

## What are actions?

Actions are the smallest unit of work in deNotary. Each transaction include one or more actions within it. The ability to include
multiple actions within a transactions allows you to perform atomic operations across multiple smart contracts. 
Actions are executed in the order they are included in the transaction, and if any action fails the entire transaction is rolled back.

## What are blocks?

Blocks are a collection of transactions that are grouped together and added to the blockchain. Each block contains a 
unique fingerprint, or hash, which is created using the transactions contained within the block, as well other information
that links the current block and the previous blocks together. 

This creates a chain of blocks, or a blockchain, that cannot be altered or tampered with. Any change to a block would change
its hash, which would break the chain of blocks and make it clear that the data has been tampered with.
# Smart Contracts

A smart contract is simply an application that lives on the blockchain. It includes access to the blockchain's
state and all the other smart contracts that are deployed on the blockchain. It can read and write data to the blockchain, 
and it can call other smart contracts to perform the actions that they expose.

Each contract is deployed to a specific `account` on the blockchain. When you interact
with that contract you do so by calling actions on that account.

## What can I do with a smart contract?

Smart contracts can be used for a variety of purposes, such as creating and executing financial transactions, 
verifying the authenticity or owner of a piece of data, or enforcing the terms of an agreement between two parties.

For example, a smart contract could be used to automatically execute the transfer of a house from one person to another
once the terms of the sale have been met. The smart contract would hold the funds from the buyer, and the title to the house
from the seller. Once both the funds and the title have been transferred to the smart contract, the smart contract would
automatically transfer the title to the buyer and the funds to the seller.

What a smart contract can do, is entirely up to your imagination.

## Are smart contracts immutable?

In deNotary, smart contracts have the _possibility_ of being immutable, but it is not the default.

As long as you retain control of the account that the smart contract is deployed to, you may update the smart contract
at any time. This is useful for fixing bugs, or adding new features to your smart contract.

If you want to make your smart contract immutable, you can give up ownership of that account. Once you do that, you will
no longer be able to update the smart contract. This is useful for smart contracts that you want to ensure will never change,
which provides extra security and peace of mind for your users.

## What is a dApp?

A dApp is a decentralized application that runs on a blockchain. It is similar to a traditional application,
but instead of running on a single server it runs on a distributed network of nodes that work together to maintain
the application and ensure its security.




# Web3

Web3 is a shift in the way we use the internet. 

Let's look at a bit of history to understand how web3 is changing the landscape of modern applications.

## Web1

The first version of the web was a read-only web. Every site on the internet was a static site, meaning that 
it was mostly text for you to read. There might have been an input form here and there where you could submit
information, but that was about it.

You did not have a way to create content for the web. In order to create content, you had to be a web developer
and know how to write code.

> Web 1 was a place to read and consume digital information.

## Web2

The web you know today is a read-write web. You can read content, but you can also create content. You can create an 
account on a variety of sites and create content for the web directly from your browser, which will then be distributed
to the rest of the world.

This change let the internet explode with content as anyone could create content for the web.

> Web2 is a place to read, consume, and create digital information.

## Web3

Web3 is a read-write-own web. You can read content, create content, and own content. Ownership comes with a variety of
other features like governance and monetization, and also requires certain features like decentralization, transparency, and 
immutability.

Web3 is a shift in the way we use the internet. It is a shift from centralized services, ownership, and control to
decentralized alternatives. It is a shift from a few companies owning and controlling the internet to a community of
users owning and controlling the internet.

> Web3 is a place to read, consume, create, and own digital information.


# Resources

The deNotary blockchain relies on two system resources: `CPU` and `RAM`. Every deNotary account needs system 
resources to interact with smart contracts deployed on the blockchain.

### RAM

RAM, just like in a computer, is a limited resource. It is a fast memory storage space that is used by the blockchain to store data.
Unlike your computer which has eventual persistence to a hard drive, the deNotary blockchain stores all of its data in RAM.

Because of this, RAM is a very limited and in-demand resource. Every piece of state data that is stored on the blockchain
must be stored in RAM. This includes account balances, contract code, and contract data.

RAM can be purchased by users on the deNotary blockchain. The price of RAM is regulated by consensus through the eosio system smart contract.

### CPU

CPU is a system resource that provides processing power to blockchain accounts. When a transaction is executed on the 
blockchain, it consumes CPU. To ensure transactions are completed successfully, the payer account must 
have enough CPU allocated to it. 

The amount of CPU available to an account is measured in microseconds.

### Buying RAM & CPU

The `eosio` system contract provides the `billuserres` action to buy `RAM` & `CPU`.

### Want to know how CPU is calculated?

Transactions executed by the blockchain contain one or more actions. Each transaction must consume an amount of CPU
within the limits predefined by the minimum and maximum transaction CPU usage values. For deNotary these limits
are set in the blockchain's configuration. You can find out these limits by running the following command and consult
the `min_transaction_cpu_usage` and the `max_transaction_cpu_usage` which are expressed in microseconds.

For accounts that execute transactions, the blockchain calculates and updates the remaining resources with each block before each transaction is executed. When a transaction is prepared for execution, the blockchain determines whether the payer account has enough CPU to cover the transaction execution. To calculate the necessary CPU, the node that actively builds the current block measures the time to execute the transaction. If the account has enough CPU, the transaction is executed; otherwise it is rejected. For technical details please refer to the following links:

* <a href="https://github.com/AntelopeIO/leap/blob/a4c29608472dd195d36d732052784aadc3a779cb/libraries/chain/include/eosio/chain/config.hpp#L66" target="_blank" rel="noreferrer noopener">The CPU configuration variables</a>
* <a href="https://github.com/AntelopeIO/leap/blob/e55669c42dfe4ac112e3072186f3a449936c0c61/libraries/chain/controller.cpp#L1559" target="_blank" rel="noreferrer noopener">The transaction initialization</a>
* <a href="https://github.com/AntelopeIO/leap/blob/e55669c42dfe4ac112e3072186f3a449936c0c61/libraries/chain/controller.cpp#L1577" target="_blank" rel="noreferrer noopener">The transaction CPU billing</a>
* <a href="https://github.com/AntelopeIO/leap/blob/a4c29608472dd195d36d732052784aadc3a779cb/libraries/chain/transaction_context.cpp#L381" target="_blank" rel="noreferrer noopener">The check of CPU usage for a transaction</a>

### Want to know how the RAM price is calculated?

The necessary RAM needed for a smart contract to store its data is calculated from the used blockchain state.

As a developer, to understand the amount of RAM your smart contract needs, pay attention to the data structure underlying the multi-index tables your smart contract instantiates and uses. The data structure underlying one multi-index table defines a row in the table. Each data member of the data structure corresponds with a row cell of the table.
To approximate the amount of RAM one multi-index row needs to store on the blockchain, you have to add the size of the type of each data member and the memory overheads for each of the defined indexes, if any. Find below the overheads defined by the deNotary code for multi-index tables, indexes, and data types:

* <a href="https://github.com/AntelopeIO/leap/blob/f6643e434e8dc304bba742422dd036a6fbc1f039/libraries/chain/include/eosio/chain/contract_table_objects.hpp#L240" target="_blank" rel="noreferrer noopener">Multi-index RAM bytes overhead</a>
* <a href="https://github.com/AntelopeIO/leap/blob/a4c29608472dd195d36d732052784aadc3a779cb/libraries/chain/include/eosio/chain/config.hpp#L109" target="_blank" rel="noreferrer noopener">Overhead per row per index RAM bytes</a>
* <a href="https://github.com/AntelopeIO/leap/blob/a4c29608472dd195d36d732052784aadc3a779cb/libraries/chain/include/eosio/chain/config.hpp#L108" target="_blank" rel="noreferrer noopener">Fixed overhead shared vector RAM bytes</a>
* <a href="https://github.com/AntelopeIO/leap/blob/a4c29608472dd195d36d732052784aadc3a779cb/libraries/chain/include/eosio/chain/config.hpp#L110" target="_blank" rel="noreferrer noopener">Overhead per account RAM bytes</a>
* <a href="https://github.com/AntelopeIO/leap/blob/a4c29608472dd195d36d732052784aadc3a779cb/libraries/chain/include/eosio/chain/config.hpp#L111" target="_blank" rel="noreferrer noopener">Setcode RAM bytes multiplier</a>
* <a href="https://github.com/AntelopeIO/leap/blob/9f0679bd0a42d6c24a966bb79de6d8c0591872a5/libraries/chain/apply_context.cpp#L725" target="_blank" rel="noreferrer noopener">RAM usage update function</a>



# Advanced Token Contract
## base.token

{% note alert %}

This smart contract is presented here as an example, do not use it for production without prior verification.

{% endnote %}

If you don't have a local deNotary node installed, use the deployment tools at docs.deNotary.io 

- Mainnet <a href="https://explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- Testnet <a href="https://dev-explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- For quick deployment to a test network, use the <a href="https://deploy.deNotary.io" target="_blank" rel="noreferrer noopener">Web Deploy</a> tools  
- You can read more about this here [Quick Start](/quick-start)  

## Overview
base.token is an advanced smart contract that implements a standard fungible token, similar to eosio.token, with additional features:

Account blacklisting: Prevent selected accounts from token operations.

Staking: Lock tokens on accounts for governance, DeFi, or utility.

Full ERC-20вЂ“like interface: Including issue, retire, transfer, open/close, and on-chain supply/balance lookups.

This contract is suitable for tokens requiring compliance, enhanced security, or staking utility directly in their core implementation.

Features
Create, Issue, Retire, Transfer: Standard fungible token operations.

Blacklisting: Prevent specific accounts from receiving, sending, or otherwise interacting with tokens.

Staking: Lock tokens to prevent their transfer, for DeFi or other advanced tokenomics.

Open/Close Account Rows: RAM management for efficient DApps.

Multi-index Tables: All balances, supply, staked amounts, and blacklist are transparently stored on chain.

Strict Validations: Extensive checks for supply, balances, staked logic, and memo sizes.

## Actions
create
Create a new token (symbol/precision/max supply/issuer).

```sh
cleos push action base.token create '["issueracc", "1000000.0000 MYT"]' -p base.token
```

### issue
Issue (mint) tokens to the issuer account.
Note: Only the issuer can issue tokens, and only to itself.

```sh
cleos push action base.token issue '["issueracc", "1000.0000 MYT", "Initial supply"]' -p issueracc
```

### retire
Burn (destroy) tokens from circulation.
Only issuer may retire tokens.

```sh
cleos push action base.token retire '["100.0000 MYT", "burn"]' -p issueracc
```

### transfer
Send tokens between accounts.

```sh
cleos push action base.token transfer '["alice", "bob", "25.0000 MYT", "For coffee"]' -p alice
```

### open
Create a zero-balance row for an account (to pay RAM in advance, e.g., for DApp onboarding).

```sh
cleos push action base.token open '["bob", "4,MYT", "alice"]' -p alice
```

### close
Remove a zero-balance row for an account (frees RAM).

```sh
cleos push action base.token close '["bob", "4,MYT"]' -p bob
```

### blacklist
Add or remove an account from blacklist.
Only the contract account can perform this action.

```sh
cleos push action base.token blacklist '["baduser", true]' -p base.token
cleos push action base.token blacklist '["baduser", false]' -p base.token
```

### stake
Stake (lock) tokens on an account.
Only the hardcoded admin ("testedemonft") may stake or unstake tokens.

```sh
cleos push action base.token stake '["alice", "100.0000 MYT"]' -p testedemonft
```

### unstake
Unstake (release) previously staked tokens.

```sh
cleos push action base.token unstake '["alice", "50.0000 MYT"]' -p testedemonft
```

## Tables
**accounts** (scope: user): Each accountвЂ™s balance for each token symbol.

**stat** (scope: contract): Token statistics (supply, max supply, issuer) per symbol.

**stake** (scope: contract): Staked tokens per account.

**blacklist** (scope: contract): Blacklisted accounts (cannot transfer, receive, etc.).

## Staking & Blacklist Logic
Staked tokens are locked: The sum of staked amount and transfer amount may not exceed balance.

Blacklisted accounts: Any transfer, issue, open, or close attempt will fail if the account is blacklisted.

## Security & Compliance
All arithmetic uses strict EOSIO asset checks.

Authorization enforced: Only the correct account can perform each action (e.g., issuer for issue/retire, contract for blacklist, account owner for transfer).

No over-issuance: Cannot issue more than max supply.

Blacklisted enforcement: Impossible to transfer to/from or open/close for blacklisted accounts.

Hardcoded admin for staking: Only testedemonft account can (un)stake (demo only; should be refactored for production).

## Static Query Functions
get_supply(token_contract_account, symbol_code): Returns current on-chain token supply.

get_balance(token_contract_account, owner, symbol_code): Returns current on-chain token balance for an owner.

## Example Deployment Flow

**Deploy** contract to an EOSIO account (e.g., base.token)

**Create** token with create

**Issue** initial supply with issue

**Allow** transfers by users

**Stake** tokens for governance/utility as needed

**Blacklist** accounts as a compliance or moderation tool

Limitations / To-Do
Staking admin is hardcoded for demonstration; should be upgraded for governance/multisig.

No transfer memo validation (beyond 256 chars); for business use, more checks may be warranted.

Only basic staking (lock/unlock); could add rewards or other features as needed.

## License
MIT or similar permissive open-source license.

## Best Practices
Always audit contract for business or regulatory use.

For production staking, use governance or multi-signature accounts instead of a hardcoded admin.

DApps should use open to prepay RAM for new users.

Frontends should monitor blacklist for compliance.

## basetoken.cpp

```cpp
#include <eosio/eosio.hpp>
#include <eosio/asset.hpp>
#include <eosio/transaction.hpp>
#include <eosio/system.hpp>
#include <eosio/crypto.hpp>
#include <eosio/action.hpp>
#include <eosio/print.hpp>

using namespace eosio;
using namespace std;
using std::string;
using std::vector;

#include "basetoken.hpp"

namespace eosio {

/**
 * @brief Action: Create a new token, defining its issuer and maximum supply.
 * Can only be called by contract itself.
 */
void basetoken::create( const name& issuer, const asset& maximum_supply )
{
    require_auth( get_self() ); // Only contract can create tokens

    auto sym = maximum_supply.symbol;
    check( sym.is_valid(), "Invalid symbol name" );
    check( maximum_supply.is_valid(), "Invalid supply");
    check( maximum_supply.amount > 0, "Max-Supply must be more then 0");

    stats statstable( get_self(), sym.code().raw() );
    auto existing = statstable.find( sym.code().raw() );
    check( existing == statstable.end(), "This token already exist" );

    // Create the stat row for this symbol
    statstable.emplace( get_self(), [&]( auto& s ) {
        s.supply.symbol = maximum_supply.symbol;
        s.max_supply    = maximum_supply;
        s.issuer        = issuer;
    });
}

/**
 * @brief Action: Issue (mint) tokens, increasing total supply.
 * Only issuer can issue, and only to their own account.
 */
void basetoken::issue( const name& to, const asset& quantity, const string& memo )
{
    getblacklist( to ); // Prevent blacklisted issuance
    auto sym = quantity.symbol;
    check( sym.is_valid(), "Invalid symbol name" );
    check( memo.size() <= 256, "Memo has more than 256 bytes" );

    stats statstable( get_self(), sym.code().raw() );
    auto existing = statstable.find( sym.code().raw() );
    check( existing != statstable.end(), "This token dont exist." );
    const auto& st = *existing;
    check( to == st.issuer, "Token can only be issued TO issuer account" );
    require_recipient( to );
    require_auth( st.issuer );
    check( quantity.is_valid(), "Invalid quantity" );
    check( quantity.amount > 0, "Amount should be more then 0" );

    check( quantity.symbol == st.supply.symbol, "Symbol precision mismatch" );
    check( quantity.amount <= st.max_supply.amount - st.supply.amount, "Quantity exceeds available supply");

    // Increase supply and add to issuer's balance
    statstable.modify( st, same_payer, [&]( auto& s ) {
        s.supply += quantity;
    });
    add_balance( st.issuer, quantity, st.issuer );
}

/**
 * @brief Action: Retire (burn) tokens, reducing total supply.
 * Only issuer can retire.
 */
void basetoken::retire( const asset& quantity, const string& memo )
{
    auto sym = quantity.symbol;
    check( sym.is_valid(), "Invalid symbol name" );
    check( memo.size() <= 256, "Memo has more than 256 bytes" );

    stats statstable( get_self(), sym.code().raw() );
    auto existing = statstable.find( sym.code().raw() );
    check( existing != statstable.end(), "Token with symbol does not exist" );
    const auto& st = *existing;

    require_auth( st.issuer );
    check( quantity.is_valid(), "Invalid quantity" );
    check( quantity.amount > 0, "Amount should be more then 0" );

    check( quantity.symbol == st.supply.symbol, "Symbol precision mismatch" );

    statstable.modify( st, same_payer, [&]( auto& s ) {
        s.supply -= quantity;
    });
    sub_balance( st.issuer, quantity );
}

/**
 * @brief Action: Transfer tokens between accounts.
 * Enforces blacklist, staked amounts, and minimum checks.
 */
void basetoken::transfer( name from, name to, asset quantity, string memo )
{
    check( from != to, "Cannot transfer to self" );
    require_auth( from );
    getblacklist( from );
    getblacklist( to );
    check( is_account( to ), "TO ["+to.to_string()+"] account does not exist");
    auto sym = quantity.symbol.code();
    stats statstable( get_self(), sym.raw() );
    const auto& st = statstable.get( sym.raw() );

    require_recipient( from );
    require_recipient( to );
    
    check_quantity( quantity );
    check( quantity.symbol == st.supply.symbol, "Symbol precision mismatch" );
    check( memo.size() <= 256, "Memo has more than 256 bytes" );

    auto payer = has_auth( to ) ? to : from;
    
    get_staked_balance( from, quantity ); // Ensure enough non-staked tokens

    sub_balance( from, quantity );
    add_balance( to, quantity, payer );
}

/**
 * @brief Subtracts tokens from account balance.
 */
void basetoken::sub_balance( const name owner, const asset value ) {
    accounts from_acnts( get_self(), owner.value );
    const auto& from = from_acnts.find( value.symbol.code().raw() );  
    if( from == from_acnts.end() ) {
        check( false, "FROM ["+owner.to_string()+"] dont have ["+value.symbol.code().to_string()+"] tokens" );
    }else{
        check( from->balance.amount >= value.amount, "Overdraw balance on token ["+value.symbol.code().to_string()+"] on ["+owner.to_string()+"]" );
        
        from_acnts.modify( from, owner, [&]( auto& a ) {
            a.balance -= value;
        });
    }
}

/**
 * @brief Adds tokens to account balance, creating row if needed.
 */
void basetoken::add_balance( const name owner, const asset value, const name ram_payer )
{
    accounts to_acnts( get_self(), owner.value );
    auto to = to_acnts.find( value.symbol.code().raw() );
    if( to == to_acnts.end() ) {
        to_acnts.emplace( ram_payer, [&]( auto& a ){
            a.balance = value;
        });
    } else {
        to_acnts.modify( to, same_payer, [&]( auto& a ) {
            a.balance += value;
        });
    }
}

/**
 * @brief Checks if enough non-staked tokens are available before transfer.
 */
void basetoken::get_staked_balance( const name from, asset quantity ){
    accounts from_acnts( get_self(), from.value );
    auto balance = from_acnts.find( quantity.symbol.code().raw() );
    if( balance != from_acnts.end() ){
        stakeds staked( get_self(), get_self().value );
        auto stake = staked.find( from.value );
        if( stake != staked.end() ) {
            if( balance->balance.amount < ( quantity.amount + stake->staked.amount ) ){
                check( false, "FROM ["+from.to_string()+"] account have staked amount ["+std::to_string( stake->staked.amount )+"]. Balance is less than possible transfer." );
            }
        }
    }
}

/**
 * @brief Action: Open a token balance row for an account and symbol.
 */
void basetoken::open( const name& owner, const symbol& symbol, const name& ram_payer )
{
    require_auth( ram_payer );
    getblacklist( owner );
    getblacklist( ram_payer );

    check( is_account( owner ), "owner ["+owner.to_string()+"] account does not exist" );

    auto sym_code_raw = symbol.code().raw();
    stats statstable( get_self(), sym_code_raw );
    const auto& st = statstable.get( sym_code_raw, "Symbol does not exist" );
    check( st.supply.symbol == symbol, "Symbol precision mismatch" );

    accounts acnts( get_self(), owner.value );
    auto it = acnts.find( sym_code_raw );
    if( it == acnts.end() ) {
        acnts.emplace( ram_payer, [&]( auto& a ){
            a.balance = asset{0, symbol};
        });
    }
}

/**
 * @brief Action: Close a token balance row for an account (balance must be zero).
 */
void basetoken::close( const name& owner, const symbol& symbol )
{
    require_auth( owner );
    getblacklist( owner );
    accounts acnts( get_self(), owner.value );
    auto it = acnts.find( symbol.code().raw() );
    check( it != acnts.end(), "Balance row already deleted or never existed. Action won't have any effect." );
    check( it->balance.amount == 0, "Cannot close because the balance is not zero." );
    acnts.erase( it );
}
 
/**
 * @brief Action: Stake tokens (only callable by privileged account for demo).
 * Staked tokens are locked and cannot be transferred.
 */
void basetoken::stake( const name from, const asset quantity )
{
    require_auth( "testedemonft"_n ); // Hardcoded admin for demonstration
    check_quantity( quantity );
    
    accounts from_acnts( get_self(), from.value );
    auto balance = from_acnts.find( quantity.symbol.code().raw() );
    if( balance != from_acnts.end() ){
        if( balance->balance.amount < quantity.amount ){
            check( false, "FROM ["+from.to_string()+"] balance ["+std::to_string( balance->balance.amount )+"] is less than want stake ["+std::to_string( quantity.amount )+"]" );
        }
    }else{
        check( false, "FROM ["+from.to_string()+"] account have balance" );
    }
    
    stakeds staked( get_self(), get_self().value );
    auto to = staked.find( from.value );
    if( to == staked.end() ) {
        staked.emplace( get_self(), [&]( auto& t ){
            t.account = from;
            t.staked = quantity;
        });
    } else {
        staked.modify( to, get_self(), [&]( auto& t ) {
            t.staked += quantity;
        });
    }
}

/**
 * @brief Action: Unstake tokens, releasing them for transfer.
 */
void basetoken::unstake( const name from, const asset quantity )
{
    require_auth( "testedemonft"_n ); // Hardcoded admin for demonstration
    check_quantity( quantity );
    stakeds staked( get_self(), get_self().value );
    auto stake = staked.find( from.value );
    if( stake == staked.end() ){
        check( false, "FROM ["+from.to_string()+"] account does have stake" );
    }else{
        if( stake->staked.amount == quantity.amount ){
            staked.erase( stake );
        }else if( stake->staked.amount < quantity.amount ){
            check( false, "FROM ["+from.to_string()+"] account have less staked amount ["+std::to_string( stake->staked.amount )+"] than want unstake ["+std::to_string( quantity.amount )+"]" );
        }else{
            staked.modify( stake, get_self(), [&]( auto& a ) {
                a.staked -= quantity;
            });
        }
    }
}

/**
 * @brief Internal utility: Check if an account is blacklisted and abort if true.
 */
void basetoken::getblacklist( name account ){
    db_blacklist blacklist(get_self(), get_self().value);
    auto black = blacklist.find( account.value );
    if(black != blacklist.end()){
        check(false, "Account is on BLACKLIST");
    }
}

/**
 * @brief Action: Add or remove an account from the blacklist (contract-only).
 * Notifies the account.
 */
void basetoken::blacklist( name account, bool a ){
    require_auth(get_self());
    require_recipient( account );
    if( account == get_self()){
        check(false, "SELF not should be added");
    }
    db_blacklist blacklist(get_self(), get_self().value);
    auto black = blacklist.find( account.value );
    if(black == blacklist.end()){
        if(!a){ check(false, "Account dont exist"); }
        blacklist.emplace(get_self(), [&](auto& t){
            t.account = account;
        });
    }else{
        if(a){
            check(false, "Account already exist");
        }else{
            blacklist.erase(black);
        }
    }
}

/**
 * @brief Internal utility: Checks validity of a quantity (positive, valid, symbol valid).
 */
void basetoken::check_quantity( asset quantity ){
    auto sym = quantity.symbol;
    check( quantity.is_valid(), "Invalid quantity" );
    check( sym.is_valid(), "Invalid symbol name" );
    check( quantity.amount > 0, "Quantity must be positive");
}

} // namespace eosio
```
## basetoken.hpp
```cpp
#pragma once

// ---- Standard EOSIO headers for smart contract development ----
#include <eosio/eosio.hpp>          // EOSIO contract, macro, and ABI definitions
#include <eosio/print.hpp>          // For debugging (not required in production)
#include <eosio/asset.hpp>          // Asset and symbol types
#include <eosio/transaction.hpp>    // Transaction utilities (not heavily used here)
#include <eosio/action.hpp>         // Action construction utilities

using namespace eosio;
using namespace std;
using std::string;
using std::vector;

/**
 * @namespace eosio
 * EOSIO C++ API namespace. All contract code is under this.
 */
namespace eosio {

    /**
     * @class basetoken
     * @brief A basic EOSIO token contract, with support for blacklisting, staking, and standard actions.
     * 
     * Features:
     * - ERC-20 like interface (create, issue, retire, transfer, open, close)
     * - Blacklist: prevent listed accounts from actions
     * - Staking: lock tokens on accounts for DeFi/gov use-cases
     */
    class [[eosio::contract("base.token")]] basetoken : public contract {
    public:
        using contract::contract;

        // --- Standard Token Actions (all exposed as public EOSIO actions) ---

        /**
         * @brief Create a new token with the specified maximum supply and issuer.
         * Only contract itself can call.
         * @param issuer          Who will control issuance of tokens
         * @param maximum_supply  The maximum allowable supply (asset, includes symbol and precision)
         */
        [[eosio::action]]
        void create( const name& issuer, const asset& maximum_supply);
        
        /**
         * @brief Issue new tokens to the issuer's account. Only issuer may call.
         * @param to       Account to receive issued tokens (must be issuer!)
         * @param quantity Amount of tokens to issue
         * @param memo     Arbitrary string memo (max 256 bytes)
         */
        [[eosio::action]]
        void issue( const name& to, const asset& quantity, const string& memo );

        /**
         * @brief Retire tokens, removing them from circulation. Only issuer may call.
         * @param quantity Amount of tokens to burn/retire
         * @param memo     Arbitrary memo
         */
        [[eosio::action]]
        void retire( const asset& quantity, const string& memo );

        /**
         * @brief Standard token transfer between accounts.
         * @param from     Sender (must authorize)
         * @param to       Recipient
         * @param quantity Amount to transfer
         * @param memo     Arbitrary memo (max 256 bytes)
         */
        [[eosio::action]]
        void transfer( const name from, const name to, const asset quantity, const string memo );

        /**
         * @brief Open a balance row for a given symbol on behalf of owner (required for RAM payer logic).
         * @param owner      Who will own the new token balance row
         * @param symbol     The token symbol
         * @param ram_payer  Who pays for RAM usage
         */
        [[eosio::action]]
        void open( const name& owner, const symbol& symbol, const name& ram_payer );

        /**
         * @brief Close a balance row for a given symbol if balance is zero.
         * @param owner  Account who owns the row (must authorize)
         * @param symbol Token symbol
         */
        [[eosio::action]]
        void close( const name& owner, const symbol& symbol );
        
        /**
         * @brief Add or remove an account from the blacklist.
         * @param account  Account to add/remove
         * @param a        true = add to blacklist, false = remove from blacklist
         */
        [[eosio::action]]
        void blacklist( name account, bool a );

        /**
         * @brief Stake tokens, locking them for advanced use-cases.
         * @param from     Account to stake from (must own tokens)
         * @param quantity Amount to stake
         */
        [[eosio::action]]
        void stake( const name from, const asset quantity );

        /**
         * @brief Unstake previously staked tokens.
         * @param from     Account to unstake from (must own stake)
         * @param quantity Amount to unstake
         */
        [[eosio::action]]
        void unstake( const name from, const asset quantity );

        // --- Static Utility Methods for DApps and Scripts ---
        
        /**
         * @brief Get the current supply for a symbol from on-chain stats table.
         */
        static asset get_supply( const name& token_contract_account, const symbol_code& sym_code )
        {
            stats statstable( token_contract_account, sym_code.raw() );
            const auto& st = statstable.get( sym_code.raw() );
            return st.supply;
        }

        /**
         * @brief Get the balance of a specific owner for a symbol from the on-chain table.
         */
        static asset get_balance( const name& token_contract_account, const name& owner, const symbol_code& sym_code )
        {
            accounts accountstable( token_contract_account, owner.value );
            const auto& ac = accountstable.get( sym_code.raw() );
            return ac.balance;
        }

        // --- EOSIO ABI Action Wrappers ---
        using create_action     = eosio::action_wrapper<"create"_n, &basetoken::create>;
        using issue_action      = eosio::action_wrapper<"issue"_n, &basetoken::issue>;
        using retire_action     = eosio::action_wrapper<"retire"_n, &basetoken::retire>;
        using transfer_action   = eosio::action_wrapper<"transfer"_n, &basetoken::transfer>;
        using open_action      = eosio::action_wrapper<"open"_n, &basetoken::open>;
        using close_action     = eosio::action_wrapper<"close"_n, &basetoken::close>;
        using blacklist_action = eosio::action_wrapper<"blacklist"_n, &basetoken::blacklist>;
        using stake_action     = eosio::action_wrapper<"stake"_n, &basetoken::stake>;
        using unstake_action   = eosio::action_wrapper<"unstake"_n, &basetoken::unstake>;
        
    private:
        // --- Internal contract utility functions (not exposed as actions) ---
        
        void getblacklist( name account );                              // Checks if account is blacklisted; aborts if true
        void sub_balance( const name owner, const asset value );        // Subtracts value from owner's balance
        void add_balance( const name owner, const asset value, const name ram_payer ); // Adds value to owner's balance
        void get_staked_balance( const name from, asset quantity );     // Checks if sufficient non-staked tokens available
        void check_quantity( asset quantity );                          // Checks quantity is valid and positive

        // --- On-chain Multi-Index Table Definitions ---

        /**
         * @struct account
         * Per-account, per-symbol token balance table (standard EOSIO token pattern)
         */
        struct [[eosio::table]] account {
            asset balance;
            uint64_t primary_key()const { return balance.symbol.code().raw(); }
        };

        /**
         * @struct currency_stats
         * Singleton stats table for each token symbol
         */
        struct [[eosio::table]] currency_stats {
            asset supply;
            asset max_supply;
            name issuer;
            uint64_t primary_key()const { return supply.symbol.code().raw(); }
        };
        
        /**
         * @struct currency_stake
         * Per-account staking info (amount staked)
         */
        struct [[eosio::table]] currency_stake {
            name account;
            asset staked;
            uint64_t primary_key()const { return account.value; }
        };
        
        /**
         * @struct blacklists
         * Stores all blacklisted accounts (preventing them from certain actions)
         */
        struct [[eosio::table]] blacklists {
            name account;
            uint64_t primary_key() const { return account.value; }
        };

        // Multi-index types
        typedef eosio::multi_index< "accounts"_n, account > accounts;
        typedef eosio::multi_index< "stat"_n, currency_stats > stats;
        typedef eosio::multi_index< "stake"_n, currency_stake > stakeds;
        typedef eosio::multi_index< "blacklist"_n, blacklists > db_blacklist;
    };
} // namespace eosio

```
# Smart Contract Database Walkthrough

{% note alert %}

This smart contract is presented here as an example, do not use it for production without prior verification.

{% endnote %}

If you don't have a local deNotary node installed, use the deployment tools at docs.deNotary.io 

- Mainnet <a href="https://explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- Testnet <a href="https://dev-explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- For quick deployment to a test network, use the <a href="https://deploy.deNotary.io" target="_blank" rel="noreferrer noopener">Web Deploy</a> tools  
- You can read more about this here [Quick Start](/quick-start)  

The ``emplace`` constructor is typically used to create database objects.

## Files

<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/database.hpp" download target="_blank" rel="noreferrer noopener">Download database.hpp</a>  
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/database.cpp" download target="_blank" rel="noreferrer noopener">Download database.cpp</a>  
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/database.abi" download target="_blank" rel="noreferrer noopener">Download database.abi</a>  

## database.cpp
```cpp
#include "database.hpp"

void test_da::create(name user, string title, string content)
{
    require_auth(user);

    check(title.size() > 0, "Title cannot be empty");
    check(content.size() > 0, "Content cannot be empty");
    check(title.size() <= 128, "Title too long");
    check(content.size() <= 4096, "Content too long");

    das datable(get_self(), get_self().value); // One global table (can use user.value for user-scoped)

    datable.emplace(user, [&](auto& d) {
        d.post_id = datable.available_primary_key();
        d.poster = user;
        d.title = title;
        d.content = content;
    });
}

void test_da::erase(name user, uint64_t post_id)
{
    das datable(get_self(), get_self().value);
    auto itr = datable.find(post_id);
    check(itr != datable.end(), "Post not found");
    check(itr->poster == user, "Only the poster can delete their post");
    require_auth(user);
    datable.erase(itr);
}

```
Precautions:

In the definition of a database object, the first parameter **_self** indicates the contract owner. The second parameter **user** indicates the database **payer**, namely, the account to which the database storage belongs.
The emplace constructor receives a **payer** parameter and a lamada expression. This structure is fixed.
Let's view the definition of the **test_da** class.
	

## database.hpp

```cpp
#pragma once

#include <eosio/eosio.hpp>
#include <string>

using namespace eosio;
using std::string;

CONTRACT test_da : public contract {
public:
    using contract::contract;

    // Create new post
    [[eosio::action]]
    void create(name user, string title, string content);

    // (Optional) Remove post by id (can only be deleted by poster)
    [[eosio::action]]
    void erase(name user, uint64_t post_id);

    // Table for posts
    struct [[eosio::table]] da {
        uint64_t     post_id;     // Unique post id (auto increment)
        name         poster;      // Account who posted
        string       title;
        string       content;

        uint64_t primary_key() const { return post_id; }
        uint64_t byposter() const { return poster.value; }
    };

    using das = multi_index<
        "data"_n, da,
        indexed_by<"byposter"_n, const_mem_fun<da, uint64_t, &da::byposter>>
    >;
};

```

All smart contracts are inherited from ***contract. test_da( account_name self ):contract(self){} is the constructor of the test_da*** contract.
The row following **test_da( account_name self ):contract(self){}** is a declaration of the create function.
The rows following the **create** function define data fields. Here we define the data structure **da**.
The primary_key function defines the primary key.
The row following the **primary_key** function defines a **secondary key**, that is, return poster.
The first parameter of the macro EOSLIB_SERIALIZE is the data structure, and the other parameters are data members in the data structure.
typedef defines the das type, which is a database object. In this example, we define a database object containing a primary key and a secondary key.

## database.abi
abi is very important. An incorrect abi will cause contract execution failure.
```json
{
  "types": [],
  "structs": [{
      "name": "da",
      "base": "",
      "fields": [{
          "name": "post_id",
          "type": "uint64"
        },{
          "name": "poster",
          "type": "account_name"
        },{
          "name": "title",
          "type": "string"
        },{
          "name": "content",
          "type": "string"
        }
      ]
    },{
      "name": "create",
      "base": "",
      "fields": [{
          "name": "user",
          "type": "account_name"
        },{
          "name": "title",
          "type": "string"
        },{
          "name": "content",
          "type": "string"
        }
      ]
    }}
  ],
  "actions": [{
          "name": "create",
          "type": "create",
        }
  ],
  "tables": [{
      "name": "data",
      "index_type": "i64",
      "key_names": [
        "post_id"
      ],
      "key_types": [
        "uint64"
      ],
      "type": "da"
    }
  ],
  "ricardian_clauses": []
}
```
Data Creation Example
Publish a contract.

```bash
cleos set contract eosio test_da     
Reading WAST/WASM from test_da/test_da.wasm...
Using already assembled WASM...
Publishing contract...
executed transaction: 3d6f04278617d3807fe876a33057f1155acf9c9e5a392ac6ed8ad51e79506009  6752 bytes  24679 us
#         eosio <= eosio::setcode               {"account":"eosio","vmtype":0,"vmversion":0,"code":"0061736d0100000001ad011a60037f7e7e0060057f7e7e7f...
#         eosio <= eosio::setabi                {"account":"eosio","abi":{"types":[],"structs":[{"name":"da","base":"","fields":[{"name":"post_id","...
```
Create data.

```bash
cleos push action eosio create '{"user":"eosio","title":"first","content":"create a first one"}' -p eosio
executed transaction: 830057f270fa499b1d61b82e80ad8cda1774cdc1786c1e786f558a3e0a48974c  216 bytes  17229 us
#         eosio <= eosio::create                {"user":"eosio","title":"first","content":"create a first one"}
```

Query the data table.

```bash
cleos get table eosio eosio data
{
  "rows": [{
      "post_id": 0,
      "poster": "eosio",
      "title": "first",
      "content": "create a first one"
    }
  ],
  "more": false
}
```

The query result indicates that data has been created successfully. Will it be successful if we create data using another account?

```bash
cleos push action eosio create '{"user":"eostea","title":"eostea first","content":"eostea create a first one"}' -p eostea
executed transaction: 8542a87e563a9c62b7dbe46ae09ccf829c7821f8879167066b658096718de148  232 bytes  2243 us
#         eosio <= eosio::create                {"user":"eostea","title":"eostea first","content":"eostea create a first one"}
```

Query the data table.

```bash
cleos get table eosio eostea data
{
  "rows": [{
      "post_id": 0,
      "poster": "eostea",
      "title": "eostea first",
      "content": "eostea create a first one"
    }
  ],
  "more": false
}
```

Great, it works! Here we shall have no questions about data creation.

Query

The most important function of a database is data query. If there is no query function, data in the database cannot be presented and therefore becomes meaningless. The database can be queried by primary key or secondary index.
In this document, all data is stored in one table to diversify the table data.
The preceding das **datable( _self, user);** in .cpp is replaced with das **datable( _self, _self);**. In this way, all data is stored in the table under the contract account.

##Query data by primary key

In this example, a method is added to query and print data:
```cpp
void test_da::getd(uint64_t post_id){
        das datable(_self, _self);
        auto post_da = datable.find( post_id);
        eosio::print("Post_id: ", post_da->post_id, "  Post_Tile: ", post_da->title.c_str(), " Content: ", post_da->content.c_str());
    }
```

The .abi file is also modified accordingly.

Run the following commands:
```bash
cleos push action eosio getd '{"post_id":1}' -p eosio
executed transaction: ac8663235462d947c74542af848cca54a059c3991d193237025da7d4767d6725  192 bytes  1724 us
#         eosio <= eosio::getd                  {"post_id":1}
>> Post_id: 1  Post_Tile: first Content: eosio create a first one
```

## Query data by secondary index

Add the following code to query data by secondary index:
```cpp
auto poster_index = datable.template get_index<N(byposter)>();
auto pos = poster_index.find( user );

for (; pos != poster_index.end(); pos++)
{
    eosio::print("content:", pos->content.c_str(), " post_id:", pos->post_id, " title:", pos->title.c_str());
}
```
Obtain the secondary index and use it to query data. In this example, only the find function is used for query.

Run getd
```bash
cleos push action eosio getd '{"post_id":2,"user": "eostea"}' -p eosio
executed transaction: 2370e1fb1ee8a581f7321f02fb40645e51269e579d183c33ef470dba0b3afdbc  200 bytes  5403 us
#         eosio <= eosio::getd                  {"post_id":2,"user":"eostea"}
>> Post_id: 2  Post_Tile: eostea first Content: eostea create a first onecontent:eostea create a first one post_id:2 title:eostea first
```

The data query result is as follows:
```bash
cleos get table eosio eosio data
{
 "rows": [{
     "post_id": 0,
     "poster": "eosio",
     "title": "first",
     "content": "eostea create a first one"
   },{
     "post_id": 1,
     "poster": "eosio",
     "title": "first",
     "content": "eostea create a first one"
   },{
     "post_id": 2,
     "poster": "eostea",
     "title": "eostea first",
     "content": "eostea create a first one"
   }
 ],
 "more": false
}
```

## Modify
Modify data in the database.

The existing data in the database is as follows:
```bash
cleos get table eosio eosio data
{
 "rows": [{
     "post_id": 0,
     "poster": "eosio",
     "title": "first",
     "content": "eostea create a first one"
   },{
     "post_id": 1,
     "poster": "eosio",
     "title": "first",
     "content": "eostea create a first one"
   },{
     "post_id": 2,
     "poster": "eostea",
     "title": "eostea first",
     "content": "eostea create a first one"
   }
 ],
 "more": false
}
```

Use the following action code to modify the data:
```cpp
void test_da::change(account_name user, uint64_t post_id, string title, string content)
    {
        require_auth(user);
        das datable( _self, user);
        auto post = datable.find(post_id);
        eosio_assert(post->poster == user, "yonghucuowu");
        datable.modify(post, user, [&](auto& p){
            if (title != "")
                p.title = title;
            if (content != "")
                p.content = content;
        });
    }
```

The first few rows of the code have been described before. We only describe the modify method in the code. The first parameter post is the object you have found for modification, and the second parameter user indicates the payer.

Run the following commands:
```bash
cleos push action eosio change '{"user":"eosio","post_id":1,"title":"change","content":"change action"}' -p eosio
executed transaction: 8cb561a712f2741560118651aefd49efd161e3d73c56f6d24cf1d699c265e2dc  224 bytes  2130 us
#         eosio <= eosio::change                {"user":"eosio","post_id":1,"title":"change","content":"change action"}
```

Query the database data:
```bash
cleos get table eosio eosio data
{
  "rows": [{
      "post_id": 0,
      "poster": "eosio",
      "title": "first",
      "content": "eostea create a first one"
    },{
      "post_id": 1,
      "poster": "eosio",
      "title": "change",
      "content": "change action"
    },{
      "post_id": 2,
      "poster": "eostea",
      "title": "eostea first",
      "content": "eostea create a first one"
    }
  ],
  "more": false
}
```

The query result indicates that the data record containing post_id=1 has been modified.

## Delete

The following action function is added to delete data:
```cpp
void test_da::dele(account_name user, uint64_t post_id)
    {
        require_auth(user);
        das datable( _self, user);
        auto post = datable.find(post_id);
        eosio::print(post->title.c_str());

        eosio_assert(post->poster == user, "yonghucuowu");
        datable.erase(post);
    }
```
The erase method is called to delete data, and the parameter is a data object. Check the command output.

```bash
cleos push action eosio dele '{"user":"eosio","post_id":1}' -p eosioexecuted transaction: 3affbbbbd1da328ddcf37753f1f2f6c5ecc36cd81a0e12fea0c789e75b59714e  200 bytes  2383 us
#         eosio <= eosio::dele                  {"user":"eosio","post_id":1}
```

Query the database data:
```bash
cleos get table eosio eosio data
{
  "rows": [{
      "post_id": 0,
      "poster": "eosio",
      "title": "first",
      "content": "eostea create a first one"
    },{
      "post_id": 2,
      "poster": "eostea",
      "title": "eostea first",
      "content": "eostea create a first one"
    }
  ],
  "more": false
}
```
The query result indicates that the data record containing post_id=1 has been deleted.
# On-Chain Private Messaging for deNotary
## messenger

{% note alert %}

This smart contract is presented here as an example, do not use it for production without prior verification.

{% endnote %}

If you don't have a local deNotary node installed, use the deployment tools at docs.deNotary.io 

- Mainnet <a href="https://explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- Testnet <a href="https://dev-explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- For quick deployment to a test network, use the <a href="https://deploy.deNotary.io" target="_blank" rel="noreferrer noopener">Web Deploy</a> tools  
- You can read more about this here [Quick Start](/quick-start)  

## Files

<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/msg.cpp" download target="_blank" rel="noreferrer noopener">Download msg.cpp</a>  
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/msg.abi" download target="_blank" rel="noreferrer noopener">Download msg.abi</a>  

## Overview
messenger is a simple, fully on-chain private messaging smart contract for deNotary blockchains.  
It allows any user to send, receive, and erase messages using only deNotary actions.  
All messages and notifications are stored on-chain, enabling DApp or wallet integrations that provide private inbox and outbox functionality.  

## Features
- Send Messages to any deNotary account  
- Receive and Delete Messages (only the intended recipient can receive)  
- Erase Sent Messages (sender can delete a message before it is read)  
- Notifications Table enables efficient inbox discovery for each user  
- All data on-chain: easy to integrate with block explorers and wallets
- No off-chain infrastructure required

### Actions
#### sendmsg
Send a message from one account to another.

```cpp
sendmsg(account_name from, account_name to, std::string msg)
```
**from**: Sender (must sign the transaction)  
**to**: Recipient  
**msg**: The message text (must not be empty)  

#### receivemsg
Receive and delete a message from your inbox.

```cpp
receivemsg(account_name to, uint64_t id)
```
**to**: The recipient (must sign)  
**id**: The unique message/notification ID  

#### erasemsg
Delete a message you previously sent (can be used before itвЂ™s read).

```cpp
erasemsg(account_name from, uint64_t id)
```
**from**: The sender (must sign)  
**id**: The unique message/notification ID  

### How It Works
When a message is sent, a notification is stored in a global table (so the recipient can quickly find new messages), and the message itself is stored in the senderвЂ™s scoped message table.  
Each message and notification shares a unique ID.  
To receive a message, the recipient calls receivemsg, which deletes both the notification and the message.  
The sender can also delete a message (before it is read) by calling erasemsg.  

### Table Structure
message (scoped by sender):
**id**: unique message id  
**to**: recipient  
**text**: message body  
**send_at**: timestamp  
**type**: reserved for future use  

notification (global scope):
**id**: unique notification/message id  
**from**: sender  
**to**: recipient  

Secondary index by to enables efficient inbox lookups.

### Example Usage

Send a message:
```sh
cleos push action messengeracc sendmsg '["alice", "bob", "Hello, Bob!"]' -p alice
```

View incoming notifications (inbox) for Bob:
```sh
cleos get table messengeracc messengeracc notification --index 2 --key-type name --lower bob --upper bob
```

Bob receives (deletes) a message:
```sh
cleos push action messengeracc receivemsg '["bob", 7]' -p bob
```

Alice deletes a sent message (before it is read):
```sh
cleos push action messengeracc erasemsg '["alice", 7]' -p alice
```

## Security and Best Practices
**Authorization**: Only the sender can erase their sent messages. Only the recipient can receive messages addressed to them.  
Message Privacy: Message content is stored on-chain and can be read by anyone with access to blockchain state. (For privacy, encrypt message text before sending.)  
Notification Table: Enables DApps to build inbox/outbox user interfaces efficiently.  
Resource Usage: Each message/notification consumes contract RAM (paid by sender).  

## Limitations & Extending
Not truly private: On-chain data is public. For confidential messaging, users should encrypt message text.
No attachments or advanced metadata (but can be added via the type field or message format).
No group chat (one-to-one messages only).
No message pagination (but easy to implement via message ids).

#### Extensions could include:
Group messages
Message encryption utilities
Message expiry and archiving
DApp wallet notification integration

## License
MIT or similar permissive license.

## msg.cpp
```cpp
/**
 *  @file
 *  EOSIO Messenger Contract
 *  Enables sending, receiving, and deleting private messages on chain.
 */

#include <utility>
#include <vector>
#include <string>
#include <eosiolib/eosio.hpp>        // EOSIO contract base class and macros
#include <eosiolib/asset.hpp>        // For asset types (not used in this contract)
#include <eosiolib/contract.hpp>     // EOSIO contract base
#include <eosiolib/time.hpp>         // EOSIO time and time_point_sec
#include <eosiolib/print.hpp>        // EOSIO print for debugging (not used in production)
#include <eosiolib/transaction.hpp>  // For inline/deferred transactions (not used here)

using namespace eosio;

/**
 * @class messenger
 * Implements a simple on-chain messenger with message sending, receiving, and deletion.
 */
class messenger : public eosio::contract
{
public:
  using contract::contract;

  // Contract constructor
  messenger(account_name self) : contract(self) {}

  /**
   * @brief Send a message from one account to another.
   * - Stores a notification and a message record on chain.
   * - The notification enables the recipient to find new incoming messages.
   * @param from  Sender account (must authorize)
   * @param to    Recipient account
   * @param msg   Message text (must not be empty)
   * @abi action
   */
  void sendmsg(const account_name from,
               const account_name to,
               const std::string msg)
  {
    require_auth(from);  // Ensure sender authorized

    eosio_assert(msg.size() > 0, "Empty message");

    // (Optional) Check that recipient account "to" exists

    notification_table notifications(_self, _self); // Notifications table (global scope)
    message_table messages(_self, from);            // Messages table (scoped to sender)

    uint64_t newid = notifications.available_primary_key(); // Unique message/notification id

    // Add a notification for the recipient (so they can find new messages)
    notifications.emplace(from, [&](auto &n) {
      n.id = newid;
      n.from = from;
      n.to = to;
    });

    // Store the actual message (including text and timestamp)
    messages.emplace(from, [&](auto &m) {
      m.id = newid;
      m.to = to;
      m.text = msg;
      m.send_at = eosio::time_point_sec(now());
      m.type = 0; // Reserved for future message type expansion
    });
  }

  /**
   * @brief Receive (and delete) a message that was sent to the recipient.
   * - The notification and message are deleted.
   * - Only the recipient can call this action.
   * @param to  The recipient account (must authorize)
   * @param id  The message/notification id
   * @abi action
   */
  void receivemsg(const account_name to, uint64_t id)
  {
    require_auth(to);

    notification_table notifications(_self, _self);
    auto itr_notif = notifications.find(id);
    eosio_assert(itr_notif != notifications.end(), "Notification not found");
    const auto &notif = *itr_notif;

    eosio_assert(notif.to == to, "Message not addressed to your account");

    message_table messages(_self, notif.from); // Message stored in sender's scope
    auto itr_msg = messages.find(id);
    eosio_assert(itr_msg != messages.end(), "Message not found");

    // Remove notification and message
    notifications.erase(itr_notif);
    messages.erase(itr_msg);
  }

  /**
   * @brief Delete a message sent by the sender (without recipient reading it).
   * - Only the sender can call this action.
   * - The notification and the message are deleted.
   * @param from  Sender account (must authorize)
   * @param id    The message/notification id
   * @abi action
   */
  void erasemsg(const account_name from, uint64_t id)
  {
    require_auth(from);

    notification_table notifications(_self, _self);
    auto itr_notif = notifications.find(id);
    eosio_assert(itr_notif != notifications.end(), "Notification not found");
    const auto &notif = *itr_notif;

    eosio_assert(notif.from == from, "Message was not sent from your account");

    message_table messages(_self, from); // Message stored in sender's scope
    auto itr_msg = messages.find(id);
    eosio_assert(itr_msg != messages.end(), "Message not found");

    // Remove notification and message
    notifications.erase(itr_notif);
    messages.erase(itr_msg);
  }

private:

  /**
   * @struct message
   * @brief Table structure for messages sent from this user.
   * - Scoped by sender's account.
   * - Stores recipient, message text, send time, and type.
   * @abi table message i64
   */
  struct message
  {
    uint64_t id;                   // Unique message id
    account_name to;               // Recipient account
    std::string text;              // Message body
    eosio::time_point_sec send_at; // Timestamp of when sent
    uint8_t type;                  // Reserved for future message types

    uint64_t primary_key() const { return id; }

    EOSLIB_SERIALIZE(message, (id)(to)(text)(send_at)(type))
  };
  typedef eosio::multi_index<N(message), message> message_table;

  /**
   * @struct notification
   * @brief Table structure for notifications of new messages.
   * - Stored globally (scope: contract).
   * - Each notification has sender and recipient accounts.
   * @abi table notification i64
   */
  struct notification
  {
    uint64_t id;           // Unique notification id (matches message id)
    account_name from;     // Sender account
    account_name to;       // Recipient account

    uint64_t primary_key() const { return id; }
     account_name get_to_key() const { return to; }
    
    EOSLIB_SERIALIZE(notification, (id)(from)(to))
  };

  typedef eosio::multi_index<N(notification), notification,
                             eosio::indexed_by<N(to),
                                               eosio::const_mem_fun<
                                                   notification,
                                                   account_name,
                                                   &notification::get_to_key>>>
      notification_table;

};

EOSIO_ABI(messenger, (sendmsg)(receivemsg)(erasemsg))
```

## msg.abi
```json
{
  "____comment": "This file was generated by eosio-abigen. DO NOT EDIT - 2018-08-26T20:16:23",
  "version": "eosio::abi/1.0",
  "types": [],
  "structs": [{
      "name": "message",
      "base": "",
      "fields": [{
          "name": "id",
          "type": "uint64"
        },{
          "name": "to",
          "type": "name"
        },{
          "name": "text",
          "type": "string"
        },{
          "name": "send_at",
          "type": "time_point_sec"
        },{
          "name": "type",
          "type": "uint8"
        }
      ]
    },{
      "name": "notification",
      "base": "",
      "fields": [{
          "name": "id",
          "type": "uint64"
        },{
          "name": "from",
          "type": "name"
        },{
          "name": "to",
          "type": "name"
        }
      ]
    },{
      "name": "sendmsg",
      "base": "",
      "fields": [{
          "name": "from",
          "type": "name"
        },{
          "name": "to",
          "type": "name"
        },{
          "name": "msg",
          "type": "string"
        }
      ]
    },{
      "name": "receivemsg",
      "base": "",
      "fields": [{
          "name": "to",
          "type": "name"
        },{
          "name": "id",
          "type": "uint64"
        }
      ]
    },{
      "name": "erasemsg",
      "base": "",
      "fields": [{
          "name": "from",
          "type": "name"
        },{
          "name": "id",
          "type": "uint64"
        }
      ]
    }
  ],
  "actions": [{
      "name": "sendmsg",
      "type": "sendmsg",
      "ricardian_contract": ""
    },{
      "name": "receivemsg",
      "type": "receivemsg",
      "ricardian_contract": ""
    },{
      "name": "erasemsg",
      "type": "erasemsg",
      "ricardian_contract": ""
    }
  ],
  "tables": [{
      "name": "message",
      "index_type": "i64",
      "key_names": [
        "id"
      ],
      "key_types": [
        "uint64"
      ],
      "type": "message"
    },{
      "name": "notification",
      "index_type": "i64",
      "key_names": [
        "id"
      ],
      "key_types": [
        "uint64"
      ],
      "type": "notification"
    }
  ],
  "ricardian_clauses": [],
  "error_messages": [],
  "abi_extensions": []
}
```
# On-chain Poll & Voting Smart Contract for deNotary
## pollgf

{% note alert %}

This smart contract is presented here as an example, do not use it for production without prior verification.

{% endnote %}

If you don't have a local deNotary node installed, use the deployment tools at docs.deNotary.io 

- Mainnet <a href="https://explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- Testnet <a href="https://dev-explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- For quick deployment to a test network, use the <a href="https://deploy.deNotary.io" target="_blank" rel="noreferrer noopener">Web Deploy</a> tools  
- You can read more about this here [Quick Start](/quick-start)  

## Overview
polleos is an deNotary smart contract for creating and managing decentralized polls.
It supports both:

### Files

<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/pollgf.hpp" download target="_blank" rel="noreferrer noopener">Download pollgf.hpp</a>  
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/pollgf.cpp" download target="_blank" rel="noreferrer noopener">Download pollgf.cpp</a>  
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/pollgf.abi" download target="_blank" rel="noreferrer noopener">Download pollgf.abi</a>  

### Standard polls (one account = one vote)

Token-weighted polls (voting power based on user's token balance)

All polls, options, and votes are stored transparently on-chain, providing auditable, trustless community decision-making.

## Features
Anyone can create polls with arbitrary text questions and custom voting options

Support for standard and token-weighted polls

Standard poll: each voter gets one vote

Token poll: each voterвЂ™s weight equals their balance of a specified token

Prevents double voting (each user can vote only once per poll)

All data on-chain: poll creation, vote casting, and tallies are persisted in GF tables

### Actions
#### newpoll
Create a new, standard (non-token-weighted) poll.

```cpp
newpoll(string question, account_name creator, vector<string> options)
```
question: The poll's question (string)  
creator: Account paying for RAM (who creates the poll)  
options: List of option strings  

#### newtokenpoll
Create a new poll where vote weights are based on token balance.

```cpp
newtokenpoll(string question, account_name payer, vector<string> options, extended_symbol token)
```
question: The poll's question  
payer: Account paying for RAM (who creates the poll)  
options: List of option strings  
token: The token used to weight votes (contract and symbol)  

#### vote
Vote in a poll.

```cpp
vote(uint64_t poll_id, account_name voter, uint8_t option_id)
```
poll_id: ID of the poll  
voter: Voter's account name  
option_id: Index of the chosen option  

### How Voting Works
Each poll has an ID, question, and options (max 255).

Standard poll: Each voter can cast one vote for one option.  
Token-weighted poll: Each voter can cast one vote; vote's weight = balance of specified token at voting time.  
Users cannot vote more than once in the same poll (double-voting is rejected).  

### Data Tables
poll (scope: contract): Stores all poll definitions (ID, question, options, results, token info).  
votes (scope: voter): Stores which poll(s) a user has voted in and for which option.  
All votes and poll results are available for public audit.  

### Example Usage
Create a standard poll:
```sh
cleos push action polleosacc newpoll '["Who is best?", "alice", ["Alice", "Bob", "Charlie"]]' -p alice
```
Create a token-weighted poll:

```sh
cleos push action polleosacc newtokenpoll '["Favorite EOSIO wallet?", "bob", ["Anchor", "Scatter"], ["4,DNLT","eosio.token"]]' -p bob
```

Vote in poll #1, option 2, as alice:
```sh
cleos push action polleosacc vote '[1, "alice", 2]' -p alice
```

### Security & Best Practices
Each user can vote only once per poll (enforced on-chain).  
For token-weighted polls, the user's token balance at the time of voting is used.  
Only tokens with a valid contract and symbol can be used.  
All results and tallies are on-chain for auditability.  

Requirements
deNotary/EOSIO/Antelope blockchain
Standard eosio.token contract deployed for token-weighted polls  

### Extending
Add poll closing times and restrict voting after close  
Allow poll creators to manage or remove polls  
Add support for anonymous voting (via zero-knowledge or shielded tokens)  
Integrate with UI or DAOs  

### License
MIT or similarly permissive license.

### pollgf.hpp
```cpp
#pragma once

#include <eosiolib/eosio.hpp>
#include <cmath>
#include "eosio.token.hpp"

/**
 * @class pollgf
 * EOSIO voting contract, supporting normal and token-weighted polls.
 */
class pollgf : public eosio::contract {
   public:
      typedef uint64_t                 poll_id_t;      // Type for poll IDs
      typedef std::vector<std::string> option_names_t; // List of option strings
      typedef eosio::extended_symbol   token_info_t;   // Token info (symbol+contract)
      typedef uint8_t                  option_id_t;    // Option index type

      pollgf(account_name contract_name)
         : eosio::contract(contract_name), _polls(contract_name, contract_name) {}

      /**
       * @struct option
       * Stores the name of a voting option.
       */
      struct option {
         std::string name;

         option(std::string name) : name(name) {}
         option() {}

         EOSLIB_SERIALIZE(option, (name))
      };

      /**
       * @struct option_result
       * Extends option by also tracking the number of votes.
       */
      struct option_result : option {
         double votes = 0; // Vote total (can be fractional for token-weighted polls)

         option_result(const std::string& name, uint64_t votes) : option(name), votes(votes) {}
         option_result(const std::string& name) : option_result(name, 0) {}
         option_result() {}

         EOSLIB_SERIALIZE(option_result, (name)(votes))
      };

      typedef std::vector<option_result> option_results;

      /**
       * @struct poll
       * Stores a poll (question, options, vote tallies, etc).
       */
      //@abi table
      struct poll {
         poll_id_t      id;            // Poll unique id
         std::string    question;      // Poll question text
         option_results results;       // Array of results (option name + vote tally)
         bool           is_token_poll = false; // True if poll is token-weighted
         token_info_t   token;         // Token info (if token-weighted)

         uint64_t primary_key() const { return id; }

         // Used for reverse order lookup/indexing (optional)
         uint64_t get_reverse_key() const { return ~id; }

         // Initializes poll object with all values and options.
         void set(poll_id_t id, const std::string& question,
                  const option_names_t& options, bool is_token_poll,
                  token_info_t token);

         EOSLIB_SERIALIZE(poll, (id)(question)(results)(is_token_poll)(token))
      };

      /**
       * @struct poll_vote
       * Stores a user's vote in a poll (per user per poll).
       */
      //@abi table votes
      struct poll_vote {
         poll_id_t   poll_id;    // The poll id this vote belongs to
         option_id_t option_id;  // Chosen option index

         uint64_t primary_key() const { return poll_id; }
         EOSLIB_SERIALIZE(poll_vote, (poll_id)(option_id))
      };

      // Table of polls, with a reverse index (not strictly needed)
      typedef eosio::multi_index<N(poll), poll,
         eosio::indexed_by<N(reverse),
            eosio::const_mem_fun<poll, uint64_t, &poll::get_reverse_key>
         >
      > poll_table;

      // Table of votes for each user (scope = user account)
      typedef eosio::multi_index<N(votes), poll_vote> vote_table;

      //@abi action
      void newpoll(const std::string& question, account_name creator,
                   const std::vector<std::string>& options);

      //@abi action
      void newtokenpoll(const std::string& question, account_name payer,
                        const std::vector<std::string>& options,
                        token_info_t token);

      //@abi action
      void vote(poll_id_t id, account_name voter, option_id_t option_id);

   private:
      // Stores poll on-chain.
      void store_poll(const std::string& question, account_name owner,
                      const option_names_t& options,
                      bool is_token_poll, token_info_t token);

      // Stores a user's vote and increments result.
      void store_vote(const poll& p, vote_table& votes, option_id_t option_id, double weight);

      // Stores a user's vote, using their token balance as weight.
      void store_token_vote(const poll& p, vote_table& votes, option_id_t option_id);

      // Converts an EOSIO asset to a weight (as a floating-point number)
      double to_weight(const eosio::asset& stake) {
         return stake.amount / std::pow(10, stake.symbol.precision());
      }

      poll_table _polls; // Main on-chain poll storage table
};
```

### pollgf.cpp
```cpp
/**
 * pollgf - A simple on-chain voting (poll) smart contract for EOSIO.
 * 
 * This contract allows anyone to create polls with multiple options, and for users to vote.
 * Polls can be standard (1 account = 1 vote) or "token-weighted" (vote weight is based on user's token balance).
 * Votes and poll data are stored on-chain for auditability and transparency.
 */

#include "pollgf.hpp"
#include <limits>

/**
 * @brief Sets up a poll object with the specified options and properties.
 * @param id            The poll's unique ID.
 * @param question      The poll question.
 * @param options       The list of options for voting.
 * @param is_token_poll True if this is a token-weighted poll.
 * @param token         Information about the token for weighting, if needed.
 */
void pollgf::poll::set(pollgf::poll_id_t id, const std::string& question,
                        const option_names_t& options, bool is_token_poll,
                        token_info_t token) {

   eosio_assert(!question.empty(), "Question can't be empty");

   this->id            = id;
   this->question      = question;
   this->is_token_poll = is_token_poll;
   this->token         = token;

   // Prepare results array for each voting option.
   results.resize(options.size());
   std::transform(options.begin(), options.end(), results.begin(),
                  [&](std::string str) {
                     eosio_assert(!str.empty(), "Option names can't be empty");
                     return option_result(str);
                  });
}

/**
 * @brief Stores a new poll in the contract's poll table.
 * @param question      The poll question.
 * @param poll_owner    Who pays RAM for this poll (creator).
 * @param options       The list of voting options.
 * @param is_token_poll Whether the poll is token-weighted.
 * @param token         Token info, if needed.
 */
void pollgf::store_poll(const std::string& question, account_name poll_owner,
                         const option_names_t& options,
                         bool is_token_poll, token_info_t token) {

   poll_id_t  id;

   eosio_assert(options.size() < std::numeric_limits<option_id_t>::max(),
                "Too many options");

   _polls.emplace(poll_owner, [&](poll& p) {
      id = _polls.available_primary_key();
      p.set(id, question, options, is_token_poll, token);
   });

   eosio::print("Poll stored with id: ", id);
}

/**
 * @brief Stores a user's vote in a poll (with explicit vote weight).
 *        Also increments the selected option's result.
 * @param p         The poll object.
 * @param votes     The vote table for the voter.
 * @param option_id The selected option's ID.
 * @param weight    The weight of the vote (1 for normal, token balance for token polls).
 */
void pollgf::store_vote(const pollgf::poll& p, pollgf::vote_table& votes,
                         option_id_t option_id, double weight) {

   eosio_assert(weight > 0, "Vote weight cannot be less than 0. Contract logic issue");

   // Voter (votes.get_scope()) pays for RAM.
   votes.emplace(votes.get_scope(), [&](poll_vote& v) {
      v.poll_id    = p.id;
      v.option_id  = option_id;
   });

   _polls.modify(p, votes.get_scope(), [&](poll& p) {
      p.results[option_id].votes += weight;
   });
}

/**
 * @brief Stores a user's token-weighted vote in a poll.
 *        Checks token balance, then records vote.
 * @param p         The poll object.
 * @param votes     The vote table for the voter.
 * @param option_id The selected option's ID.
 */
void pollgf::store_token_vote(const pollgf::poll& p, pollgf::vote_table& votes,
                               option_id_t option_id) {

   account_name voter = votes.get_scope();

   eosio::token token(p.token.contract);
   // Will fail if voter has no tokens
   eosio::asset balance = token.get_balance(voter, p.token.name());

   // Validate token balance
   eosio_assert(balance.is_valid(), "Balance of voter account is invalid. Something is wrong with token contract.");
   eosio_assert(balance.amount > 0, "Voter must have more than 0 tokens to participate in a poll!");

   // Store vote with token balance as weight
   store_vote(p, votes, option_id, to_weight(balance));
}

/**
 * @brief Create a new standard (non-token-weighted) poll.
 * @param question The poll question.
 * @param payer    Account paying for RAM.
 * @param options  The list of voting options.
 * @abi action
 */
void pollgf::newpoll(const std::string& question, account_name payer,
                      const option_names_t& options) {

   store_poll(question, payer, options, false, token_info_t());
}

/**
 * @brief Create a new token-weighted poll.
 * @param question   The poll question.
 * @param owner      Account paying for RAM.
 * @param options    The list of voting options.
 * @param token_inf  Info about the token to use for vote weighting.
 * @abi action
 */
void pollgf::newtokenpoll(const std::string& question, account_name owner,
                           const option_names_t& options, token_info_t token_inf) {

   eosio::token token(token_inf.contract);
   eosio_assert(token.exists(token_inf.name()), "This token does not exist");
   store_poll(question, owner, options, true, token_inf);
}

/**
 * @brief Cast a vote in a poll.
 *        Checks for double-voting and option validity, then stores the vote.
 * @param id        Poll id.
 * @param voter     Voter's account.
 * @param option_id Chosen option's index.
 * @abi action
 */
void pollgf::vote(pollgf::poll_id_t id, account_name voter, option_id_t option_id) {

   eosio::require_auth(voter);

   const poll & p = _polls.get(id, "Poll with this id does not exist");

   eosio_assert(option_id < p.results.size(), "Option with this id does not exist");

   vote_table votes(get_self(), voter);
   eosio_assert(votes.find(p.id) == votes.end(), "This account has already voted in this poll");

   if (p.is_token_poll)
      store_token_vote(p, votes, option_id);
   else
      store_vote(p, votes, option_id, 1);

   eosio::print("Vote stored!");
}

// Macro to register the contract's actions
EOSIO_ABI(pollgf, (newpoll)(newtokenpoll)(vote))
```

### pollgf.abi

```json
{
  "types": [{
      "new_type_name": "poll_id_t",
      "type": "uint64"
    },{
      "new_type_name": "option_results",
      "type": "option_result[]"
    },{
      "new_type_name": "token_info_t",
      "type": "extended_symbol"
    },{
      "new_type_name": "symbol_name",
      "type": "symbol"
    }
  ],
  "structs": [{
      "name": "option",
      "base": "",
      "fields": [{
          "name": "name",
          "type": "string"
        }
      ]
    },{
      "name": "option_result",
      "base": "option",
      "fields": [{
          "name": "votes",
          "type": "float64"
        }
      ]
    },{
      "name": "symbol_type",
      "base": "",
      "fields": [{
          "name": "value",
          "type": "symbol_name"
        }
      ]
    },{
      "name": "extended_symbol",
      "base": "symbol_type",
      "fields": [{
          "name": "contract",
          "type": "name"
        }
      ]
    },{
      "name": "poll",
      "base": "",
      "fields": [{
          "name": "id",
          "type": "poll_id_t"
        },{
          "name": "question",
          "type": "string"
        },{
          "name": "results",
          "type": "option_results"
        },{
          "name": "is_token_poll",
          "type": "bool"
        },{
          "name": "token",
          "type": "token_info_t"
        }
      ]
    },{
      "name": "poll_vote",
      "base": "",
      "fields": [{
          "name": "pollid",
          "type": "poll_id_t"
        },{
          "name": "optionid",
          "type": "uint8"
        }
      ]
    },{
      "name": "newpoll",
      "base": "",
      "fields": [{
          "name": "question",
          "type": "string"
        },{
          "name": "creator",
          "type": "name"
        },{
          "name": "options",
          "type": "string[]"
        }
      ]
    },{
      "name": "newtokenpoll",
      "base": "",
      "fields": [{
          "name": "question",
          "type": "string"
        },{
          "name": "creator",
          "type": "name"
        },{
          "name": "options",
          "type": "string[]"
        },{
          "name": "token",
          "type": "token_info_t"
        }
      ]
    },{
      "name": "vote",
      "base": "",
      "fields": [{
          "name": "id",
          "type": "poll_id_t"
        },{
          "name": "voter",
          "type": "name"
        },{
          "name": "option_id",
          "type": "uint8"
        }
      ]
    }
  ],
  "actions": [{
      "name": "newpoll",
      "type": "newpoll",
      "ricardian_contract": ""
    },{
      "name": "newtokenpoll",
      "type": "newtokenpoll",
      "ricardian_contract": ""
    },{
      "name": "vote",
      "type": "vote",
      "ricardian_contract": ""
    }
  ],
  "tables": [{
      "name": "poll",
      "index_type": "i64",
      "key_names": [
        "id"
      ],
      "key_types": [
        "poll_id_t"
      ],
      "type": "poll"
    },{
      "name": "votes",
      "index_type": "i64",
      "key_names": [
        "id"
      ],
      "key_types": [
        "poll_id_t"
      ],
      "type": "poll_vote"
    }
  ],
  "ricardian_clauses": []
}
```
# deNotary token with pause and blacklist
## stablecoin

{% note alert %}

This smart contract is presented here as an example, do not use it for production without prior verification.

{% endnote %}

If you don't have a local deNotary node installed, use the deployment tools at docs.deNotary.io 

- Mainnet <a href="https://explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- Testnet <a href="https://dev-explorer.deNotary.io" target="_blank" rel="noreferrer noopener">Explorer</a>  
- For quick deployment to a test network, use the <a href="https://deploy.deNotary.io" target="_blank" rel="noreferrer noopener">Web Deploy</a> tools  
- You can read more about this here [Quick Start](/quick-start)  

## Files
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/stablecoin.hpp" download target="_blank" rel="noreferrer noopener">Download stablecoin.hpp</a>  
<a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/stablecoin.cpp" download target="_blank" rel="noreferrer noopener">Download stablecoin.cpp</a> 

## Brief description
stablecoin is a token contract for deNotary/EOSIO/Antelope that provides standard operations (create, issue, transfer, burn), as well as mechanisms for contract pause (pause/unpause) and account blacklist (blacklist/unblacklist). The contract stores balances in accounts, issue metadata in stat, pause status in pausetable, and blocked accounts in blacklists. stablecoin

### Features
Create a token with a given symbol, precision, and maximum emission.
Issue (mint) of tokens by the issuer; credit to the issuer's balance with an optional internal transfer to a third party.  
Transfers between accounts with checks (accounts exist, are not blocked, the contract is not paused, correct amounts/symbols).  
Burn by the issuer with a decrease in supply and max_supply.  
Pause/unpause the contract. In pause mode, user transfers should be prohibited.  
Blacklist: add/remove accounts to block any operations with the token.  
get_supply / get_balance utilities for reading the current supply and balances.  

### Tables and data structure
#### accounts
Stores the balance of each account by token symbol.  
balance (asset) вЂ” token balance; primary key вЂ” symbol.code().raw().  
stat (currency_stats)  
Token metadata by symbol:  
- supply (asset) вЂ” current supply;  
- max_supply (asset) вЂ” maximum allowed emission;
- issuer (name) вЂ” issuer (account that has the right to issue/burn).  

#### blacklists
List of blacklisted accounts:  
account (name) вЂ” blacklisted account (primary key: account.value).  

#### pausetable
Pause status:  
- id (uint64) вЂ” always 1;
- paused (bool) вЂ” true if the contract is paused.  

#### Actions
- create(issuer, maximum_supply)
- Creates an entry in stat for the token symbol.

Conditions:  
Only the contract account can call create.
maximum_supply > 0, valid symbol/asset.  
Symbol is not registered in stat yet.  

#### Example:

```bash
cleos push action stablecoin create '["issueracct","1000000.0000 STC"]' -p stablecoin@active
```
issue(to, quantity, memo)  
Issues (mint) the specified number of tokens.  

Logic:  
Only issuer from stat can issue.  
quantity > 0; symbol must match symbol from stat.  
Increases supply; in this code, when supply > max_supply overflows, it raises max_supply to the current supply (this behavior can be disabled if "limit expansion" is unacceptable).  
Adds tokens to the issuer's balance; if to != issuer, it performs an internal transfer transfer(issuer в†’ to).  

#### Example:

```bash
cleos push action stablecoin issue '["issueracct","50000.0000 STC","initial"]' -p issueracct@active
```
transfer(from, to, quantity, memo)  
Transfer tokens between accounts.  

Checks:  
Cannot transfer to yourself; from authorizes the transaction.  
Account to must exist.  
Both accounts must not be blacklisted.  
Transfers must be blocked in pause mode (see the Pause section below).  
quantity is valid, positive, and the symbol matches stat.  
Memo в‰¤ 256 bytes.  
Writes off from, credits to (RAM pays to if it authorizes; otherwise, from).  

Example:
```bash
cleos push action stablecoin transfer '["alice","bob","12.3456 STC","payment"]' -p alice@active
```
burn(quantity, memo)  
Burns tokens, reducing supply and max_supply; writes off the issuer's balance.  

Conditions:  
Only issuer can call;  
quantity > 0; does not exceed current supply.  

Example:
```bash
cleos push action stablecoin burn '["100.0000 STC","reduce supply"]' -p issueracct@active
```
pause() and unpause()  
pause() вЂ” enables pause mode: adds/updates an entry in pausetable (id=1, paused=true).  
unpause() вЂ” removes pause: clears pausetable.
Can only be called by contract account.  

Examples:

```bash
cleos push action stablecoin pause '[]' -p stablecoin@active
cleos push action stablecoin unpause '[]' -p stablecoin@active
```
> [!NOTE]
> вљ пёЏ Important about the pause check: the code implements the helper function is_paused() and a check in
> transfer. The semantics should be "if the contract is paused - prohibit the transfer". Make sure in the
> review that the condition in transfer interprets is_paused() correctly to block transfers when paused.

blacklist(account, memo) and unblacklist(account)  
blacklist - adds an account to the blacklist; contract only; memo в‰¤ 256 bytes; re-addition is prohibited.  
unblacklist - removes an account from the list; contract only; requires that the record exists.  
Accounts in the list cannot send/receive tokens.  

Examples:
```bash
cleos push action stablecoin blacklist '["badguy","fraud investigation"]' -p stablecoin@active
cleos push action stablecoin unblacklist '["badguy"]' -p stablecoin@active
```
Internal functions (balances)  
sub_balance(owner, value) вЂ” safely decreases the balance; if zero, deletes the line in accounts.  
add_balance(owner, value, ram_payer) вЂ” creates/replenishes the balance; RAM pays ram_payer.  

#### Useful static methods
get_supply(token_contract, sym_code) вЂ” reads the current offer from stat.  
get_balance(token_contract, owner, sym_code) вЂ” reads the owner balance from accounts.  

### Deployment
Build a contract with EOSIO.CDT:

```bash
eosio-cpp -abigen -o stablecoin.wasm stablecoin.cpp
```

Upload the code to the contract account:
```bash
cleos set contract stablecoin /path/to/build -p stablecoin@active
```
Create a token create, then issue an issue.

#### Sample scenarios
Project start: create в†’ issue to issuer в†’ transfer to users.  
Emergency stop of transfers: pause в†’ investigation/fixes в†’ unpause.  
Compliance: if abuse is detected вЂ” blacklist the account; after risks are removed вЂ” unblacklist.  
Submission reduction: burn at issuer.  

### Security and recommendations
Actions create, pause/unpause, blacklist/unblacklist should be called only by the contract account; issue/burn вЂ” only by the issuer.  
Test the pause logic in transfer on testnet to ensure correct blocking of transfers when paused=true.  
Monitor RAM costs during mass transfers (creating new lines in accounts).  

#### Limitations and possible improvements
Current issue behavior can automatically raise max_supply if supply exceeds the limit. If a strict limit is needed, remove this block.  
Add events/notifications (inline logging) for auditing.  
Consider roles/multisig for admin actions.  

### License
MIT or similarly permissive license.

## stablecoin.hpp

```cpp
#pragma once

#include <eosiolib/asset.hpp>
#include <eosiolib/eosio.hpp>
#include <string>

using namespace eosio;
using std::string;

/**
 * The stablecoin contract is an implementation of its own token with standard capabilities,
 * as well as support for a blacklist of accounts and contract pause.
 */
CONTRACT stablecoin : public contract {
public:
      using contract::contract;

      /**
	   * Token creation.
	   * issuer вЂ” issuer (token owner, who has the right to issue).
	   * maximum_supply вЂ” maximum token issue volume.
       */
      ACTION create( name issuer, asset maximum_supply );

      /**
       * Token emission (mint).
	   * to вЂ” recipient account.
	   * quantity вЂ” quantity of tokens.
	   * memo вЂ” arbitrary comment.
       */
      ACTION issue( name to, asset quantity, string memo );

      /**
       * Transfer tokens between accounts.
	   * from вЂ” sender.
	   * to вЂ” recipient.
	   * quantity вЂ” quantity.
	   * memo вЂ” arbitrary comment.
       */
      ACTION transfer( name from, name to, asset quantity, string memo );

      /**
	   * Token burning by the issuer.
	   * quantity вЂ” the number of tokens to be destroyed.
	   * memo вЂ” an arbitrary comment.
       */
      ACTION burn( asset quantity, string memo );

      /**
	   * Pause the contract.
	   * All transfers are blocked (except the pause/unpause method itself).
	   * Only the contract account can call.
       */
      ACTION pause();

      /**
	   * Unpause contract (allow transfers).
	   * Only contract account can call.
       */
      ACTION unpause();

      /**
	   * Adding an account to the blacklist.
	   * An account in the blacklist cannot send/receive tokens.
	   * memo вЂ” the reason for blocking.
       */
      ACTION blacklist( name account, string memo );

      /**
       * Removing an account from the blacklist.
       */
      ACTION unblacklist( name account );

      /**
       * Get the current supply (emission) of the token.
       */
      static asset get_supply( name token_contract_account,  symbol_code sym ) {
            stats statstable( token_contract_account, sym.raw() );
            const auto& st = statstable.get( sym.raw() );
            return st.supply;
      }

      /**
       * Get the balance of a specific account using the token symbol code.
       */
      static asset get_balance( name token_contract_account,  name owner, symbol_code sym ) {
            accounts accountstable( token_contract_account, owner.value );
            const auto& ac = accountstable.get( sym.raw() );
            return ac.balance;
      }

private:
      /**
	   * Account balance table.
	   * Each account and token has a balance stored.
       */
      TABLE account {
            asset       balance; // Balance in this token
            uint64_t primary_key()const { return balance.symbol.code().raw(); }
      };

      /**
	   * Table with information about each token (emission statistics).
	   * Includes supply, max_supply, issuer.
       */
      TABLE currency_stats {
            asset       supply;     // Current offer
            asset       max_supply; // Maximum permitted emission
            name        issuer;     // Token issuer
            uint64_t primary_key()const { return supply.symbol.code().raw(); }
      };

      /**
	   * Account blacklist table.
	   * Accounts from here cannot perform operations with the token.
       */
      TABLE blacklist_table {
            name      account; // Blocked account
            auto primary_key() const {  return account.value;  }
      };

      /**
       * Table for storing the contract pause status.
       */
      TABLE pause_table {
            uint64_t            id;     // Always 1, single line
            bool                paused; // True if the contract is paused
            auto primary_key() const {  return id;  }
      };

      // Definitions of multi_index tables for access within a contract
      typedef eosio::multi_index< "accounts"_n, account > accounts;
      typedef eosio::multi_index< "stat"_n, currency_stats > stats;
      typedef eosio::multi_index< "blacklists"_n, blacklist_table > blacklists;
      typedef eosio::multi_index< "pausetable"_n, pause_table > pausetable;

      /**
       * Internal method: decrease account balance (called on transfers/burning).
       */
      void sub_balance( name owner, asset value );

      /**
       * Internal method: increase account balance (called during transfers/issues).
       */
      void add_balance( name owner, asset value, name ram_payer );

      /**
       * Internal method: Check if the contract is in paused state.
       */
      bool is_paused();
};

```

## stablecoin.cpp

```cpp
#include "stablecoin.hpp"

/**
 * Action: create a new token.
 * - Only the contract itself can create a token.
 * - Checks that the parameters are correct and that there is no token with that symbol.
 */
ACTION stablecoin::create( name issuer, asset maximum_supply ) {
    require_auth( _self );

    auto sym = maximum_supply.symbol;
    eosio_assert( sym.is_valid(), "invalid symbol name" );
    eosio_assert( maximum_supply.is_valid(), "invalid supply");
    eosio_assert( maximum_supply.amount > 0, "max-supply must be positive");

    stats statstable( _self, sym.code().raw() );
    auto existing = statstable.find( sym.code().raw() );
    eosio_assert( existing == statstable.end(), "token with symbol already exists" );

    statstable.emplace( _self, [&]( auto& s ) {
       s.supply.symbol = maximum_supply.symbol; // РЅР°С‡Р°Р»СЊРЅР°СЏ СЌРјРёСЃСЃРёСЏ = 0
       s.max_supply    = maximum_supply;
       s.issuer        = issuer;
    });
}

/**
 * Action: issue new tokens.
 * - Can only be called by the token issuer.
 * - The issued amount is added to the issuer's balance and increases the total supply.
 * - Only a positive number of tokens can be issued.
 * - If the specified recipient is not the issuer, an internal transfer is immediately called.
 */
ACTION stablecoin::issue( name to, asset quantity, string memo ) {
    auto sym = quantity.symbol;
    eosio_assert( sym.is_valid(), "invalid symbol name" );
    eosio_assert( memo.size() <= 256, "memo has more than 256 bytes" );

    stats statstable( _self, sym.code().raw() );
    auto existing = statstable.find( sym.code().raw() );
    eosio_assert( existing != statstable.end(), "token with symbol does not exist, create token before issue" );
    const auto& st = *existing;

    require_auth( st.issuer );
    eosio_assert( quantity.is_valid(), "invalid quantity" );
    eosio_assert( quantity.amount > 0, "must issue positive quantity" );

    eosio_assert( quantity.symbol == st.supply.symbol, "symbol precision mismatch" );

    // We increase supply, as well as max_supply, if supply suddenly goes beyond max_supply (it can be removed if there is no need to "expand" the limit)
    statstable.modify( st, same_payer, [&]( auto& s ) {
       s.supply += quantity;
       if ( s.supply > s.max_supply ) {
           s.max_supply = s.supply;
       }
    });

    add_balance( st.issuer, quantity, st.issuer );

    if( to != st.issuer ) {
       // If the recipient is not the issuer, we transfer tokens to him (from the issuer)
       SEND_INLINE_ACTION( *this, transfer, {st.issuer, "active"_n}, {st.issuer, to, quantity, memo} );
    }
}

/**
 * Action: transfer tokens between accounts.
 * - Rejects if the contract is paused or if the sender/recipient is blacklisted.
 * - Disables transfers to yourself.
 * - Checks for the presence of the recipient account.
 */
ACTION stablecoin::transfer( name from, name to, asset quantity, string memo ) {
    eosio_assert( is_paused(), "contract is paused." );

    blacklists blacklistt(_self, _self.value);
    auto fromexisting = blacklistt.find( from.value );
    eosio_assert( fromexisting == blacklistt.end(), "account blacklisted(from)" );
    auto toexisting = blacklistt.find( to.value );
    eosio_assert( toexisting == blacklistt.end(), "account blacklisted(to)" );

    eosio_assert( from != to, "cannot transfer to self" );
    require_auth( from );
    eosio_assert( is_account( to ), "to account does not exist");
    auto sym = quantity.symbol.code();
    stats statstable( _self, sym.raw() );
    const auto& st = statstable.get( sym.raw() );

    require_recipient( from );
    require_recipient( to );

    eosio_assert( quantity.is_valid(), "invalid quantity" );
    eosio_assert( quantity.amount > 0, "must transfer positive quantity" );
    eosio_assert( quantity.symbol == st.supply.symbol, "symbol precision mismatch" );
    eosio_assert( memo.size() <= 256, "memo has more than 256 bytes" );

    auto payer = has_auth( to ) ? to : from;

    sub_balance( from, quantity );
    add_balance( to, quantity, payer );
}

/**
 * Action: Token burning.
 * - Only the issuer can burn tokens.
 * - Decreases the total supply and max_supply.
 * - Writes off tokens from the issuer's balance.
 */
ACTION stablecoin::burn(asset quantity, string memo ) {
    auto sym = quantity.symbol;
    eosio_assert( sym.is_valid(), "invalid symbol name" );
    eosio_assert( memo.size() <= 256, "memo has more than 256 bytes" );

    auto sym_name = sym.code();
    stats statstable( _self, sym_name.raw() );
    auto existing = statstable.find( sym_name.raw() );
    eosio_assert( existing != statstable.end(), "token with symbol does not exist, create token before burn" );
    const auto& st = *existing;

    require_auth( st.issuer );
    eosio_assert( quantity.is_valid(), "invalid quantity" );
    eosio_assert( quantity.amount > 0, "must burn positive or zero quantity" );

    eosio_assert( quantity.symbol == st.supply.symbol, "symbol precision mismatch" );
    eosio_assert( quantity.amount <= st.supply.amount, "quantity exceeds available supply");

    statstable.modify( st, same_payer, [&]( auto& s ) {
       s.supply -= quantity;
       s.max_supply -= quantity;
    });

    sub_balance( st.issuer, quantity );
}

/**
 * Action: Pause the contract.
 * - Only allowed by the contract account.
 * - Adds/modifies an entry in the pausetable with paused = true.
 */
ACTION stablecoin::pause() {
    require_auth( _self );

    pausetable pauset(_self, _self.value);
    auto itr = pauset.find(1);
    if (itr != pauset.end()) {
      pauset.modify(itr, _self, [&](auto& p) {
        p.paused = true;
      });
    } else {
      pauset.emplace(_self, [&](auto& p) {
        p.id = 1;
        p.paused = true;
      });
    }
}

/**
 * Action: Unpause contract (allow transfers).
 * - Only allowed for contract account.
 * - Clears pause table.
 */
ACTION stablecoin::unpause() {
    require_auth( _self );
    pausetable pauset(_self, _self.value);
    while (pauset.begin() != pauset.end()) {
      auto itr = pauset.end();
      itr--;
      pauset.erase(itr);
      pausetable pauset(_self, _self.value);
    }
}

/**
 * Action: add account to blacklist.
 * - Allowed only for contract account.
 * - Prohibits specified account from any operations with token.
 */
ACTION stablecoin::blacklist( name account, string memo ) {
    require_auth( _self );
    eosio_assert( memo.size() <= 256, "memo has more than 256 bytes" );
    
    blacklists blacklistt(_self, _self.value);
    auto existing = blacklistt.find( account.value );
    eosio_assert( existing == blacklistt.end(), "blacklist account already exists" );

    blacklistt.emplace( _self, [&]( auto& b ) {
       b.account = account;
    });
}

/**
 * Action: remove account from blacklist.
 * - Allowed only for contract account.
 */
ACTION stablecoin::unblacklist( name account) {
    require_auth( _self );

    blacklists blacklistt(_self, _self.value);
    auto existing = blacklistt.find( account.value );
    eosio_assert( existing != blacklistt.end(), "blacklist account not exists" );

    blacklistt.erase(existing);
}

/**
 * Internal method: decrease the owner account balance by value.
 * If the balance becomes zero, the record is deleted.
 */
void stablecoin::sub_balance( name owner, asset value ) {
   accounts from_acnts( _self, owner.value );

   const auto& from = from_acnts.get( value.symbol.code().raw(), "no balance object found" );
   eosio_assert( from.balance.amount >= value.amount, "overdrawn balance" );

   if( from.balance.amount == value.amount ) {
      from_acnts.erase( from );
   } else {
      from_acnts.modify( from, owner, [&]( auto& a ) {
          a.balance -= value;
      });
   }
}

/**
 * Internal method: increase owner balance by value.
 * If there was no account, a new record is created, otherwise the amount is increased.
 * ram_payer вЂ” who pays for the memory for the new record.
 */
void stablecoin::add_balance( name owner, asset value, name ram_payer ) {
   accounts to_acnts( _self, owner.value );
   auto to = to_acnts.find( value.symbol.code().raw() );
   if( to == to_acnts.end() ) {
      to_acnts.emplace( ram_payer, [&]( auto& a ){
        a.balance = value;
      });
   } else {
      to_acnts.modify( to, same_payer, [&]( auto& a ) {
        a.balance += value;
      });
   }
}

/**
 * Internal method: increase owner balance by value.
 * If there was no account, a new record is created, otherwise the amount is increased.
 * ram_payer вЂ” who pays for the memory for the new record.
 */
bool stablecoin::is_paused() {
      pausetable pauset(_self, _self.value);
      bool existing = ( pauset.find( 1 ) == pauset.end() );
      return existing;
}

/**
 * EOSIO_DISPATCH macro - registers all contract actions for external calling.
 */
EOSIO_DISPATCH( stablecoin, (create)(issue)(transfer)(burn)(pause)(unpause)(blacklist)(unblacklist) )
```
# Address

## Address Creation
```
gf.address create '[ "gf", [{ "network":"ETHEREUM", "type":"ETH", "address":"0x0000000000000000000000000000000000000001" }]]'
```
``Contract | Action | [ User | Address array ]``

## Address Update
```
gf.address update '[ "gf", [{ "network":"ETHEREUM", "type":"ETH", "address":"0x0000000000000000000000000000000000000001" }]]'
```
``Contract | Action | [ User | Address array ]``

## Address Remove
```
gf.address remove '[ "gf" ]'
```
``Contract | Action | [ User ]``

## Action '**Create**'

- **account**: Account name
- **address[]**: Address array

#### Example
```json
{
  "account": "gf",
  "address": [ 
      { 
        "network":"ETHEREUM", 
        "type":"ETH", 
        "address":"0x0000000000000000000000000000000000000001" 
      }
    ]
}
```

## Action '**Update**'

- **account**: Account name
- **address[]**: Address array

#### Example
```json
{
  "account": "gf",
  "address": [ 
      { 
        "network":"ETHEREUM", 
        "type":"ETH", 
        "address":"0x0000000000000000000000000000000000000001" 
      }
    ]
}
```

## Action '**Remove**'

- **account**: Account name

#### Example
```json
{
  "account": "gf"
}
```

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.address&scope=useraccount&table=address&json=true&lower_bound=gf&limit=1``

``https://dev-history.deNotary.io get table gf.address useraccount address``

```json
"rows": [{
    "contract": "account",
    "address": [{ 
		"network":"ETHEREUM",
		"type":"ETH",
		"address":"0xer718erb8erbr5d4bdfbdf"
	  }],						
    }
  ]
```
# Asset

## Configure the price for storing assets
```
gf.asset configure '["0.0002 DNLT", 1024, 102400]'
```
``Contract | Action | [ Price per byte | Mininmal byte size | Maximal byte size ]``

## Store asset
```
gf.asset store '[ "useraccount", "useraccount", "/9j/4AAQSkZBAQEASABIAAD/4QAiRXhbjk9eaZ" ]'
```
``Contract | Action | [ issuer | owner | base64 Asset ]``

## Destroy asset
```
gf.asset destroy '[ 1 ]'
```
``Contract | Action | [ Asset ID ]``


## Asset owner change
```
gf.asset setowner '[ 1, "useraccount" ]'
```
``Contract | Action | [ Asset ID | New Owner ]``


## Action '**Configure**'

- **price**: Price per byte
- **min_size**: Mininmal byte size (uint64)
- **max_size**: Maximal byte size (uint64)

#### Example
```json
{
    "price": "0.0002 DNLT",
	"min_size": 1024,
	"max_size": 102400
}
```

## Action '**Store**'

- **issuer**: Asset issuer
- **owner**: Asset owner
- **base64**: Asset (base64 encoding)

#### Example
```json
{
    "issuer": "useraccount",
	"owner": "useraccount",
	"base64": "/9j/4AAQSkZBAQEASABIAAD/4QAiRXhbjk9eaZ"
}
```

## Action '**Destroy**'

- **asset_id**: Asset id (uint64)

#### Example
```json
{
    "asset_id": 1
}
```

## Action '**Setowner**'

- **asset_id**: Asset id (uint64)
- **owner**: New asset owner

#### Example
```json
{
    "asset_id": 1,
    "owner": "useraccount"
}
```

## Asset Config

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.asset&scope=gf.asset&table=config&json=true&limit=1``
``https://dev-history.deNotary.io get table gf.asset gf.asset config``

```json
"rows": [{
		"id": 1,
		"pricebyte": "0.0002 DNLT",
		"min_size": 1024,
		"max_size": 409600,
		"last_update": 1728314164
	}
  ]

```

## Asset Imagestore

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.asset&scope=gf.asset&table=imagestore&json=true&limit=1``
``https://dev-history.deNotary.io get table gf.asset gf.asset imagestore``

```json
"rows": [{
		"asset_id": 1,
		"owner": "onenewaccnt1",
		"paid": "0.2544 DNLT",
		"base64": "iVBORw0KVIolgAAAABJRU5ErkJggg==",
		"last_update": 1694878787
	}
  ]
```
# DEX

## Exchange Workflow

### Creating a Pool
```
gf.dex create [ "useraccount", "gf.eth", "8,ETH", "3.2500 DNLT" ]
```
``Contract | Action | [ User | Token Account | Token Symbol | Token Price ]``

### Depositing Balance to the Exchange
```
gf.eth transfer '[ "useraccount", "gf.dex", "10.10000000 ETH", "add_balance" ]'
```
``Contract | Action | [ User | Exchange Account | Transfer Amount | Memo with Deposit Identifier ]``

### Transferring Funds from User Balance to Pool
```
gf.dex deposit '[ "useraccount", "gf.eth", "20.0000 DNLT" ]'
```
``Exchange Contract | Action | [ User | Token Account | Amount ]``

### Trading
```
eosio.token transfer '[ "useraccount", "gf.eth", "0.6000 DNLT", "gf.trx" ]'
```
``Contract | Action | [ User | Exchange Account | Exchange Amount | Memo with "Token Account for Exchange" parameters ]``
- Exchange TRX to DNLT (by market) - do not specify anything in the memo
- Exchange TRX to ETH - specify **gf.eth** (exchange contract) in the memo
-  Exchange DNLT to TRX - specify **gf.trx** (exchange contract) in the memo

### Withdrawing Free Tokens from the Exchange Balance
```
gf.dex withdraw '[ "useraccount", "gf.eth", " 0.10000000 ETH"]'
```
``Exchange Contract | Action | [ User | Contract | Withdrawal Amount from the balance table `balance.quantity` ]``


## Action '**Create**'

- **Account name**: owner
- **Contract name**: pool contract
- **Symbol ticker**: pool token symbol
- **Asset price**: starting price of the pool

#### Example
```json
{
  "account": "useraccount",
  "contract": "gf.eth",
  "ticker": "8,ETH",
  "price": "665.0000 DNLT"
}
```

After creation, the pool is available in the pools table:
```json
"rows": [{
      "contract": "gf.eth",
      "owner": "poolowneracc",
      "ticker": "6,ETH",
      "price": "72.4164 DNLT",
      "v_price": "7241641917",
      "token": "23.04200094 ETH",
      "v_token": 230420009486,
      "market": "1668.6260 DNLT",
      "v_market": "166862600000",
      "lp": 9167.968574
    }
  ]
```

## Balance Refill

- **Memo** - ``add_balance``
- **Table** - ``balance``

#### Example
``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.dex&scope=useraccount&table=balance&json=true&lower_bound=useraccount&limit=2``

```json
"rows": [{
      "contract": "gf.eth",
      "quantity": "4995.26000034 ETH",
    },{
      "contract": "eosio.token",
      "quantity": "1100.0000 DNLT"
    }
  ]

```

## Action '**Deposit**'

- **Account Name**: owner
- **Contract Name**: pool contract
- **Symbol Market**: the amount of DNLT tokens being added to the pool. The amount of paired tokens is calculated in the smart contract and deducted from the balance table.  

#### Example
```json
{  
	"account": "tokenrerere2",  
	"contract": "gf.eth",  
	"market": "105.0000 DNLT"  
}  
```

## Pooled

After adding to the pool, a new object is added to the pooled table

- **Table** - ``pooled``

#### Example

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.dex&scope=gf.eth&table=pooled&index_position=2&key_type=i64&json=true&lower_bound=testdexacco1&limit=10``

```json
"rows": [{
      "owner": "gf",
      "lp": "15253.4527 LP",
      "timestamp": 1708004454
    }
  ]

```

## Action '**Outpool**'

- **Account Name**: owner
- **Contract Name**: pool contract
- **Asset Lp**: percentage of its part of the pool in the pooled table

#### Example

```json
{  
	"account": "tokenrerere2",  
	"contract": "gf.eth",
	"quantity": "5.0000 LP"
}
```
&nbsp;
```
outpool '[ "tokenrerere2", "gf.eth", 5.00 ]'
```

## Action '**Withdraw**'

- **Account Name**: owner
- **Contract Name**: pool contract
- **Quantity**: Total sum

#### Example

```json
{  
	"account": "useraccount",  
	"contract": "eosio.token",
	"quantity": "1.0000 DNLT"
}
```
&nbsp;
```
withdraw '[ "tokenrerere2", "eosio.token", "1.0000 DNLT" ]'
```
# Fees

## Creating a record of the amount of fees
```
gf.fee create '[ "ETHEREUM", "ETH", "gf.eth", "8,ETH" ]'
```
``Contract | Action | [ Network | Network Type | Token Contract | Symbol ]``

## Updating the record of fees
```
gf.fee update '[ 2, "0.00000124 ETH" ]'
```
``Contract | Action | [ Network Id | Network Fee ]``

## Removing of fees records
```
gf.fee remove '[ 2 ]'
```
``Contract | Action | [ Network Id ]``

## Action '**Create**'

- **NETNAME**: Network name
- **TYPE**: Network type
- **contract**: Contract name
- **token**: Symbol

#### Example
```json
{
  "NETNAME": "ETHEREUM",
    "TYPE": "ETH",
    "contract": "gf.eth",
    "token": "8,ETH"
}
```

## Action '**Update**'

- **id**: Network ID (uint64)
- **fee**: Network fees

#### Example
```json
{
	"id": 2,
	"fee": "0.00000124 ETH"
}
```


## Action '**Remove**'

- **id**: Network ID (uint64)

#### Example
```json
{
	"id": 2
}
```

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.fee&scope=gf.fee&table=fees&json=true&limit=500``

```json
"rows": [{
      "id": "1",						
      "NETNAME": "ETHEREUM",
	  "TYPE": "ETH",
	  "contract": "gf.eth",
	  "fee": "0.00002400 ETH"
    }
  ]
```
# HOLD

## Stake token
```
gf.hold stake [ "useraccount", "3.2500 DNLT", "" ]
```
``Contract | Action | [ User | Token Amount, Memo (Optional) ]``

## Unstake token
```
gf.hold unstake '[ "gf", "1000000.0000 DNLT"]'
```
``Contract | Action | [ User | Token Amount ]``

## Token giveaway
```
eosio.token transfer '[ "useraccount", "gf.hold", "10.5000 DNLT", "applystake"]'
```
``Contract | Action | [ User | Stake Account | Quantity | Memo]``
## Take reward
```
gf.hold claim '[ "useraccount" ]'
```
``Exchange Contract | Action | [ User ]``

## Action '**Stake**'
- **Account from**: user
- **Quantity**: amount of tokens
- **Memo**: memo (optional)

#### Example
```json
{
  "from": "useraccount",
  "quantity": "665.0000 DNLT",
  "memo": ""
}
```

After stake balance is ready to check in table ``stake``:
``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.hold&scope=gf.hold&table=stake&json=true&lower_bound=useraccount&limit=1``

```json
"rows": [{
      "account": "useraccount",				
      "staked": "72.4164 DNLT",				
      "rewards": [{							
		"contract":"eosio.token",
		"quantity":"304029.9408 DNLT"
	  }],
      "claim": [{
		"contract":"eosio.token",
		"quantity":"113538879.3409 DNLT"
	  }],
      "unstake": "0.0000 DNLT",
      "unstake_time": "1668626000"
    }
  ]
```

## Action '**Unstake**'
- **Account from**: user
- **Quantity**: amount of tokens


#### Example
```json
{
  "from": "useraccount",
  "quantity": "665.0000 DNLT",
}
```

After unstake data is available in table ``stake``:
``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.hold&scope=gf.hold&table=stake&json=true&lower_bound=useraccount&limit=1``

```json
"rows": [{
      "account": "useraccount",		
      "staked": "72.4164 DNLT",		
      "rewards": [{					
		"contract":"eosio.token",
		"quantity":"304029.9408 DNLT"
	  }],
      "claim": [{							
		"contract":"eosio.token",
		"quantity":"113538879.3409 DNLT"
	  }],
      "unstake": "0.0000 DNLT",
      "unstake_time": "1668626000"
    }
  ]
```

## Action '**Claim**'
- **Account**: user

```json
{
  "account": "useraccount"
}
```

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.hold&scope=gf.hold&table=stake&json=true&lower_bound=useraccount&limit=1``

```json
"rows": [{
      "account": "useraccount",		
      "staked": "72.4164 DNLT",		
      "rewards": [{					
		"contract":"eosio.token",
		"quantity":"304029.9408 DNLT"
	  }],
      "claim": [{
		"contract":"eosio.token",
		"quantity":"113538879.3409 DNLT"
	  }],
      "unstake": "0.0000 DNLT",			
      "unstake_time": "1668626000"		
    }
  ]
```
# KYC

## Add check status
```
gf.kyc add '[ "useraccount", 1, "completed" ]'
```
``Contract | Action | [ User Account | KYC Level | KYC Status ]``

## Delete check status
```
gf.kyc del '[ "useraccount" ]'
```
``Contract | Action | [ User Account ]``

## Action '**Add**'

- **account**: User Account
- **level**: KYC Level (int32)
- **status**: KYC Status

#### Example
```json
{
    "account": "useraccount",
	"level": 1,
	"status": "completed"
}
```

## Action '**Del**'

- **account**: User Account

#### Example
```json
{
    "account": "useraccount"
}
```

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.kyc&scope=gf.kyc&table=accounts&json=true&lower_bound=useraccount&limit=1``
``https://dev-history.deNotary.io get table gf.kyc gf.kyc accounts``

```json
"rows": [{
		"account": "useraccount",
		"status_level1": "completed",
		"status_level2": "",
		"status_level3": ""
	}
  ]
```
# NFT

## ACTION `cncreate`
**Create a collection.**
- **Parameters:**
  - `cname` (string): Collection name.
  - `anybody` (uint64_t): 
    - `0`: Anyone can create tokens in the collection.
    - `1`: Only the creator can create tokens.
  - `owner` (name): Owner of the collection.
  - `desc` (string): Description of the collection.


## ACTION `cnsetowner`
**Transfer collection ownership.**
- **Parameters:**
  - `id` (uint64_t): Collection ID.
  - `owner` (name): New owner of the collection.

## ACTION `cnedit`
**Edit a collection.**
- **Parameters:**
  - `id` (uint64_t): Collection ID.
  - `cname` (string): New collection name.
  - `desc` (string): New collection description.


## ACTION `issuenft`
**Create an NFT.**
- **Parameters:**
  - `id` (uint64_t): Collection ID.
  - `tname` (string): Token name (not unique).
  - `creatorfee` (uint64_t): Creator fee percentage for sales.
  - `url` (string): Website URL (1вЂ“1024 characters).
  - `asset_id` (uint64_t): Asset ID.
  - `freezetime` (uint64_t): Freeze time in seconds. `0` means it's available immediately.
  - `lifetime` (uint64_t): Token lifespan in seconds. `0` means perpetual. Current time + `lifetime` = token expiration.
  - `immutable` (string): Non-updatable data (JSON).
  - `mutables` (string): Updatable data (JSON). Can be changed with `setnftmdata`.


## ACTION `burnnft`
**Burn a token.**
- **Parameters:**
  - `id` (uint64_t): Token ID.

## ACTION `setnftmdata`
**Update token data.**
- **Parameters:**
  - `id` (uint64_t): Token ID.
  - `mutables` (string): Updatable data (JSON).

## ACTION `stakenft`
**Stake a token.**
- **Parameters:**
  - `id` (uint64_t): Token ID.
  - `stake` (uint64_t): Stake flag. Set to `1`.
  - `freezetime` (uint64_t): Freeze timestamp. If staking for 1 minute, set to current timestamp + 60 seconds.

## ACTION `unstakenft`
**Unstake a token.**
- **Parameters:**
  - `id` (uint64_t): Token ID.

## ACTION `setnftowner`
**Transfer token ownership.**
- **Parameters:**
  - `id` (uint64_t): Token ID.
  - `owner` (name): New token owner.

## ACTION `sellnft`
**List a token for sale on the market.**
- **Parameters:**
  - `id` (uint64_t): Token ID.
  - `price` (asset): Sale price in the specified token. Example: `1.0000 DNLT`.
  - `token` (name): Contract for the sale. Example: `eosio.token`.


## ACTION `unsellnft`
**Remove a token from the market.**
- **Parameters:**
  - `id` (uint64_t): Token ID.

---

## Token Purchase

**To purchase a token, transfer the specified amount to the smart contract address with the token order ID in the memo.**

### Example:
- **From**: `testaccount`  
- **To**: `gf.nft`  
- **Quantity**: `1.0000 USDT`  
- **Memo**: `153`
# Price

## Adding a token for price monitoring
```
gf.price create '[ "eosio.token", "4,USDT", "4,DNLT", 4]'
```
``Contract | Action | [ Token Contract | Pair Symbol | Token Symbol | Number of decimal places ]``

## Token price update
```
gf.price update '[ "eosio.token", "0.0011 USDT"]'
```
``Contract | Action | [ Token Contract | Token Price ]``
## Token deletion
```
gf.price remove '[ "eosio.token" ]'
```
``Contract | Action | [ Token Contract ]``

## Action '**Create**'

- **contract**: Token Contract
- **token**: Pair Symbol
- **trade**: Token Symbol
- **decimal**: Number of decimal places (int)

#### Example
```json
{
    "contract": "eosio.token",
	"token": "4,DNLT",
	"trade": "",
    "decimal": 4
}
```

## Action '**Update**'

- **contract**: Token Contract
- **price**: Token Price

#### Example
```json
{
    "contract": "eosio.token",
	"price": "0.0011 USDT"
}
```

## Action '**Remove**'

- **contract**: Token Contract

#### Example
```json
{
    "contract": "eosio.token"
}
```

## Prices

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.price&scope=gf.price&table=prices&json=true&limit=500``
``https://dev-history.deNotary.io get table gf.price gf.price prices``

```json
"rows": [{
    "contract": "eosio.token",
    "trade": "DNLT",
    "decimal": 4,
    "price": "0.1005 USDT",
    "last_update": 1730100204
	}
  ]
```

## Price Rates

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.price&scope=gf.price&table=rates&json=true&lower_bound=eosio.token&limit=1``
``https://dev-history.deNotary.io get table gf.price gf.price rates``

```json
"rows": [{
    "contract": "eosio.token",
    "rate": [
			{
				"contract": "eosio.token",
				"price": "0.1005 USDT",
				"last_update": 1730100204
			}
		],
		"last_update": 1730100204
	}
  ]
```

## Price Config

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.price&scope=gf.price&table=config&json=true&limit=500``
``https://dev-history.deNotary.io get table gf.price gf.price config``

```json
 "rows": [{
		"contract": "eosio.token",
		"token": "DNLT",
		"decimal": 4,
		"networks": [
			{
				"network": "GF",
				"transfer": 0,
				"swapout": 0
			}
		]
	}
  ]
```
# Types

## Creating a network record
```
gf.types create '[ "ETHEREUM", "ETH", "https://etherscan.io/tx/","https://etherscan.io/address/" ]'
```
``Contract | Action | [ Network | Network Type | Transaction URL | Account URL ]``

## Network record update
```
gf.types update '[ "ETHEREUM", "ETH", "https://etherscan.io/tx/","https://etherscan.io/address/" ]'
```
``Contract | Action | [ Network | Network Type | Transaction URL | Account URL ]``

## Deletion of network record
```
gf.types remove '[ 1 ]''
```
``Contract | Action | [ Network ID ]``

## Action '**Create**'

- **NETNAME**: Network name
- **TYPE**: Network type
- **EXPLORER**: Transaction URL
- **ADDRESS**: Account URL

#### Example
```json
{
    "NETNAME": "ETHEREUM",
    "TYPE": "ETH",
    "EXPLORER": "https://etherscan.io/tx/",
    "ADDRESS": "https://etherscan.io/address/"
}
```

## Action '**Update**'

- **NETNAME**: Network name
- **TYPE**: Network type
- **EXPLORER**: Transaction URL
- **ADDRESS**: Account URL

#### Example
```json
{
    "NETNAME": "ETHEREUM",
    "TYPE": "ETH",
    "EXPLORER": "https://etherscan.io/tx/",
    "ADDRESS": "https://etherscan.io/address/"
}
```

## Action '**Remove**'

- **id**: Network ID (uint64)

#### Example
```json
{
    "id": 2
}
```

``https://dev-history.deNotary.io/v1/chain/get_table_rows?code=gf.types&scope=gf.types&table=types&json=true&limit=500``

``https://dev-history.deNotary.io get table gf.types gf.types types``

```json
"rows": [
	  {
		"id": 1,
		"NETNAME": "GF",
		"TYPE": "GF",
		"EXPLORER": "https://deNotary.io/transaction/",
		"ADDRESS": "https://deNotary.io/account/"
	  },
	  {
		"id": 2,
		"NETNAME": "BITCOIN",
		"TYPE": "BTC",
		"EXPLORER": "https://www.blockchain.com/btc/tx/",
		"ADDRESS": "https://www.blockchain.com/explorer/addresses/btc/"
	  }
	]
```
# History API

![Hyperion Logo](image-600.png)

## Endpoints

### /v2/history/export_actions

#### **GET**: Request Large Action Data Export
- **Tags:** history
- **Summary:** Request a large export of action data
- **Operation ID:** `exportActions`

##### Responses:
- **200:** Successful response
  - **Description:** Default Response

---

### /v2/history/get_abi_snapshot

#### **GET**: Fetch ABI at Specific Block
- **Tags:** history
- **Summary:** Fetch contract ABI at a specific block
- **Operation ID:** `getAbiSnapshot`

##### Parameters:
- `contract` (required, string): Contract account name
  - **Min Length:** 1
  - **Max Length:** 12
- `block` (optional, integer): Target block number, minimum: 1
- `fetch` (optional, boolean): Indicates whether to fetch the ABI

##### Responses:
- **200:** Successful response
  - **Description:** Default Response

---

### /v2/history/check_transaction

#### **GET**: Check if a Transaction was Included in a Block
- **Tags:** history
- **Summary:** Check the inclusion status of a transaction in a block
- **Operation ID:** `checkTransaction`

##### Parameters:
- `id` (required, string): Transaction ID
  - **Min Length:** 64
  - **Max Length:** 64

##### Responses:
- **200:** Successful response with transaction details
  - **Content:** `application/json`
  - **Schema:** [CheckTransactionResult](#checktransactionresult)

---

### /v2/history/get_actions

#### **GET**: Get Root Actions
- **Tags:** history
- **Summary:** Retrieve actions based on the notified account. This endpoint also supports generic filters based on indexed fields (e.g., `act.authorization.actor=eosio` or `act.name=delegatebw`), combined with an AND operator.
- **Operation ID:** `getActions`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `account` (optional, string): Notified account name, minLength: 1, maxLength: 12
- `track` (optional, string): Total results to track (number or true)
- `filter` (optional, string): Code:name filter, minLength: 3
- `sort` (optional, string): Sort direction
  - **Enum:** `desc`, `asc`, `1`, `-1`
- `after` (optional, string): Filter results after specified date (ISO8601 format)
- `before` (optional, string): Filter results before specified date (ISO8601 format)
- `simple` (optional, boolean): Enable simplified output mode
- `hot_only` (optional, boolean): Search only the latest hot index
- `noBinary` (optional, boolean): Exclude large binary data
- `checkLib` (optional, boolean): Perform reversibility check

##### Responses:
- **200:** Successful response containing action details
  - **Content:** `application/json`
  - **Schema:** [ActionResponse](#actionresponse)

---

### /v2/history/get_created_accounts

#### **GET**: Get Created Accounts
- **Tags:** accounts
- **Summary:** Retrieve all accounts created by a specified creator
- **Operation ID:** `getCreatedAccounts`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `account` (required, string): Creator account name, minLength: 1, maxLength: 12

##### Responses:
- **200:** Successful response containing account creation details
  - **Content:** `application/json`
  - **Schema:** [CreatedAccountsResponse](#createdaccountsresponse)

---

### /v2/history/get_creator

#### **GET**: Get Account Creator
- **Tags:** accounts
- **Summary:** Retrieve the creator of a specified account.
- **Operation ID:** `getCreator`

##### Parameters:
- `account` (required, string): The account name for which to retrieve the creator, minLength: 1, maxLength: 12

##### Responses:
- **200:** Successful response containing creator information
  - **Content:** `application/json`
  - **Schema:** [CreatorResponse](#creatorresponse)

---

### /v2/history/get_deltas

#### **GET**: Get State Deltas
- **Tags:** history
- **Summary:** Retrieve state deltas with optional filtering criteria.
- **Operation ID:** `getDeltas`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `code` (optional, string): Contract account
- `scope` (optional, string): Table scope
- `table` (optional, string): Table name
- `payer` (optional, string): Payer account
- `after` (optional, string): Filter results after specified date (ISO8601 format)
- `before` (optional, string): Filter results before specified date (ISO8601 format)
- `present` (optional, number): Delta present flag

##### Responses:
- **200:** Successful response containing state delta information
  - **Content:** `application/json`
  - **Schema:** [DeltasResponse](#deltasresponse)

---

### /v2/history/get_schedule

#### **GET**: Get Producer Schedule by Version
- **Tags:** history
- **Summary:** Retrieve the producer schedule based on a specified version or filters.
- **Operation ID:** `getSchedule`

##### Parameters:
- `producer` (optional, string): Producer to search by
- `key` (optional, string): Search by key
- `after` (optional, string): Filter results after specified date (ISO8601 format)
- `before` (optional, string): Filter results before specified date (ISO8601 format)
- `version` (optional, integer): Schedule version, minimum: 1

##### Responses:
- **200:** Successful response containing the producer schedule details
  - **Content:** `application/json`
  - **Schema:** [ScheduleResponse](#scheduleresponse)

---

### /v2/history/get_table_state

#### **GET**: Get Table State at Specific Block Height
- **Tags:** history
- **Summary:** Retrieve the state of a specified table at a certain block height.
- **Operation ID:** `getTableState`

##### Parameters:
- `code` (required, string): Contract to search by
- `table` (required, string): Table to search by
- `block_num` (optional, integer): Target block, minimum: 1
- `after_key` (optional, string): Last key for pagination

##### Responses:
- **200:** Successful response containing table state information
  - **Content:** `application/json`
  - **Schema:** [TableStateResponse](#tablestateresponse)

---

### /v2/history/get_transaction

#### **GET**: Get Transaction by ID
- **Tags:** history
- **Summary:** Retrieve all actions within a transaction by transaction ID.
- **Operation ID:** `getTransaction`

##### Parameters:
- `id` (required, string): Transaction ID
- `block_hint` (optional, integer): Block hint to speed up transaction recovery

##### Responses:
- **200:** Successful response containing transaction details
  - **Content:** `application/json`
  - **Schema:** [TransactionResponse](#transactionresponse)

---

### /v2/history/get_transaction_legacy

#### **GET**: Get Transaction by ID (Legacy)
- **Tags:** history
- **Summary:** Retrieve all actions within a transaction by transaction ID (legacy endpoint).
- **Operation ID:** `getTransactionLegacy`

##### Parameters:
- `id` (required, string): Transaction ID

##### Responses:
- **200:** Successful response containing transaction details
  - **Content:** `application/json`
  - **Schema:** [TransactionResponse](#transactionresponse)

---

### /v2/state/get_account

#### **GET**: Get Account Summary
- **Tags:** accounts
- **Summary:** Retrieve summary data of an account, including tokens and actions.
- **Operation ID:** `getAccount`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `account` (required, string): Account name, minLength: 1, maxLength: 12

##### Responses:
- **200:** Successful response containing account details
  - **Content:** `application/json`
  - **Schema:** [AccountSummaryResponse](#accountsummaryresponse)

---

### /v2/state/get_key_accounts

#### **GET**: Get Accounts by Public Key
- **Tags:** accounts
- **Summary:** Retrieve a list of accounts associated with a specific public key.
- **Operation ID:** `getKeyAccounts`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `public_key` (required, string): Public key for account lookup
- `details` (optional, boolean): Include permission details if set to true

##### Responses:
- **200:** Successful response containing account details
  - **Content:** `application/json`
  - **Schema:** [KeyAccountsResponse](#keyaccountsresponse)

#### **POST**: Get Accounts by Public Key
- **Tags:** accounts, state
- **Summary:** Retrieve accounts associated with a public key through a POST request.
- **Operation ID:** `postKeyAccounts`

##### Parameters:
- `body` (required, object): JSON object with a public key
  - **Schema**:
    - `public_key` (required, string): Public key for account lookup

##### Responses:
- **200:** Successful response containing account names
  - **Content:** `application/json`
  - **Schema:** [KeyAccountsResponse](#keyaccountsresponse)

---

### /v2/state/get_links

#### **GET**: Get Permission Links
- **Tags:** accounts
- **Summary:** Retrieve permission links for an account.
- **Operation ID:** `getPermissionLinks`

##### Parameters:
- `account` (optional, string): Account name
- `code` (optional, string): Contract name
- `action` (optional, string): Method or action name
- `permission` (optional, string): Permission name

##### Responses:
- **200:** Successful response containing permission link details
  - **Content:** `application/json`
  - **Schema:** [PermissionLinksResponse](#permissionlinksresponse)

---

### /v2/state/get_proposals

#### **GET**: Get Proposals
- **Tags:** system
- **Summary:** Retrieve a list of proposals.
- **Operation ID:** `getProposals`

##### Parameters:
- `proposer` (optional, string): Filter by proposer name
- `proposal` (optional, string): Filter by proposal name
- `account` (optional, string): Filter by requested or provided account
- `requested` (optional, string): Filter by requested account
- `provided` (optional, string): Filter by provided account
- `executed` (optional, boolean): Filter by execution status
- `track` (optional, string): Track total results (as number or "true")
- `skip` (optional, integer): Number of actions to skip, minimum: 0
- `limit` (optional, integer): Limit of actions per page, minimum: 1

##### Responses:
- **200:** Successful response containing proposal data
  - **Content:** `application/json`
  
---

### /v2/state/get_voters

#### **GET**: Get Voters
- **Tags:** system
- **Summary:** Retrieve a list of voters.
- **Operation ID:** `getVoters`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `producer` (optional, string): Filter by voted producer (comma-separated), max length: 12

##### Responses:
- **200:** Successful response containing voter data
  - **Content:** `application/json`
  - **Schema:** [VotersResponse](#votersresponse)

---

### /v2/state/get_tokens

#### **GET**: Get Tokens
- **Tags:** accounts
- **Summary:** Retrieve a list of tokens associated with an account.
- **Operation ID:** `getTokens`

##### Parameters:
- `limit` (optional, integer): Limit of results per page, minimum: 1
- `skip` (optional, integer): Number of results to skip, minimum: 0
- `account` (required, string): Account name to retrieve tokens for, min length: 1, max length: 12

##### Responses:
- **200:** Successful response containing token data
  - **Content:** `application/json`

---

### /v2/stats/get_action_usage

#### **GET**: Get Action and Transaction Stats
- **Tags:** stats
- **Summary:** Retrieve action and transaction statistics for a specific period.
- **Operation ID:** `getActionUsage`

##### Parameters:
- `period` (required, string): Time period to analyze (e.g., "1d", "1w")
- `end_date` (optional, string): End date for the analysis period
- `unique_actors` (optional, boolean): Flag to compute unique actors

##### Responses:
- **200:** Successful response containing action usage statistics
  - **Content:** `application/json`

---

### /v2/stats/get_missed_blocks

#### **GET**: Get Missed Blocks
- **Tags:** stats
- **Summary:** Retrieve missed blocks based on various filters.
- **Operation ID:** `getMissedBlocks`

##### Parameters:
- `producer` (optional, string): Filter by producer name
- `after` (optional, string): Filter by date (ISO8601) after specified date
- `before` (optional, string): Filter by date (ISO8601) before specified date
- `min_blocks` (optional, integer): Minimum blocks threshold, minimum: 1

##### Responses:
- **200:** Successful response containing missed blocks data
  - **Content:** `application/json`
  - **Schema:** [MissedBlocksResponse](#missedblocksresponse)

### /v2/stats/get_resource_usage

#### **GET**: Get Resource Usage Stats
- **Tags:** stats
- **Summary:** Retrieve resource usage statistics for a specific action.
- **Operation ID:** `getResourceUsage`

##### Parameters:
- `code` (required, string): Contract code name
- `action` (required, string): Action name to analyze

##### Responses:
- **200:** Successful response containing resource usage stats
  - **Content:** `application/json`

---

### /v1/history/get_actions

#### **POST**: Get Actions
- **Tags:** history
- **Summary:** Legacy endpoint to query actions.
- **Operation ID:** `getActions`

##### Request Body Parameters:
- `account_name` (optional, string): Notified account name, min length: 1, max length: 12
- `pos` (optional, integer): Action position for pagination
- `offset` (optional, integer): Limit of actions per page
- `filter` (optional, string): Code:name filter, min length: 3
- `sort` (optional, string): Sort direction, options: `desc`, `asc`, `1`, `-1`
- `after` (optional, string): Filter actions after specified date (ISO8601)
- `before` (optional, string): Filter actions before specified date (ISO8601)
- `parent` (optional, integer): Filter by parent global sequence, minimum: 0

##### Responses:
- **200:** Successful response containing actions data
  - **Content:** `application/json`
  - **Schema:** [ActionsResponse](#actionsresponse)
---

### /v1/history/get_controlled_accounts

#### **POST**: Get Controlled Accounts
- **Tags:** accounts
- **Summary:** Retrieve controlled accounts by specified controlling accounts.
- **Operation ID:** `getControlledAccounts`

##### Request Body Parameters:
- `controlling_account` (required, string): The controlling account name.

##### Responses:
- **200:** Successful response containing controlled accounts.
  - **Content:** `application/json`
  - **Schema:** [ControlledAccountsResponse](#controlledaccountsresponse)

---

### /v1/history/get_key_accounts

#### **POST**: Get Accounts by Public Key
- **Tags:** accounts
- **Summary:** Retrieve accounts associated with a specific public key.
- **Operation ID:** `getKeyAccounts`

##### Request Body Parameters:
- `public_key` (required, string): The public key to filter accounts.

##### Responses:
- **200:** Successful response containing account names.
  - **Content:** `application/json`
  - **Schema:** [KeyAccountsResponse](#keyaccountsresponse)

---

### /v1/history/get_transaction

#### **POST**: Get Transaction by ID
- **Tags:** history
- **Summary:** Retrieve all actions belonging to a specified transaction.
- **Operation ID:** `getTransaction`

##### Request Body Parameters:
- `id` (required, string): Transaction ID to query.
- `block_num_hint` (optional, integer): Optional block number hint.

##### Responses:
- **200:** Successful response containing transaction data.
  - **Content:** `application/json`

---

### /v1/trace_api/get_block

#### **POST**: Get Block Traces
- **Tags:** history
- **Summary:** Retrieve traces for a specified block.
- **Operation ID:** `getBlock`

##### Request Body Parameters:
- `block_num` (optional, integer): Block number to query.
- `block_id` (optional, string): Block ID to query.

##### Responses:
- **200:** Successful response containing block traces.
  - **Content:** `application/json`
  - **Schema:** [BlockTracesResponse](#blocktracesresponse)

---

### /v1/chain/abi_bin_to_json

#### **GET**: Convert ABI Binary to JSON
- **Tags:** chain
- **Summary:** Returns an object containing rows from the specified table.
- **Operation ID:** `abiBinToJson`

##### Query Parameters:
- `code` (required, string): The code of the contract.
- `action` (required, string): The action to perform.
- `binargs` (required, string): Hexadecimal arguments.

##### Responses:
- **200:** Successful response containing the requested data.
  - **Content:** `application/json`

---

#### **HEAD**: Convert ABI Binary to JSON
- Same as the GET request above.

##### Responses:
- **200:** Successful response containing the requested data.
  - **Content:** `application/json`

---

#### **POST**: Convert ABI Binary to JSON
- **Tags:** chain
- **Summary:** Returns an object containing rows from the specified table.
- **Operation ID:** `abiBinToJsonPost`

##### Request Body Parameters:
- `code` (required, string): The code of the contract.
- `action` (required, string): The action to perform.
- `binargs` (required, string): Hexadecimal arguments.

##### Responses:
- **200:** Successful response containing the requested data.
  - **Content:** `application/json`

---

### /v1/chain/abi_json_to_bin

#### **GET**: Convert JSON object to binary
- **Tags:** chain
- **Summary:** Convert JSON object to binary.
- **Operation ID:** `abiJsonToBinGet`

##### Query Parameters:
- `binargs` (required, string): Hexadecimal representation of the binary arguments. Must match the pattern `^(0x)(([0-9a-f][0-9a-f])+)?$`.

##### Responses:
- **200:** Default Response.

---

#### **HEAD**: Convert JSON object to binary
- **Tags:** chain
- **Summary:** Convert JSON object to binary.
- **Operation ID:** `abiJsonToBinHead`

##### Query Parameters:
- `binargs` (required, string): Hexadecimal representation of the binary arguments. Must match the pattern `^(0x)(([0-9a-f][0-9a-f])+)?$`.

##### Responses:
- **200:** Default Response.

---

#### **POST**: Convert JSON object to binary
- **Tags:** chain
- **Summary:** Convert JSON object to binary.
- **Operation ID:** `abiJsonToBinPost`

##### Request Body Parameters:
- `binargs` (required, string): Hexadecimal representation of the binary arguments. Must match the pattern `^(0x)(([0-9a-f][0-9a-f])+)?$`.

##### Responses:
- **200:** Default Response.

---

### /v1/chain/get_abi

#### **GET**: Retrieves the ABI for a contract based on its account name
- **Tags:** chain
- **Summary:** Retrieves the ABI for a contract based on its account name.
- **Operation ID:** `getAbiGet`

##### Query Parameters:
- `account_name` (required, string): The account name of the contract.

##### Responses:
- **200:** Default Response.

---

#### **HEAD**: Retrieves the ABI for a contract based on its account name
- **Tags:** chain
- **Summary:** Retrieves the ABI for a contract based on its account name.
- **Operation ID:** `getAbiHead`

##### Query Parameters:
- `account_name` (required, string): The account name of the contract.

##### Responses:
- **200:** Default Response.

---

#### **POST**: Retrieves the ABI for a contract based on its account name
- **Tags:** chain
- **Summary:** Retrieves the ABI for a contract based on its account name.
- **Operation ID:** `getAbiPost`

##### Request Body Parameters:
- `account_name` (required, string): The account name of the contract.

##### Responses:
- **200:** Default Response.

---

### /v1/chain/get_account

#### **GET**: Returns an object containing various details about a specific account on the blockchain.
- **Tags:** chain
- **Summary:** Returns an object containing various details about a specific account on the blockchain.
- **Operation ID:** `getAccountGet`

##### Query Parameters:
- `account_name` (required, string): The account name to retrieve details for.

##### Responses:
- **200:** Default Response.

---

#### **HEAD**: Returns an object containing various details about a specific account on the blockchain.
- **Tags:** chain
- **Summary:** Returns an object containing various details about a specific account on the blockchain.
- **Operation ID:** `getAccountHead`

##### Query Parameters:
- `account_name` (required, string): The account name to retrieve details for.

##### Responses:
- **200:** Default Response.

---

#### **POST**: Returns an object containing various details about a specific account on the blockchain.
- **Tags:** chain
- **Summary:** Returns an object containing various details about a specific account on the blockchain.
- **Operation ID:** `getAccountPost`

##### Request Body Parameters:
- `account_name` (required, string): The account name to retrieve details for.

##### Responses:
- **200:** Default Response.

---

### /v1/chain/get_activated_protocol_features

#### **GET**: Retrieves the activated protocol features for producer node
- **Tags:** chain
- **Summary:** Retrieves the activated protocol features for producer node.
- **Operation ID:** `getActivatedProtocolFeaturesGet`

##### Query Parameters:
- `lower_bound` (optional, integer): Lower bound for the query.
- `upper_bound` (optional, integer): Upper bound for the query.
- `limit` (optional, integer): The limit, default is 10.
- `search_by_block_num` (optional, boolean): Flag to indicate it should search by block number.
- `reverse` (optional, boolean): Flag to indicate it should search in reverse.

##### Responses:
- **200:** Default Response.

---

#### **HEAD**: Retrieves the activated protocol features for producer node
- **Tags:** chain
- **Summary:** Retrieves the activated protocol features for producer node.
- **Operation ID:** `getActivatedProtocolFeaturesHead`

##### Query Parameters:
- `lower_bound` (optional, integer): Lower bound for the query.
- `upper_bound` (optional, integer): Upper bound for the query.
- `limit` (optional, integer): The limit, default is 10.
- `search_by_block_num` (optional, boolean): Flag to indicate it should search by block number.
- `reverse` (optional, boolean): Flag to indicate it should search in reverse.

##### Responses:
- **200:** Default Response.

---

#### **POST**: Retrieves the activated protocol features for producer node
- **Tags:** chain
- **Summary:** Retrieves the activated protocol features for producer node.
- **Operation ID:** `getActivatedProtocolFeaturesPost`

##### Request Body Parameters:
- `lower_bound` (optional, integer): Lower bound for the query.
- `upper_bound` (optional, integer): Upper bound for the query.
- `limit` (optional, integer): The limit, default is 10.
- `search_by_block_num` (optional, boolean): Flag to indicate it should search by block number.
- `reverse` (optional, boolean): Flag to indicate it should search in reverse.

##### Responses:
- **200:** Default Response.

---

### /v1/chain/get_block

#### GET
- **Summary**: Returns an object containing various details about a specific block on the blockchain. 
- **Tags:** chain  

##### **Parameters:**
- `block_num_or_id` (string, required): Provide a `block number` or a `block id`.  

##### **Responses:**
- **200**: Default Response

---

#### HEAD
- **Summary:** Returns an object containing various details about a specific block on the blockchain.  
- **Tags:** chain  

##### **Parameters:**
- `block_num_or_id` (string, required): Provide a `block number` or a `block id`.  

##### **Responses:**
- **200**: Default Response

---

#### POST
- **Summary:** Returns an object containing various details about a specific block on the blockchain.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `block_num_or_id` (string, required): Provide a `block number` or a `block id`.  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_block_header_state

#### GET

- **Summary:** Retrieves the block header state.  
- **Tags:** chain  

##### **Parameters:**
- `block_num_or_id` (string, required): Provide a block number or a block ID.  

##### **Responses:**
- **200**: Default Response

---

##### HEAD

- **Summary:** Retrieves the block header state.  
- **Tags:** chain  

##### **Parameters:**
- `block_num_or_id` (string, required): Provide a block number or a block ID.  

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves the block header state.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `block_num_or_id` (string, required): Provide a block number or a block ID.  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_code

#### GET

- **Summary:** Retrieves contract code.  
- **Tags:** chain  

##### **Parameters:**
- `account_name` (string, required): The name of the account.  
- `code_as_wasm` (integer, required, default: 1): This must be 1 (true).  

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves contract code.  
- **Tags:** chain  

##### **Parameters:**
- `account_name` (string, required): The name of the account.  
- `code_as_wasm` (integer, required, default: 1): This must be 1 (true).  

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves contract code.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `account_name` (string, required): The name of the account.  
  - `code_as_wasm` (integer, required, default: 1): This must be 1 (true).  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_currency_balance

#### GET

- **Summary:** Retrieves the current balance.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): Currency code.  
- `account` (string, required): Account name.  
- `symbol` (string, required): Token symbol.  

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves the current balance.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): Currency code.  
- `account` (string, required): Account name.  
- `symbol` (string, required): Token symbol.  

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves the current balance.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `code` (string, required): Currency code.  
  - `account` (string, required): Account name.  
  - `symbol` (string, required): Token symbol.  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_currency_stats

#### GET

- **Summary:** Retrieves currency stats.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): Currency code.  
- `symbol` (string, required): Token symbol.  

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves currency stats.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): Currency code.  
- `symbol` (string, required): Token symbol.  

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves currency stats.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `code` (string, required): Currency code.  
  - `symbol` (string, required): Token symbol.  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_info

#### GET

- **Summary:** Returns an object containing various details about the blockchain.  
- **Tags:** chain  

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Returns an object containing various details about the blockchain.  
- **Tags:** chain  

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Returns an object containing various details about the blockchain.  
- **Tags:** chain  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_producers

#### GET

- **Summary:** Retrieves producers list.  
- **Tags:** chain  

##### **Parameters:**
- `limit` (string, optional): Total number of producers to retrieve.  
- `lower_bound` (string, optional): In conjunction with limit can be used to paginate through the results.  
- `json` (boolean, optional): Return result in JSON format.  

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves producers list.  
- **Tags:** chain  

##### **Parameters:**
- `limit` (string, optional): Total number of producers to retrieve.  
- `lower_bound` (string, optional): In conjunction with limit can be used to paginate through the results.  
- `json` (boolean, optional): Return result in JSON format.  

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves producers list.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `limit` (string, optional): Total number of producers to retrieve.  
  - `lower_bound` (string, optional): In conjunction with limit can be used to paginate through the results.  
  - `json` (boolean, optional): Return result in JSON format.  

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_raw_abi

#### GET

- **Summary:** Retrieves raw ABI for a contract based on account name.  
- **Tags:** chain  

##### **Parameters:**
- `account_name` (string, required): Account name.

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves raw ABI for a contract based on account name.  
- **Tags:** chain  

##### **Parameters:**
- `account_name` (string, required): Account name.

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves raw ABI for a contract based on account name.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `account_name` (string, required): Account name.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_raw_code_and_abi

#### GET

- **Summary:** Retrieves raw code and ABI for a contract based on account name.  
- **Tags:** chain  

##### **Parameters:**
- `account_name` (string, required): Account name.

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves raw code and ABI for a contract based on account name.  
- **Tags:** chain  

##### **Parameters:**
- `account_name` (string, required): Account name.

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves raw code and ABI for a contract based on account name.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `account_name` (string, required): Account name.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_scheduled_transaction

#### GET

- **Summary:** Retrieves the scheduled transaction.  
- **Tags:** chain  

##### **Parameters:**
- `lower_bound` (string, optional): Date/time string in the format YYYY-MM-DDTHH:MM:SS.sss.
- `limit` (integer, optional): The maximum number of transactions to return.
- `json` (boolean, optional): Whether the packed transaction is converted to JSON.

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves the scheduled transaction.  
- **Tags:** chain  

##### **Parameters:**
- `lower_bound` (string, optional): Date/time string in the format YYYY-MM-DDTHH:MM:SS.sss.
- `limit` (integer, optional): The maximum number of transactions to return.
- `json` (boolean, optional): Whether the packed transaction is converted to JSON.

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves the scheduled transaction.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `lower_bound` (string, optional): Date/time string in the format YYYY-MM-DDTHH:MM:SS.sss.
  - `limit` (integer, optional): The maximum number of transactions to return.
  - `json` (boolean, optional): Whether the packed transaction is converted to JSON.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_table_by_scope

#### GET

- **Summary:** Retrieves table scope.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): Name of the contract to return table data for.
- `table` (string, optional): Filter results by table.
- `lower_bound` (string, optional): Filters results to return the first element that is not less than the provided value in the set.
- `upper_bound` (string, optional): Filters results to return the first element that is greater than the provided value in the set.
- `limit` (integer, optional): Limit the number of results returned.
- `reverse` (boolean, optional): Reverse the order of returned results.

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Retrieves table scope.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): Name of the contract to return table data for.
- `table` (string, optional): Filter results by table.
- `lower_bound` (string, optional): Filters results to return the first element that is not less than the provided value in the set.
- `upper_bound` (string, optional): Filters results to return the first element that is greater than the provided value in the set.
- `limit` (integer, optional): Limit the number of results returned.
- `reverse` (boolean, optional): Reverse the order of returned results.

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Retrieves table scope.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `code` (string, required): Name of the contract to return table data for.
  - `table` (string, optional): Filter results by table.
  - `lower_bound` (string, optional): Filters results to return the first element that is not less than the provided value in the set.
  - `upper_bound` (string, optional): Filters results to return the first element that is greater than the provided value in the set.
  - `limit` (integer, optional): Limit the number of results returned.
  - `reverse` (boolean, optional): Reverse the order of returned results.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/get_table_rows

#### GET

- **Summary:** Returns an object containing rows from the specified table.  
- **Tags:** chain  

##### **Parameters:**
- `code` (string, required): The name of the smart contract that controls the provided table.
- `table` (string, required): The name of the table to query.
- `scope` (string, optional): The account to which this data belongs.
- `index_position` (string, optional): Position of the index used; accepted parameters: `primary`, `secondary`, `tertiary`, `fourth`, `fifth`, `sixth`, `seventh`, `eighth`, `ninth`, `tenth`.
- `key_type` (string, optional): Type of key specified by index_position (e.g., `uint64_t` or `name`).
- `encode_type` (string, optional): Encoding type.
- `upper_bound` (string, optional): Upper bound for the query.
- `lower_bound` (string, optional): Lower bound for the query.

##### **Responses:**
- **200**: Default Response

---

#### HEAD

- **Summary:** Returns an object containing rows from the specified table.  
- **Tags:** chain  

##### **Parameters:** (Same as GET)

##### **Responses:**
- **200**: Default Response

---

#### POST

- **Summary:** Returns an object containing rows from the specified table.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `code` (string, required): The name of the smart contract that controls the provided table.
  - `table` (string, required): The name of the table to query.
  - `scope` (string, optional): The account to which this data belongs.
  - `index_position` (string, optional): Position of the index used.
  - `key_type` (string, optional): Type of key specified by index_position.
  - `encode_type` (string, optional): Encoding type.
  - `upper_bound` (string, optional): Upper bound for the query.
  - `lower_bound` (string, optional): Lower bound for the query.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/push_transaction

#### POST

- **Summary:** This method expects a transaction in JSON format and will attempt to apply it to the blockchain.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `signatures` (array, required): Array of signatures required to authorize the transaction.
  - `compression` (boolean, optional): Compression used, usually false.
  - `packed_context_free_data` (string, optional): JSON to hex.
  - `packed_trx` (string, required): Transaction object JSON to hex.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/push_transactions

#### POST

- **Summary:** This method expects a transaction in JSON format and will attempt to apply it to the blockchain.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `expiration` (integer, required): Transaction expiration time.
  - `ref_block_num` (integer, required): Reference block number.
  - `ref_block_prefix` (integer, required): Reference block prefix.
  - `max_net_usage_words` (integer, required): Maximum net usage in words.
  - `max_cpu_usage_ms` (integer, required): Maximum CPU usage in milliseconds.
  - `delay_sec` (integer, required): Delay in seconds.
  - `context_free_actions` (array, optional): Context-free actions.
  - `actions` (array, required): Actions to be executed.
  - `transaction_extensions` (array, optional): Transaction extensions.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/send_transaction

#### POST

- **Summary:** This method expects a transaction in JSON format and will attempt to apply it to the blockchain.  
- **Tags:** chain  

##### **Parameters:**
- **Body** (object, required):
  - `signatures` (array, required): Array of signatures required to authorize the transaction.
  - `compression` (boolean, optional): Compression used, usually false.
  - `packed_context_free_data` (string, optional): JSON to hex.
  - `packed_trx` (string, required): Transaction object JSON to hex.

##### **Responses:**
- **200**: Default Response

---

### /v1/chain/*

#### GET  

- **Summary:** Wildcard chain API handler.  
- **Responses:**
  - **200**: Default Response

---

#### POST  

- **Summary:** Wildcard chain API handler.  
- **Responses:**
  - **200**: Default Response

---

### /v1/node/get_supported_apis

#### GET  

- **Summary:** Get list of supported APIs.  
- **Responses:**
  - **200**: Default Response


## Schemas

### **CheckTransactionResult**
- **Description:** Server response for checking transaction inclusion
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `id` (string): Transaction ID
  - `status` (string): Transaction status
  - `block_num` (number): Block number containing the transaction
  - `root_action` (object): Root action details
    - **Properties**:
      - `account` (string): Account name
      - `name` (string): Action name
      - `authorization` (array): List of authorizations
        - **Items** (object):
          - `actor` (string): Actor name
          - `permission` (string): Permission level
      - `data` (string): Action data
  - `signatures` (array): List of transaction signatures
    - **Items** (string): Signature string

---

### **ActionResponse**
- **Description:** Server response for retrieving root actions
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `simple_actions` (array): Array of simplified action objects
    - **Items**:
      - `block` (number): Block number
      - `timestamp` (string): Action timestamp
      - `irreversible` (boolean): Irreversibility status
      - `contract` (string): Contract name
      - `action` (string): Action name
      - `actors` (string): List of actors
      - `notified` (string): Notified account
      - `transaction_id` (string): Transaction ID
      - `data` (object): Additional action data (key-value pairs)
  - `actions` (array): Array of action objects
    - **Items**:
      - `@timestamp` (string): Timestamp of action creation
      - `timestamp` (string): Action timestamp
      - `block_num` (number): Block number
      - `block_id` (string): Block ID
      - `trx_id` (string): Transaction ID
      - `act` (object): Action details
        - **Properties**:
          - `account` (string): Account name
          - `name` (string): Action name
          - `authorization` (array): List of authorizations
            - **Items**:
              - `actor` (string): Actor name
              - `permission` (string): Permission level
      - `receipts` (array): Action receipts
        - **Items**:
          - `receiver` (string): Receiver name
          - `global_sequence` (number): Global sequence number
          - `recv_sequence` (number): Receiver sequence number
          - `auth_sequence` (array): Authorization sequences
            - **Items**:
              - `account` (string): Account name
              - `sequence` (number): Sequence number
      - `cpu_usage_us` (number): CPU usage in microseconds
      - `net_usage_words` (number): Network usage in words
      - `account_ram_deltas` (array): Account RAM deltas
        - **Items**:
          - `account` (string): Account name
          - `delta` (number): RAM delta
      - `global_sequence` (number): Global sequence number
      - `producer` (string): Producer name
      - `parent` (number): Parent block number
      - `action_ordinal` (number): Action ordinal
      - `creator_action_ordinal` (number): Creator action ordinal
      - `signatures` (array): List of signatures
        - **Items** (string): Signature

---

### **CreatedAccountsResponse**
- **Description:** Server response for retrieving created accounts
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `query_time` (number): Total query time
  - `accounts` (array): List of created account objects
    - **Items**:
      - `name` (string): Account name
      - `timestamp` (string): Account creation timestamp
      - `trx_id` (string): Transaction ID

---

### **CreatorResponse**
- **Description:** Server response for retrieving account creator information
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `account` (string): Account name
  - `creator` (string): Creator account name
  - `timestamp` (string): Account creation timestamp
  - `block_num` (integer): Block number
  - `trx_id` (string): Transaction ID
  - `indirect_creator` (string): Indirect creator account name

---

### **DeltasResponse**
- **Description:** Server response for retrieving state deltas
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `deltas` (array): List of delta objects
    - **Items**:
      - `timestamp` (string): Delta timestamp
      - `present` (number): Delta present flag
      - `code` (string): Contract account
      - `scope` (string): Table scope
      - `table` (string): Table name
      - `primary_key` (string): Primary key
      - `payer` (string): Payer account
      - `block_num` (number): Block number
      - `block_id` (string): Block ID
      - `data` (object): Delta data, additional properties allowed

---

### **ScheduleResponse**
- **Description:** Server response for retrieving producer schedule by version
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `timestamp` (string): Schedule timestamp
  - `block_num` (number): Block number
  - `version` (number): Schedule version
  - `producers` (array): List of producer objects
    - **Items**:
      - `producer_name` (string): Name of the producer
      - `block_signing_key` (string): Block signing key of the producer
      - `legacy_key` (string): Legacy key of the producer

---

### **TableStateResponse**
- **Description:** Server response for retrieving the state of a table at a specific block height
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `code` (string): Contract code
  - `table` (string): Table name
  - `block_num` (number): Block number
  - `after_key` (string): Last key for pagination
  - `next_key` (string): Next key for pagination
  - `results` (array): List of state entries
    - **Items**:
      - `scope` (string): Table scope
      - `primary_key` (string): Primary key
      - `payer` (string): Payer account
      - `timestamp` (string): Entry timestamp
      - `block_num` (number): Block number
      - `block_id` (string): Block ID
      - `present` (number): Present flag
      - `data` (object): Additional data, additional properties allowed
---

### **TransactionResponse**
- **Description:** Server response for retrieving transaction details by ID
- **Type:** object
- **Properties**:
  - **Content depends on transaction details and may vary per implementation**

---

### **AccountSummaryResponse**
- **Description:** Server response for retrieving an account summary
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `account` (object): Account details with additional properties allowed
  - `links` (array): List of account link objects
    - **Items**:
      - `timestamp` (string): Link timestamp
      - `permission` (string): Permission level
      - `code` (string): Linked contract code
      - `action` (string): Linked action
  - `tokens` (array): List of token objects
    - **Items**:
      - `symbol` (string): Token symbol
      - `precision` (integer): Decimal precision of token
      - `amount` (number): Token amount
      - `contract` (string): Contract of the token
  - `total_actions` (number): Total actions count
  - `actions` (array): List of action objects
    - **Items**:
      - `@timestamp` (string): Action timestamp
      - `timestamp` (string): Action timestamp (legacy)
      - `block_num` (number): Block number of action
      - `block_id` (string): Block ID
      - `trx_id` (string): Transaction ID
      - `act` (object): Action details
        - **Properties**:
          - `account` (string): Account responsible for action
          - `name` (string): Action name
          - `authorization` (array): Authorization details
            - **Items**:
              - `actor` (string): Authorizing account
              - `permission` (string): Permission level
      - `receipts` (array): Receipt objects associated with action
        - **Items**:
          - `receiver` (string): Receiving account
          - `global_sequence` (number): Global sequence number
          - `recv_sequence` (number): Receive sequence number
          - `auth_sequence` (array): Authorization sequences
            - **Items**:
              - `account` (string): Authorizing account
              - `sequence` (number): Sequence number
      - `cpu_usage_us` (number): CPU usage in microseconds
      - `net_usage_words` (number): Net usage in words
      - `account_ram_deltas` (array): RAM deltas associated with account
        - **Items**:
          - `account` (string): Account affected by RAM delta
          - `delta` (number): RAM delta amount
      - `global_sequence` (number): Global sequence number
      - `producer` (string): Producing account
      - `parent` (number): Parent sequence number
      - `action_ordinal` (number): Action ordinal in transaction
      - `creator_action_ordinal` (number): Ordinal of creator action in transaction
      - `signatures` (array): List of transaction signatures
        - **Items**: String representing a signature

---

### **KeyAccountsResponse**
- **Description:** Server response containing account names and optional permission details linked to a public key
- **Type:** object
- **Properties**:
  - `account_names` (array): List of account names associated with the public key
    - **Items**: string representing an account name
  - `permissions` (array, optional): Permission details if `details` parameter is true
    - **Items**:
      - `owner` (string): Owner of the permission
      - `block_num` (integer): Block number associated with the permission
      - `parent` (string): Parent permission
      - `last_updated` (string): Last updated timestamp
      - `auth` (object): Authorization details
      - `name` (string): Permission name
      - `present` (number): Presence indicator

---

### **PermissionLinksResponse**
- **Description:** Server response containing permission link information
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Cached result status
  - `hot_only` (boolean): Hot-only flag
  - `lib` (number): Last irreversible block number
  - `total` (object): Total object
    - **Properties**:
      - `value` (number): Total value
      - `relation` (string): Relation description
  - `links` (array): List of permission link objects
    - **Items**:
      - `block_num` (number): Block number associated with the link
      - `timestamp` (string): Link timestamp
      - `account` (string): Account name associated with the link
      - `permission` (string): Permission name
      - `code` (string): Contract code
      - `action` (string): Linked action
      - `irreversible` (boolean): Whether the link is irreversible

---

### **VotersResponse**
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query time in milliseconds
  - `cached` (boolean): Indicates if result was cached
  - `hot_only` (boolean): Hot-only status
  - `lib` (number): Last irreversible block number
  - `total` (object): Total results
    - `value` (number): Total count
    - `relation` (string): Description of relation
  - `voters` (array): List of voter objects
    - **Items**:
      - `account` (string): Voter account name
      - `weight` (number): Voting weight
      - `last_vote` (number): Last vote timestamp
      - `data` (object): Additional data (key-value pairs)

---

### **MissedBlocksResponse**
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Query execution time in milliseconds
  - `cached` (boolean): Whether the data is cached
  - `hot_only` (boolean): Hot-only data status
  - `lib` (number): Last irreversible block number
  - `total` (object): Total results
    - `value` (number): Count of results
    - `relation` (string): Relation to the total count
  - `stats` (object): Statistics, including data by producer
  - `events` (array): List of missed block events
    - **Items**:
      - `@timestamp` (string): Timestamp of the event
      - `last_block` (number): Last block number
      - `schedule_version` (number): Version of the schedule
      - `size` (number): Size of the missed block data
      - `producer` (string): Producer who missed the block

---

### **ActionsResponse**
- **Type:** object
- **Properties**:
  - `query_time` (number): Time taken for the query
  - `last_irreversible_block` (number): Last irreversible block number
  - `actions` (array): List of action details
    - **Items**:
      - `account_action_seq` (number): Account action sequence
      - `global_action_seq` (number): Global action sequence
      - `block_num` (number): Block number
      - `block_time` (string): Block time
      - `action_trace` (object): Trace data of the action
        - `action_ordinal` (number): Ordinal of the action
        - `creator_action_ordinal` (number): Ordinal of creator action
        - `receipt` (object): Receipt information
          - `receiver` (string): Receiver name
          - `global_sequence` (number): Global sequence number
          - `recv_sequence` (number): Receiver sequence
          - `auth_sequence` (array): Authorization sequence data
        - `receiver` (string): Receiver of the action
        - `act` (object): Action data
          - `account` (string): Account involved
          - `name` (string): Name of the action
          - `authorization` (array): Authorization details
          - `data` (object): Additional data
          - `hex_data` (string): Hexadecimal representation of data
        - `trx_id` (string): Transaction ID
        - `block_num` (number): Block number where action occurred
        - `block_time` (string): Block time in ISO8601 format

---

### ControlledAccountsResponse
- **Type:** object
- **Properties**:
  - `controlled_accounts` (array): List of controlled accounts.
    - **Items**: (string)

---

### KeyAccountsResponse
- **Type:** object
- **Properties**:
  - `account_names` (array): List of account names associated with the public key.
    - **Items**: (string)

---

### BlockTracesResponse
- **Type:** object
- **Properties**:
  - `query_time_ms` (number): Time taken to execute the query in milliseconds.
  - `cached` (boolean): Whether the response was cached.
  - `hot_only` (boolean): Whether only hot data is included.
  - `lib` (number): Last irreversible block number.
  - `total` (object): Total results.
    - `value` (number): Count of results.
    - `relation` (string): Relation to the total count.
  - `id` (string): Block ID.
  - `number` (integer): Block number.
  - `previous_id` (string): Previous block ID.
  - `status` (string): Block status.
  - `timestamp` (string): Block timestamp in ISO8601 format.
  - `producer` (string): Block producer.
  - `transactions` (array): List of transactions in the block.
    - **Items**:
      - `id` (string): Transaction ID.
      - `actions` (array): List of actions within the transaction.
        - **Items**:
          - `receiver` (string): Receiver of the action.
          - `account` (string): Account initiating the action.
          - `action` (string): Name of the action.
          - `authorization` (array): Authorization details.
            - **Items**:
              - `account` (string): Authorized account.
              - `permission` (string): Required permission.
          - `data` (object): Additional data associated with the action.

## Credits

Made with в™ҐпёЏ by [EOS Rio](https://eosrio.io/)
# NFT API

## Servers
- **Production:** `https://history.deNotary.io/api/nft`
- **Development:** `https://dev-history.deNotary.io/api/nft`

## Endpoints

### /search

#### **GET**: Find NFT
- **Tags:** NFT search
- **Summary:** Find NFT by various filters and search parameters
- **Operation ID:** `getOrderById`

##### Parameters:
- `by` (required, string, default: `tid`): Filter by specific fields such as `tid`, `cid`, `towner`, `tcreator`, `asset_id`, `sell`, `tstake`, `tfreezetime`, `tlifetime`
  - **Enum:** `tid`, `cid`, `towner`, `tcreator`, `asset_id`, `sell`, `tstake`, `tfreezetime`, `tlifetime`
- `query` (required, string): Search query (e.g., nameaccount)
- `limit` (required, integer): Limit number of results, min: 0, max: 100
- `position` (required, integer): Position in pagination, min: 0
- `sort` (required, string, default: `desc`): Sorting direction
  - **Enum:** `desc`, `asc`
- `sort_key` (optional, string): Sort by field (e.g., `cid`, `towner`, `tcreator`, `asset_id`, etc.)
- `sort_value` (optional, string): Filter value used with `sort_key` (e.g., testtestte44)
- `asset` (optional, boolean): When `true`, response will not contain base64 encoded image

##### Responses:
- **200:** Successful response containing a list of NFT objects.
  - **Content:** `application/json`
  - **Schema:** `NFTresult`

---

### /market

#### **GET**: Collections on market
- **Tags:** NFT collections on market
- **Summary:** Fetch NFT collections on the market
- **Operation ID:** `getMarket`

##### Parameters:
- `limit` (required, integer): Limit number of results, min: 0, max: 100
- `position` (required, integer): Position in pagination, min: 0
- `sort` (required, string, default: `desc`): Sorting direction
  - **Enum:** `desc`, `asc`

##### Responses:
- **200:** Successful response containing a list of NFT collections.
  - **Content:** `application/json`
  - **Schema:** `MARKETresult`

---

### Schemas

#### **NFTresult**
- **Description:** Server response for the NFT search
- **Type:** object
- **Properties:**
  - `total` (integer): Total count of NFTs, example: 18
  - `result` (array): List of NFT objects
    - **Items:** `NFTobject`

#### **MARKETresult**
- **Description:** Server response for market collections
- **Type:** object
- **Properties:**
  - `total` (integer): Total count of collections, example: 18
  - `result` (array): List of market objects
    - **Items:** `MARKETobject`

#### **NFTobject**
- **Description:** NFT object
- **Type:** object
- **Properties:**
  - `tid` (integer): Unique token ID, example: 977
  - `cid` (integer): Collection ID, example: 2
  - `tname` (string): Token name, example: Super Awesome Meme Token
  - `cname` (string): Collection name (max: 128 characters), example: Simple Collections
  - `cdesc` (string): Collection description (max: 1024 characters), example: Descr Collections
  - `cowner` (string): Collection owner, example: testtestte44
  - `towner` (string): Token owner, example: testtestte44
  - `tcreator` (string): Token creator, example: testtestte44
  - `tcreatorfee` (integer): Creator fee percentage, example: 0
  - `turl` (string): URL in token description (optional), example: https://my-aswesome-token.com
  - `asset_id` (integer): Asset ID, example: 1021
  - `base64` (string): Base64 encoded image string, example: iVBORw0KGgoAAAANSUhEUgAAA9QAAAN
  - `sell` (integer): Market flag: 1 if listed for sale, example: 0
  - `price` (string): Sale price, example: 1.0000 DNLT
  - `order_id` (integer): Order ID, example: 23
  - `token` (string): Token account, example: eosio.token
  - `tstake` (integer): Stake flag: 1 if staked, example: 0
  - `tfreezetime` (integer): Freeze time in seconds, example: 0
  - `tlifetime` (integer): Token lifetime in seconds, example: 0
  - `idata` (string): Non-overwritable JSON string, example: {}
  - `mdata` (string): Overwritable JSON string, example: {}
  - `last_update` (integer): Token creation timestamp, example: 1694877432

#### MARKETobject
- **Description:** Market collection object
- **Type:** object
- **Properties:**
  - `cid` (integer): Unique collection ID, example: 2
  - `anybody` (integer): Flag for public token creation: 1 if any user can create tokens, example: 0
  - `cname` (string): Collection name, example: Test collection
  - `cocdescwner` (string): Collection owner, example: testtestte44
  - `cdesc` (string): Collection description, example: testtestte44
  - `last_update` (integer): Last update timestamp, example: 1694877432

---
### Example Response Objects:

#### NFT Search Response Example (`NFTresult`)
```json
{
  "total": 18,
  "result": [
    {
      "tid": 977,
      "cid": 2,
      "tname": "Meme NFT Card",
      "cname": "Simple Collections",
      "cdesc": "Descr Collections",
      "cowner": "testtestte44",
      "towner": "testtestte44",
      "tcreator": "testtestte44",
      "tcreatorfee": 0,
      "turl": "https://your-meme.com",
      "asset_id": 1021,
      "base64": "iVBORw0KGgoAAAANSUhEUgAAA9QAAAN",
      "sell": 0,
      "price": "1.0000 DNLT",
      "order_id": 23,
      "token": "eosio.token",
      "tstake": 0,
      "tfreezetime": 0,
      "tlifetime": 0,
      "idata": "{}",
      "mdata": "{}",
      "last_update": 1694877432
    }
  ]
}
```
---

#### NFT Market Collections Example (`MARKETresult`)
```json
{
  "total": 18,
  "result": [
    {
      "cid": 2,
      "anybody": 0,
      "cname": "Test colletion",
      "cocdescwner": "testtestte44",
      "cdesc": "testtestte44",
      "last_update": 1694877432
    }
  ]
}
```
# Quick Start

## Attention 

This Quick Start is intended for informational use only. Use local libraries and tools in production and development. 

If you want to go straight to local development without learning the basics, go to [Local Development](/quick-start/05_local-development). 

Also, do not use `deploy.deNotary.io` For development or production, this site was created solely to familiarize with the process of publishing a smart contract on the deNotary blockchain. Sincerely, the development team.

## Introduction

deNotary is one of the most performant blockchains in the world.
It is capable of processing 10,000+ transactions per second, with minimal fees and near-instant confirmation times. 

Before you begin, you should have a basic understanding of blockchain technology and deNotary.
If you are new to blockchain, check out our [Core Concepts](/core-concepts/blockchain-basics/10_decentralization) section
which dives into the knowledge you need to get off on the right foot.

Check out the [next section](/quick-start/02_setup) to install wallet app and setup it.


# Setup

## Install the wallet app

First you need to install the wallet app. 

Below is a list of supported platforms. 

Install it and follow the instructions to create or restore a wallet.

Official download page: <a href="https://explorer.deNotary.io/wallet" target="_blank" rel="noreferrer noopener">explorer.deNotary.io/wallet</a>

---

### рџ“± Android

1. Go to the page <a href="https://explorer.deNotary.io/wallet" target="_blank" rel="noreferrer noopener">deNotary Wallet</a>.  
2. Click the button **Google Play** or **Galaxy Store** (if u use Samsung Phone).  
3. In the store that opens, tap **Install**.  
4. After installation, open the app and create or import a wallet.

---

### рџ“± iOS (iPhone, MacOS m-series chips')
1. Go to the page <a href="https://explorer.deNotary.io/wallet" target="_blank" rel="noreferrer noopener">deNotary Wallet</a>.  
2. Click the button **App Store**.  
3. In the Apple Store, tap **Download** and confirm the installation. 
4. After installation, open the app and create or import a wallet.

---

### рџ’» Windows
1. Go to the page <a href="https://explorer.deNotary.io/wallet" target="_blank" rel="noreferrer noopener">deNotary Wallet</a>.  
2. Click the button **Download for Windows**.  
3. In the store that opens, tap **Download**.
5. After installation, open the app and create or import a wallet.

## Preparing a wallet for smart contract Deploy

You will need a deNotary testnet account.

In the application, at the top of the screen, you will see your currently selected network. 

Make sure that it is a TestNet, otherwise change the network.

To change the network, click on the name of the current network and select TestNet

Follow the wallet instructions to log in to TestNet

## Enabling the Wallet Connect feature

After you have logged in to Testnet, you need to enable the Wallet Connect feature.

To do this, you need to click on the button <img alt="wifi icon" src="image-wifi.png" style="width:24px" />

Then you will see the Wallet Connect page.

To enable the feature, switch the Wallet Connect toggle switch to the enabled state.


Check out the [next section](/quick-start/03_write-a-contract) to get started with your first smart contract.



# Write a Contract

In this guide we're going to create a simple smart contract that will allow us to store a string in the blockchain.
This will teach you some of the basics of smart contract development on deNotary.

## Create your first Smart Contract

You can think of a Smart Contract like a function that runs on the blockchain. It must be **deterministic**, meaning
that it will always produce the same output given the same input. This is required so that all nodes on the network
can agree on the output of the function.

```cpp
#include <eosio/eosio.hpp>
using namespace eosio;

CONTRACT mycontract : public contract {
  public:
    using contract::contract;

    TABLE StoredData {
      uint64_t id;
      std::string text;
      
      uint64_t primary_key() const { return id; }
    };
    
    using storage_table = multi_index<"mytable"_n, StoredData>;

    ACTION save( uint64_t id, std::string text ) {
      storage_table _storage( get_self(), get_self().value );
      _storage.emplace( get_self(), [&]( auto& row ) {
        row.id = id;
        row.text = text;
      });
    }
};
```

Take a look at the code and see if you can figure out what it's doing. 

Here's the basic gist of it:
- You created a new contract called `mycontract`
- A table model called `StoredData`
- A table called `mytable` to store your `StoredData` records
- An action called `save` that will allow you to save a string to the table

If you're having trouble understanding the code, don't worry, you can head over to the [Smart Contract Basics](/smart-contracts/01_contract-anatomy)
section to learn more about the various parts of a smart contract and how they work.

Head over to the [next section](/quick-start/04_build-and-deploy) to see how we can deploy this to a testnet with a few clicks.
# Build & Deploy

In the previous section we wrote a simple smart contract. In this section we will build and deploy it to the blockchain
using the deNotary Web Deploy.

## What does a Smart Contract build to?

When you build a smart contract, it will produce two files:
- `mycontract.wasm` - This is the compiled WebAssembly code that will run on the blockchain.
- `mycontract.abi` - This is the ABI file that describes the interface to your smart contract.

## What is an ABI?

ABI stands for Application Binary Interface. It is a file that describes the interface to your smart contract. It
contains information about the functions that your smart contract exposes, and the parameters that they take.

It also contains information about the data structures that your smart contract uses, and how they are stored in the
blockchain. For instance, what tables are available, and what fields are in those tables.

## What is WebAssembly?

WebAssembly is a binary instruction format for a stack-based virtual machine. It is designed as a portable target for
compilation of high-level languages like C/C++/Rust, enabling deployment on the web for client and server applications.

## Download source code

Go ahead and download the following code: <a href="https://raw.githubusercontent.com/deNotaryIO/example-smart-contracts/refs/heads/main/save_string/mycontract.cpp" download="mycontract.cpp" target="_blank" rel="noreferrer noopener">Download code</a>

This is the code that we reviewed earlier

{% note tip %}

New browser window opens after clicking on the link. Right-click in the window that opens and select (Save As). This action will save the file to your device.

{% endnote %}

## Let's build!

<a href="https://deploy.deNotary.io/" target="_blank" rel="noreferrer noopener">Open the deNotary deploy web site</a>

Click `Add Files to build`, updload file `mycontract.cpp` the one you downloaded earlier

Select entry file `mycontract.cpp`for build from the list.

Click `Build Contract`

If the build **succeeds**, you will see the wasm and abi files.

If the build **fails**, you will see the error message, with the line number where the error occurred.

## Wallet connection processes

{% note alert %}

If you missed the setup section, go back to it, install and setup the recommended wallet. 

{% endnote %}

Link to [Setup section](/quick-start/02_setup)

Go ahead.

   1. Click <img alt="fingerprint icon" src="image-fingerscan.png" style="width:24px" /> in the top-right corner or `Connect Wallet`.

   2. **The wallet connection widget** will appear with two options:  
      - рџ“± **QR Code** вЂ” to connect from another device.  
      - рџ’» **Open App** вЂ” to connect using a locally installed application.  

      {% note tip %}

      A locally installed application is one installed on the same device youвЂ™ll use to connect to the DApp via Wallet Connect.

      {% endnote %}

      **If the app is installed locally** в†’ click **Open App**.  


      **If itвЂ™s on another device** в†’  
         - рџ“· Scan the QR code with your camera (if QR scanning is supported).  
         - If not, log in wallet app, open the **Wallet Connect** menu <img alt="wifi icon" src="image-wifi.png" style="width:24px" /> and select **Scan QR Code for Connect**.  

   5. **Start the connection** using any method.  

   6. рџ”ђ If you are not logged in yet then Log in to your account, or create/restore one. 

   вљ  If prompted to **switch networks**, confirm order. 

   8. вњ… Complete the connection by accepting the **Wallet Connect** request.

   {% note alert %}

   Make sure that the application is active, otherwise the connection may be terminated.

   {% endnote %}

## Deploying to the testnet

Now that we have a smart contract that builds without errors, we can deploy it to the blockchain.

Now you can click on the `Deploy Contract`.

A transaction confirmation window will appear in the application. Confirm this.

{% note alert %}

If you encounter an error during the deployment process indicating that you do not have enough resources to execute the smart contract action, click on "Buy Resources" to learn how to purchase resources.

{% endnote %}

{% note alert %}

If there are not enough funds in your account when purchasing resources, click on the "Faucet" to receive some amount of them to your account & and try buy resources again

{% endnote %}

This will deploy your smart contract to the deNotary Testnet, and allow you to interact with it.

If there are any errors during the deployment process, you will see them in browser and application.

## Interacting with the contract

Now that we have deployed our smart contract to the blockchain, we can interact with it.


Open <a href="https://dev-explorer.deNotary.io" target="_blank" rel="noreferrer noopener">explorer</a> for deNotary TestNet.

Click the search button in the upper-right corner.

Enter your account name. You will see a page with information about your account.

Go to the `CONTRACT` tab, after `Actions`.

As you can see, we will need to reconnect our wallet to interact with this contract. Do it as we described it above.

You can fill out the fields for the `save` action and click the `Submit Transaction` button to execute the action.
After that, you will need to confirm this transaction in the application.

You can also view the entries in the table. To do this, go to the `Table` tab. You will see the changes in your table.


## Congratulations!

You've now built and deployed your first smart contract to the blockchain, and interacted with it.

It's time for you to start building your own smart contracts! These docs will lead you through ever step of
the way, but your first step is learning about the [Anatomy](/smart-contracts/01_contract-anatomy) of
a smart contract.

You might also want to study some of the [Core Concepts](/core-concepts/blockchain-basics/10_decentralization) of the blockchain.

You are also ready to move on to the [next section to study local development](/quick-start/05_local-development).
# Local Development

Developing using the [Web Deploy](https://deploy.deNotary.io) will only take you so far.
Eventually, you will want to develop locally on your machine, so that you can easily use version control, your
favorite editor, and other tools that you are used to.

This guide will walk you through setting up your local development environment using Contract Development Toolkit

## Operating systems

Use Ubuntu 22.04 or Ubuntu 24.04. On machines running other operating systems, you can use dev containers (docker), virtual machines, or WSL to run Ubuntu.

## CDT (Contract Development Toolkit)
The Contract Development Toolkit (CDT) is a C/C++ toolkit targeting WebAssembly (WASM) designed for developing smart contracts in C/C++ that will be deployed on the deNotary blockchain.

### CDT installation
```bash
wget https://github.com/AntelopeIO/cdt/releases/download/v4.1.1/cdt_4.1.1-1_amd64.deb
sudo apt install ./cdt_4.1.0_amd64.deb
```
### Cleos installation
```bash
wget https://github.com/AntelopeIO/leap/releases/download/v5.0.3/leap_5.0.3_amd64.deb
sudo dpkg -i leap_5.0.3_amd64.deb
```

**Getting wallet**
[Getting wallet](https://explorer.deNotary.io/wallet)

**Create account**
[Create account](https://wiki.deNotary.io/wallet-info/account/CreatingNewAccount)

**Getting private key**
[Getting private key](https://wiki.deNotary.io/wallet-info/security/getting-private-key)

### Import a wallet in Cleos
**Start keosd**
```bash
nohup keosd >/tmp/keosd.log 2>&1 &
```
**Creating a wallet**
```bash
cleos wallet create -n default --to-console
```
**The answer will be something like this**
```
Creating wallet: default
Save password to use in the future to unlock this wallet.
Without password imported keys will not be retrievable.
"PW..."
```
**Be sure to save your password**

```bash
cleos wallet open -n default
cleos wallet unlock -n default
cleos wallet import -n default --private-key <Your private key>
```

### Creating a smart contract
Create a project folder, preferably one that matches your account name.. 
 ```bash
 mkdir <Preferably the same as your account name.>
 ```
In the project folder, create a dist folder for assemblies.
 ```bash
 mkdir dist
 ```
In the dist folder, create a folder with the name of the smart contract for builds. In this case, it's the EOSest folder. 
```bash
mkdir dist/EOSest
```
create a cpp file
```bash
> EOSest.cpp
```
// Place the following code in the file
```cpp
#include <eosio/eosio.hpp>
#include <eosio/print.hpp>

using namespace eosio;

CONTRACT EOSest : public contract {
public:
  using contract::contract;

  ACTION hi(name user) {
    require_auth(user);
    print("Hello, ", user, "!");
  }
};

EOSIO_DISPATCH(EOSest, (hi))

```
**This smart contract must be named EOSest.cpp**

## Compiling a smart contract

The contract name must match the address in the deNotary network where the deployment will take place. For this example, we've used EOSest.

### Compilation is performed using CDT.

```bash
cdt-cpp -I. -O3 --abigen EOSest.cpp -o ./dist/EOSest/EOSest.wasm
```

### Smart contract deployment

**Deployment is performed by the cleos command**

```bash
cleos -u https://dev-history.deNotary.io set contract <the name of the wallet on the network, for example: testtesttest> ./dist/EOSest -p <the name of the wallet on the network, for example: testtesttest>@active
```
In case of error
```bash
Error 3120003: Locked wallet
Ensure that your wallet is unlocked before using it!
Error Details:
You don't have any unlocked wallet!
```
You need to unlock your wallet and re-deploy the smart contract.
```bash
cleos wallet unlock -n default
```
**Check the paths**

### Adding eosio.code for online actions.
```bash
cleos -u https://dev-history.deNotary.io set account permission <the name of the wallet on the network, for example: testtesttest> active --add-code
```

## Smart contract development
[Documentation](https://docs.antelope.io/cdt/latest/)

# WalletConnect Web Integration (deNotary Wallet)

You can find an example of how this can be implemented in this [repository](https://github.com/deNotaryIO/Wallet-Connect-V2-Exapmle-Integration).

This document explains how to connect WalletConnect to a web project (if you need a custom solution in another programming language, contact us by email: `office@swisstechcorp.com`).

- `deNotary-wallet-plugin` - wallet plugin for WharfKit
- `react-deNotary-frontend` - working frontend example
- `wallet-connect-server` - Socket.IO bridge server between dApp and mobile wallet

## 1. How the Integration Works

Flow:

1. Your website (dApp) connects to `wallet-connect-server` through `deNotary-wallet-plugin`.
2. The plugin shows a QR/deeplink to open the deNotary wallet app.
3. The user confirms the connection in the wallet.
4. The dApp sends a transaction signing request.
5. The wallet signs and returns signatures/packed transaction data.
6. The dApp sends the transaction to the blockchain.

## 2. Software Requirements

Minimum:

- Node.js 18+ (LTS recommended)
- A web project (React/Vite, Next.js, Vue, etc.)

## 3. Installing Dependencies in a Web Project

Run the following commands:

```bash
cd ../your-web-project
npm install @wharfkit/session @wharfkit/web-renderer @wharfkit/antelope deNotary-wallet-plugin
```

## 4. Basic Initialization (Recommended Path)

### 4.1 Create `wallet.ts` (or a similar module)

```ts
import { SessionKit } from '@wharfkit/session'
import { WebRenderer } from '@wharfkit/web-renderer'
import {
  deNotaryWalletPlugin,
  deNotaryTestNet,
  deNotaryMainNet,
  type deNotaryWalletConfig,
} from 'deNotary-wallet-plugin'

const walletConfig: deNotaryWalletConfig = {
  requiresChainSelect: false,
  requiresPermissionSelect: false,
  serverUrl: 'wss://wcs2.deNotary.io', // WalletConnect server URL
  chain: deNotaryTestNet, // or deNotaryMainNet
}

// Singleton WebRenderer instance
const webRenderer = new WebRenderer();

// Create SessionKit factory function
export const sessionKit = new SessionKit(
  {
    appName: 'My Web dApp',
    chains: [deNotaryTestNet], // or deNotaryMainNet
    ui: new WebRenderer(),
    walletPlugins: [new deNotaryWalletPlugin(walletConfig)],
  },
  {
    transactPlugins: undefined,
  }
)
```

### 5. Login / Logout / Session Restore

```ts
import type { Session } from '@wharfkit/session'
import { sessionKit } from './wallet'

export async function restoreSession(): Promise<Session | null> {
  const restored = await sessionKit.restore()
  return restored ?? null
}

export async function login() {
  const result = await sessionKit.login()
  return result.session
}

export async function logout() {
  await sessionKit.logout()
}
```

What `login()` does:

- opens the UI prompt (QR + deeplink)
- waits for a wallet connection event
- returns a session object (`session`) for transaction signing

## 6. Transaction Signing and Sending

This project uses a safe flow:

1. `session.transact(..., { broadcast: false })` - sign only
2. manual `push_transaction` to blockchain

This lets you use `packedTransactionHex`, returned by the wallet.

```ts
import { Bytes, PackedTransaction } from '@wharfkit/antelope'
import type { Session } from '@wharfkit/session'
import { GFResolvedSigningRequest } from 'deNotary-wallet-plugin'

export async function sendTransfer(session: Session) {
  const actions = [
    {
      account: 'eosio.token',
      name: 'transfer',
      authorization: [session.permissionLevel],
      data: {
        from: session.actor,
        to: 'gf.dex',
        quantity: '0.1000 DNLT',
        memo: 'Transfer from web dApp',
      },
    },
  ]

  const signed = await session.transact({ actions }, { broadcast: false })

  const resolved = GFResolvedSigningRequest.fromBase(signed.resolved)
  if (!resolved?.packedTransactionHex) {
    throw new Error('Wallet did not return packed transaction data')
  }

  const packed = PackedTransaction.from({
    packed_trx: Bytes.from(resolved.packedTransactionHex),
    compression: 0,
    packed_context_free_data: Bytes.from(''),
    signatures: signed.signatures,
  })

  const pushResult = await session.client.v1.chain.push_transaction(packed)
  return pushResult.transaction_id
}
```

### 6.1 How to Display Blockchain/API Errors

When `push_transaction(...)` fails, WharfKit usually throws `APIError` from `@wharfkit/antelope`. This error may contain a full node response in `response.json`, including `error.details`.

If you want to show not only `err.message`, but also detailed blockchain error data in UI, normalize the error first:

```ts
import { APIError, type APIErrorData } from '@wharfkit/antelope'

export interface TransactionErrorData {
  code?: number
  message?: string
  error?: Partial<APIErrorData>
}

export function normalizeTransactionError(err: unknown): {
  errorMessage: string
  parsedError: TransactionErrorData | null
} {
  let errorMessage = 'Transaction failed'
  let parsedError: TransactionErrorData | null = null

  if (err instanceof APIError) {
    const apiErr = err as APIError & { json?: unknown }

    if (apiErr.response?.json) {
      parsedError = apiErr.response.json
    } else if (apiErr.json) {
      parsedError = apiErr.json as TransactionErrorData
    } else if (apiErr.error) {
      parsedError = {
        code: apiErr.code,
        message: err.message,
        error: apiErr.error,
      }
    } else {
      try {
        const jsonMatch = (err.message || String(err)).match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          parsedError = JSON.parse(jsonMatch[0]) as TransactionErrorData
        }
      } catch {
        // ignore JSON parse error
      }
    }

    if (!parsedError) {
      parsedError = {
        code: apiErr.code || 500,
        message: err.message || 'API Error',
        error: {
          name: err.name || 'api_error',
          what: err.message,
          details: apiErr.details,
        },
      }
    }

    errorMessage = `Transaction failed: ${err.message}`
  } else if (err instanceof Error) {
    parsedError = {
      message: err.message,
    }
    errorMessage = err.message
  } else {
    parsedError = {
      message: 'Unknown error',
    }
  }

  return { errorMessage, parsedError }
}
```

Then in the `catch` around `sendTransfer(...)`:

```ts
try {
  const txId = await sendTransfer(session)
  setLastTxId(txId)
} catch (err) {
  const { errorMessage, parsedError } = normalizeTransactionError(err)

  setError(errorMessage)
  setErrorDetails(parsedError ? JSON.stringify(parsedError, null, 2) : null)
}
```

And render both the short error text and the raw details:

```tsx
{error && <p style={{ color: 'red' }}>{error}</p>}
{errorDetails && <pre>{errorDetails}</pre>}
```

This is useful for:

- showing `error.details[0].message` from nodeos/Leap-compatible APIs
- debugging permission errors, RAM/CPU limits, invalid action data
- distinguishing wallet-side failures from blockchain-side failures

## 7. Full React Example (Minimal)

```tsx
import { useEffect, useState } from 'react'
import type { Session } from '@wharfkit/session'
import { sessionKit } from './wallet'
import { normalizeTransactionError, sendTransfer } from './sendTransfer'

export default function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetails, setErrorDetails] = useState<string | null>(null)

  useEffect(() => {
    sessionKit.restore().then((restored) => {
      if (restored) setSession(restored)
    })
  }, [])

  const onLogin = async () => {
    try {
      setLoading(true)
      setError(null)
      setErrorDetails(null)
      const result = await sessionKit.login()
      setSession(result.session)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const onLogout = async () => {
    await sessionKit.logout()
    setSession(null)
  }

  const onSend = async () => {
    if (!session) return
    try {
      setLoading(true)
      setError(null)
      setErrorDetails(null)
      const txId = await sendTransfer(session)
      alert(`TX sent: ${txId}`)
    } catch (e) {
      const { errorMessage, parsedError } = normalizeTransactionError(e)
      setError(errorMessage)
      setErrorDetails(parsedError ? JSON.stringify(parsedError, null, 2) : null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>WalletConnect Web Integration</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {errorDetails && <pre>{errorDetails}</pre>}

      {!session ? (
        <button onClick={onLogin} disabled={loading}>
          {loading ? 'Connecting...' : 'Connect Wallet'}
        </button>
      ) : (
        <>
          <p>Actor: {session.actor.toString()}</p>
          <p>Permission: {session.permission.toString()}</p>
          <button onClick={onSend} disabled={loading}>
            {loading ? 'Sending...' : 'Send Test Transaction'}
          </button>
          <button onClick={onLogout}>Disconnect</button>
        </>
      )}
    </div>
  )
}
```

## 8. Important Parameters and Common Mistakes

### `serverUrl`

- Production and development: use only `wss://...` (TLS is required)

### `chain`

- Use one of the networks provided by the `deNotary-wallet-plugin` npm package

```ts
import {
  deNotaryTestNet,
  deNotaryMainNet,
} from 'deNotary-wallet-plugin'
```

### UI Renderer

- For browser apps, `@wharfkit/web-renderer` is required. Otherwise `login()` cannot show the QR/deeplink prompt.

### CORS and Proxy

- If the server and website are on different domains, verify CORS/Reverse Proxy settings. If you run into issues, contact us by email: `office@swisstechcorp.com`.

## 9. What the Plugin Handles Automatically

`deNotaryWalletPlugin` already handles:

- creating `client_id`
- connecting to Socket.IO (`/dapp/{client_id}`)
- generating deeplink for mobile wallet
- rendering QR/deeplink through WharfKit UI
- E2E payload encryption/decryption
- waiting for wallet response and returning signatures in `session.transact`

## 10. Quick Integration Validation (Checklist)

1. `wallet-connect-server` is running and reachable from the browser.
2. `walletConfig.serverUrl` is set to the correct URL.
3. `sessionKit.login()` opens a prompt with QR/deeplink.
4. After scanning, an active session appears (`session.actor` is filled).
5. Transaction is signed and sent (`transaction_id` is returned).

## 11. Troubleshooting

### Connection Error (`connect_error` / timeout)

- Check that `serverUrl` is reachable.
- Confirm the protocol is correct (`ws/wss` via Socket.IO).
- For production, use `wss://`, not `ws://`.

### Prompt Opened, but Wallet Does Not Connect

- Check that the deeplink opens in the mobile wallet app.
- Check chain id match between dApp and wallet.

### Signature Succeeds, but Transaction Is Not Pushed

- Check account permissions (`permission`) and available network resources.
- Check `actions` fields (account/name/data/authorization).
- Log `resolved.packedTransactionHex` and `signatures`.
- If available, log `APIError.response.json` or render `parsedError` in UI to see `error.details`.
# Endpoints

<head><title>deNotary Endpoints</title></head>

deNotary MainNet - <a href="https://history.deNotary.io/" target="_blank" rel="noreferrer noopener">history.deNotary.io</a>

deNotary TestNet - <a href="https://dev-history.deNotary.io/" target="_blank" rel="noreferrer noopener">dev-history.deNotary.io</a>
# Contract Anatomy

The most used Smart Contract development language for deNotary is C++. 
The C++ knowledge required for writing smart contracts is minimal. If you have ever written C, C++, Java, C#, or
TypeScript, you should be able to pick up writing deNotary smart contracts with ease.

There are also community efforts to support other languages such as Rust, Python, Go, and AssemblyScript.
However, these docs will focus on C++ for writing smart contracts. 
If you are interested in learning about the other community-led initiatives for extending language support, 
check out the [Language Support](/smart-contracts/999_language-support) page.

## Project Structure

You have a lot of freedom when it comes to structuring your project. You can use one monolithic `.cpp` file for your
entire project, or you can split it up into multiple files. You can even use a build system like CMake to manage your
project.

In most of the guides here we will be using a single `.cpp` file.
This is the simplest way to get started, and it is the most common way to write smart contracts.

### Single File

Below is an example of a single file smart contract. You don't need anything else in your project to compile this,
and you don't need to include any other files.

```cpp title="project/singlefile.cpp"
#include <eosio/eosio.hpp>

CONTRACT singlefile : public eosio::contract {
  public:
    using contract::contract;

    ACTION test() {
      // ...
    }
};
```

### Multiple Files

If you want to split your project up into multiple files, you can do that as well.

```cpp title="project/src/library.hpp"
class library {
    struct data {
      uint64_t id;
      std::string value;
    };
};
```

```cpp title="include/multiplefiles.cpp"
#include <eosio/eosio.hpp>
#include "library.hpp"

CONTRACT multiplefiles : public eosio::contract {
  public:
    using contract::contract;

    ACTION test() {
      // ...
    }
};
```


#### Header vs Source

In C++ you have two types of files: header files (`.hpp/.h`) and source files (`.cpp`).

- Header files are used to declare functions, classes, structs, and other types.
- Source files are used for the implementation of functions declared in header files.

#### Include directories

When you compile your project, you will need to tell the compiler where to find your header files.

Generally, you will want to put your header files in a directory called `include`, and your source files in a directory
called `src`.

```text
project/
  include/
    library.hpp
  src/
    multiplefiles.cpp
```

### When to use a multi-file project

If you are writing a large project, you will probably want to split it up into multiple files.

Keeping your project tidy means splitting it up into logical components. For example, you might have a file for your
database, a file for your business logic, and a file for some helper functions.

This also helps larger teams not stumble over each-other when working with version control systems like `git`.

## Contract Structure

Contracts are object-oriented. You define a contract the same way you would define a `class`.

```cpp title="project/mycontract.cpp"
#include <eosio/eosio.hpp>

CONTRACT mycontract : public eosio::contract {
    public:
    using contract::contract;
};
```

There are a few key components here. 

### CONTRACT definition

The `CONTRACT` keyword is how we tell the compiler that we are writing a deNotary Smart Contract.

It must be followed by the name of the contract, and the base class which this contract inherits from.

```cpp
CONTRACT mycontract : public contract {
```

{% note tip %}
**Good to know**

You should typically keep your contract name the same as your `.cpp` file name. Some build systems will enforce this
for you, and the errors they return are not always clear.
{% endnote %}

### Access Modifiers

Access modifiers are used to define the visibility of certain elements of your contract.
There are three access modifiers in C++: 
- `public`: The element is visible to everything.
- `private`: The element is only visible to the contract itself.
- `protected`: The element is visible to the contract itself, and any contracts that inherit from it.

When you declare a visibility modifier, everything below it will have that visibility.

```cpp
public:
  // Everything below this is public
private:
  // Everything below this is private
```


{% note alert %}

You are not defining the visibility of your contract to the outside world. You are defining the visibility of your
contract to other elements of your contract. Things like actions and tables will ALWAYS be publicly accessible
outside your contract.

{% endnote %}

### Using Contract

A required line for deNotary Smart Contracts to compile is the `using contract::contract;` line.


### Primary Elements

deNotary Smart Contracts are made up of two primary elements:

- **Actions**: The entry points to your contract. 
- **Tables**: The way you store data in your contract.

We will explain both of these in more detail in the next sections.
# Actions

An action is a function that can be called on the Smart Contract. It is the entry point into some piece of functionality
that you want to expose to the outside world.

Actions can be called by any account, even other smart contracts.

## Defining an Action

There are two ways to define an action, one is more verbose, but allows you to specify the return type of the action,
and the other is a shorthand that will always return `void`.

### Simple action

When you don't need to specify the return type of the action, you can use the `ACTION` keyword which 
is a shorthand for `[[eosio::action]] void`.

```cpp
ACTION youraction(){
    // Your logic here
}
```

### Specifying the return type

If you want to specify the return type of the action, you must use the `[[eosio::action]]` attribute followed by the
return type.

```cpp
[[eosio::action]] uint64_t youraction(){
    // Your logic here
    return 1337;
}
```
{% note alert %}

вљ  Return values & Composability.

Return values are only usable from outside the blockchain, and cannot currently be used
in deNotary for smart contract composability. 

{% endnote %}

## Inline Actions

Inline actions are a way to call another contract's action from within your contract. 
This is useful when you want to build functionality on top of other contracts.

Let's demonstrate this below with two simple contracts.

```cpp title="sender.cpp"
#include <eosio/eosio.hpp>
using namespace eosio;

CONTRACT sender : public contract {
public:
    using contract::contract;

    ACTION sendinline(name user) {
        action(
            permission_level{get_self(), name("active")},
            name("contract2"),
            name("receiver"),
            std::make_tuple(user)
        ).send();
    }
};
```

{% note alert %}

? Your contract's account.
The `get_self()` function returns the name of the account that the contract is deployed to. It is useful
when you don't know where this contract will be deployed to until you deploy it, or if the contract might
be on multiple accounts.

{% endnote %}

```cpp title="receiver.cpp"
#include <eosio/eosio.hpp>
using namespace eosio;

CONTRACT receiver : public contract {
public:
    using contract::contract;

    ACTION received(name user) {
        print("I was called by ", user);
    }
};
```

| Contract | Account deployed to |
| -------- |---------------------|
| `sender`   | `contract1`         |
| `receiver` | `contract2`         |

If you had these two contracts deployed, you could call the `contract1::sendinline` action, which would then call the
`contract2::receiver` action.

It would also pass the parameter `user` to the `contract2::receiver` action. 

### Interface of the inline action sender

The `action` constructor takes four arguments:

```cpp
action(
    <permission_level>, 
    <contract>, 
    <action>, 
    <data>
).send();
```

- `permission_level` - The permission level that the action will be called with
- `contract (name type)` - The account that the action is deployed to
- `action (name type)` - The name of the action that will be called
- `data` - The data that will be passed to the action, as a tuple

{% note alert %}

The `name()` function is used to convert a `string` into a `name` type. This is useful when you want to pass
the name of an account or action as a string, but the function you are calling requires a `name` type.

{% endnote %}

### Creating the permission level

The `permission_level` argument is used to specify the permission level that the action will be called with.
This will either be the contract that the action is deployed to, or a permission that the account that the 
contract is deployed to has.

The `permission_level` constructor takes two arguments:

```cpp
permission_level(
    <account (name type)>, 
    <permission (name type)>
)
```

{% note alert %}

The contract is the new sender.
When you call an inline action, the contract that is calling the action becomes the new sender.
For security reasons, the original authorization is not passed to the new contract, as it would mean
that the new contract could call actions on behalf of the original sender (like sending tokens).

{% endnote %}

### Creating the tuple

The `data` argument is used to specify the parameters of the action that you are calling.

A tuple is just a way to group multiple arguments together. You can create a tuple using the `std::make_tuple` function.
```cpp
std::make_tuple(<arg1>, <arg2>, <arg3>, ...);
```

> вљ  **Passing strings properly**
>
> A common issue with `make_tuple` is using literal c-strings (like `make_tuple(name, "withdrawl")`). Instead, you should use
> `std::string` (like `make_tuple(name, std::string("withdrawl"))`).


Instead of using `make_tuple`, you can also manually define a struct and then construct it.

```cpp
struct transfer_args {
    name         from;
    name         to;
    asset        quantity;
    string       memo;
};

// Example usage
action(
    permission_level{_self, name("active")},
    name("eosio.token"),
    name("transfer"),
    transfer_args {.from=_self, .to=recipient, .quantity=quantity, .memo=memo}
).send();

```

### Code Permission

There is a special account permission called `eosio.code` that allows a contract to call inline actions.
Without this permission your contract will not be able to call actions on other contracts.

This permission sits on the `active` permission level, so that other contract's using the `require_auth`
function will be able to verify that your contract has the authority to call the action.

To add the code permission you need to update your account's active permission to be controlled by
`<YOURACCOUNT>@eosio.code` **along with your current active permission**.

{% note alert %}
вљ  Don't lose access!

The `eosio.code` permission is meant to be **added** to your existing active permission, not replace it.
If you remove your current active permission controllers (accounts or keys), then you will lose access to 
your account/contract.

{% endnote %}

An example permission structure with a Code Permission on the account `yourcontract` would look like:
```text
owner 
  вЂў YOUR_PUBLIC_KEY
в†і active -> 
  вЂў YOUR_PUBLIC_KEY
  вЂў yourcontract@eosio.code
```

# Variables

Defining variables is a fundamental part of any programming language. In this section, we will look at
the different types of variables you can define in deNotary Smart Contracts.

C++ supports a wide range of data types. deNotary extends the set of types with deNotary-specific types.

## Defining variables

Variables are defined in the same way as in C++.

```cpp
function main() {
    // <type> <name> = <value>;
    int a = 5;
}
```


## Basic types

These are the basic types that come built-in with C++. You have likely used some form of these types before
in other programming languages you have used.

Unless otherwise specified, the types below are imported from the `<eosio/eosio.hpp>` header.

```cpp
#include <eosio/eosio.hpp>
```

### Integer types

Integer types are used to represent whole numbers. They can be either signed (positive or negative) or unsigned (positive only).


| Integer Types         | Description |
|------------------------| --- |
| `bool`                 | Boolean (true/false) |
| `int8_t`               | Signed 8-bit integer |
| `int16_t`              | Signed 16-bit integer |
| `int32_t`              | Signed 32-bit integer |
| `int64_t`              | Signed 64-bit integer |
| `int128_t`             | Signed 128-bit integer |
| `uint8_t`              | Unsigned 8-bit integer |
| `uint16_t`             | Unsigned 16-bit integer |
| `uint32_t`             | Unsigned 32-bit integer |
| `uint64_t`             | Unsigned 64-bit integer |
| `uint128_t`            | Unsigned 128-bit integer |

#### Required Header

```cpp
#include <eosio/varint.hpp>
```

| Integer Types         | Description |
|------------------------| --- |
| `signed_int`           | Variable-length signed 32-bit integer |
| `unsigned_int`         | Variable-length unsigned 32-bit integer |


### Floating-Point types

Floating-point types are used to represent decimal numbers.

{% note alert %}

вљ  Warning.

Floating-point types are not precise. They are not suitable for storing currency values, and are often
problematic for storing other types of data as well. Use them with caution, especially when dealing with
blockchains.

{% endnote %}

| Float Types | Description |
| --- | --- |
| `float` | 32-bit floating-point number |
| `double` | 64-bit floating-point number |

### Byte types

Byte types are used to represent raw byte sequences, such as binary data / strings.

| Blob Types | Description |
| --- | --- |
| `bytes` | Raw byte sequence |
| `string` | String |

### Time types

Time types are used to represent time, specifically relating to blocks.

| Time Types | Description                   |
| --- |-------------------------------|
| `time_point` | Point in time in microseconds |
| `time_point_sec` | Point in time in seconds      |
| `block_timestamp` | Block timestamp               |

#### Helpful functions

| Function                                            | Description                          |
|-----------------------------------------------------|--------------------------------------|
| `time_point eosio::current_time_point()`            | Get the current time point           |
| `const microseconds& time_point.time_since_epoch()` | Get the microseconds since the epoch |
| `uint32_t time_point.sec_since_epoch()`             | Get the seconds since the epoch      |
| `block_timestamp eosio::current_block_time()`       | Get the current block time           |


### Hash types

Hash types are used to represent cryptographic hashes such as SHA-256.

| Checksum Types | Description |
| --- | --- |
| `checksum160` | 160-bit checksum |
| `checksum256` | 256-bit checksum |
| `checksum512` | 512-bit checksum |

## Custom types

These are the custom types that come built-in with deNotary. You will likely use some of these types often in your deNotary Smart Contracts.

### Name type

The `name` type is used to represent account names. It is a 64-bit integer, but is displayed as a string.

A variety of system functions require names as parameters.

You have three ways of turning a string into a name:
- `name{"string"}`
- `name("string")`
- `"string"_n`

If you want to get the `uint64_t` value of a name, you can use the `value` method.

```cpp
name a = name("hello");
uint64_t b = a.value;
```

### Key and Signature types

The `public_key` and `signature` types are used to represent cryptographic keys and signatures, and are
also a deNotary specific type.

#### Required Header

```cpp
#include <eosio/crypto.hpp>
```

#### Recovering a key from a signature

```cpp
function recover(checksum256 hash, signature sig) {
    public_key recovered_key = recover_key(hash, sig);
}
```

### Asset types

The `asset` type is used to represent a quantity of a digital asset. It is a 64-bit integer with a symbol, but is displayed as a string.

It is resistent to overflow and underflow, and has various methods for performing arithmetic operations easily.

#### Required Header

```cpp
#include <eosio/asset.hpp>
```

| Asset Types | Description |
| --- | --- |
| `symbol` | Asset symbol |
| `symbol_code` | Asset symbol code |
| `asset` | Asset |

#### Creating an asset

There are two parts to an asset: the quantity, and the symbol. The quantity is a 64-bit integer, and the symbol
is a combination of a string and a precision.

```cpp
// symbol(<symbol (string)>, <precision (1-18)>)
symbol mySymbol = symbol("TKN", 4);

// asset(<quantity (int64_t)>, <symbol>)
asset myAsset = asset(1'0000, mySymbol);
```

#### Performing arithmetic operations

You can easily do arithmetic operations on assets.

```cpp
asset a = asset(1'0000, symbol("TKN", 4));
asset b = asset(2'0000, symbol("TKN", 4));

asset c = a + b; // 3'0000 TKN
asset d = a - b; // -1'0000 TKN
asset e = a * 2; // 2'0000 TKN
asset f = a / 2; // 0'5000 TKN
```

{% note alert %}

?? Symbol matching.

Doing arithmetic operations on assets with different symbols will throw an error, but only during runtime. Make sure that 
you are always doing operations on assets with the same symbol.

{% endnote %}

#### Asset methods

You can convert an asset to a string using the `to_string` method.

```cpp
std::string result = a.to_string(); // "1.0000 TKN"
```

You can also get the quantity and symbol of an asset using the `amount` and `symbol` methods.

```cpp
int64_t quantity = a.amount; // 1'0000
symbol sym = a.symbol; // symbol("TKN", 4)
```

When using an asset, you always want to make sure that it is valid (that the amount is within range).

```cpp
bool valid = a.is_valid();
```


#### Symbol methods

You can convert a symbol to a string using the `to_string` method.

```cpp
std::string result = mySymbol.to_string(); // "4,TKN"
```

You can also get the raw `uint64_t` value of a symbol using the `value` method.

```cpp
uint64_t value = mySymbol.value;
```

When using a symbol by itself, you always want to make sure that it is valid. **However, when using asset, it already checks 
the validity of the symbol within its own `is_valid` method.**

```cpp
bool valid = mySymbol.is_valid();
```

#### Symbol limitations

Symbols have a precision between 1 and 18. This means that you can have a maximum of 18 decimal places.

```cpp
// Valid
symbol mySymbol = symbol("TKN", 4);

// Invalid
symbol mySymbol = symbol("TKN", 19);
```

Symbol codes are limited to 7 characters.

```cpp
// Valid
symbol mySymbol = symbol("TKN", 4);

// Invalid
symbol mySymbol = symbol("ISTOOLONG", 4);
```


## Structs

Structs are used to represent complex data. They are similar to classes, but are simpler and more lightweight. Think of a
`JSON` object.

You can use these in deNotary, but if you are storing them in a table you should use the `TABLE` keyword which we will discuss in the 
[next section](/smart-contracts/04_state-data).

```cpp
struct myStruct {
    uint64_t id;
};
```
# State Data

There are two types of data in a smart contract: state data and transient data. State data is data that is stored on the
blockchain, and is persistent. Transient data is data that is stored during the execution of a transaction, and is not
persistent. The second the transaction is over, the transient data is gone.

There are two parts to storing data on the blockchain: the model and the table. The model is the data structure that you
will be storing, and the table is the container that holds the data. There are a few different types of tables, and each
one has its own use case.

## Data Models

A model is a data structure that you will be storing in a deNotary table. It is a serializable C++ struct, and can contain 
any data type that is also serializable. All common data types are serializable, and you can also create your own
serializable data types, such as other models that start with the `TABLE` keyword.

```cpp
TABLE UserModel {
    uint64_t id;
    name account;
    
    uint64_t primary_key() const { return id; }
};
```

Defining a model is very similar to defining a C++ struct, but with a few differences. The first difference is that you
must use the `TABLE` keyword instead of the `struct` keyword. The second difference is that you must define a `primary_key`
function that returns a `uint64_t`. This function is used to determine the primary key of the table, which is used to
index the table.

Think of this like a NoSQL database, where the primary key is the index of the table. The primary key is used to
determine the location of the data in the table, and is used to retrieve the data from the table easily and efficiently.

### Primary key data types

The primary key **must** be a `uint64_t` (you can also use `name.value`), and it must be unique for each row in the table. This means that you cannot
have two rows with the same primary key. If you need to have multiple rows with the same primary key, you can use a
secondary index.

### Secondary key data types

A secondary index is more flexible than a primary key, and can be any of the following data types:

- `uint64_t`
- `uint128_t`
- `double`
- `long double`
- `checksum256`

They can also include duplicate values, which means that you can have multiple rows with the same secondary key.

{% note alert %} 

? Cost considerations.
 
Each index costs RAM per row, so you should only use secondary indices when you need to. If you don't need to query the table
by a certain field, then you should not create an index for that field.

{% endnote %}

## Payer & Scope

Before we dig into how to store data in tables, we need to talk about `scope` and `payer`.

### RAM Payer

The RAM payer is the account that will pay for the RAM that is used to store the data. This is either the account that
is calling the contract, or the contract itself. This sometimes relies heavily on game-theory, and can be a complex
decision. For now, you will just use the contract itself as the RAM payer.

You also cannot have an account that isn't part of the transaction's authorizations pay for RAM.

{% note alert %} 

? Beware of RAM.

RAM is a limited resource on the deNotary blockchain, and you should be careful about how much RAM you allow others to use on
your contracts. It's often better to make the user pay for the RAM, but this requires that you create incentives for them
to spend their own RAM in return for something of perceived equal or greater value.

{% endnote %}

### Scope

The scope of a table is a way to further segregate the data in the table. It is a `uint64_t` that is used to determine
what _bucket_ the data is stored in.

If we were to imagine the database as a `JSON` object, it might look like this:

```json title="tables.json"
{
    "users": {
        1: [
            {
                "id": 1,
                "account": "bob"
            },
            {
                "id": 2,
                "account": "sally"
            }
        ],
        2: [
            {
                "id": 1,
                "account": "joe"
            }
        ]
    }
}
```

As you can see above, you can have the same primary key in different scopes without there being a conflict. This is useful in a variety of different cases:
- If you want to store data per-user
- If you want to store data per-game-instance
- If you want to store data per-user-inventory
- etc


## Multi-Index Table

The multi-index table is the most common way to store data on the deNotary blockchain. It is a persistent key-value store that
can be indexed in multiple ways, but always has a primary key. Going back to the NoSQL database analogy, you can think
of the multi-index table as a collection of documents, and each index as a different way to query or fetch data from the collection.

### Defining a table

To create a multi-index table you must have a model defined with at least a primary key. You can then create a multi-index
table by using the `multi_index` template, and passing in the name of the table/collection and the model you want to use.

```cpp
TABLE UserModel ...

using users_table = multi_index<"users"_n, UserModel>;
```

This will create a table called `users` that uses the `UserModel` model. You can then use this table to store and retrieve
data from the blockchain.


### Instantiating a table

To do anything with a table, you must first instantiate it. To do this, you must pass in the contract that owns the table,
and the scope that you want to use.

```cpp
ACTION test() {
    name thisContract = get_self();
    users_table users(thisContract, thisContract.value);
```


### Inserting data

Now that you have a reference to an instantiated table, you can insert data into it. To do this, you can use the `emplace`
function, which takes a lambda/anonymous function that accepts a reference to the model that you want to insert.

```cpp
...

name ramPayer = thisContract;
users.emplace(ramPayer, [&](auto& row) {
    row.id = 1;
    row.account = name("deNotary");
});
```

You can also define a model first, and insert it into the entire row.

```cpp
UserModel user = {
    .id = 1,
    .account = name("deNotary")
};

users.emplace(ramPayer, [&](auto& row) {
    row = user;
});
```

### Retrieving data

To retrieve data from a table, you will use the `find` method on the table, which takes the primary key of the row that
you want to retrieve. This will return an iterator (reference) to the row.

```cpp
auto iterator = users.find(1);
```

You need to check if you actually found the row, because if you didn't, then the iterator will be equal to the `end` iterator,
which is a special iterator that represents the end of the table.

```cpp
if (iterator != users.end()) {
    // You found the row
}
```

You then have two ways of accessing the data in the row. The first way is to use the `->` operator, which will give you
a pointer to the row's data, and the second way is to use the `*` operator, which will give you the row's raw data.

```cpp
UserModel user = *iterator;
uint64_t idFromRaw = user.id;
uint64_t idFromRef = iterator->id;
```


### Modifying data

If you tried to call `emplace` twice you would get an error because the primary key already exists. To modify data
in a table, you must use the `modify` method, which takes a reference to the iterator you want to modify, a RAM payer,
and a lambda/anonymous function that allows us to modify the data.

```cpp
users.modify(iterator, same_payer, [&](auto& row) {
    row.account = name("foobar");
});
```

{% note alert %}

? What is same_payer

You can use `same_payer` to make the RAM payer the same as the original ram payer. This is useful if someone else has
paid for the RAM, but you want to modify the data. If you don't use `same_payer`, then you will have to pay for the RAM
yourself. You will also have to pay for the RAM if you are changing fields with mutable size, such as `string` or `vector`.

{% endnote %}

### Removing data

To remove data from a table, you must use the `erase` method, which takes a reference to the iterator you want to remove.

```cpp
users.erase(iterator);
```


### Using a secondary index

Using a secondary index will allow you to query your table in a different way. For example, if you wanted to query your
table by the `account` field, you will need to create a secondary index on that field.

#### Redefining our model and table

To use a secondary index, you must first define it in your model. You do this by using the `indexed_by` template, and passing
in the name of the index, and the type of the index.

```cpp
TABLE UserModel {
    uint64_t id;
    name account;

    uint64_t primary_key() const { return id; }
    uint64_t account_index() const { return account.value; }
};

using users_table = multi_index<"users"_n, UserModel,
    indexed_by<"byaccount"_n, const_mem_fun<UserModel, uint64_t, &UserModel::account_index>>
>;
```

The `indexed_by` template can be a bit confusing, so let's break it down.

```cpp
indexed_by<
    <name_of_index>,
    const_mem_fun<
        <model_to_use>, 
        <index_type>,
        <pointer_to_index_function>
    >
>
```

The `name_of_index` is the name of the index that you want to use. This can be anything, but it's best to use something
that describes what the index is for.

The `model_to_use` is the model that you want to use for the index. This is usually the same model that you are using for
the table, but it doesn't have to be. This is useful if you want to use a different model for the index, but still want
to be able to access the data in the table.

The `index_type` is the type of the index, and is limited to the types we discussed earlier.

The `pointer_to_index_function` is a pointer to a function that returns the value that you want to use for the index. This
function must be a `const_mem_fun` function, and must be a member function of the model that you are using for the index.

#### Using the secondary index

Now that you have a secondary index, you can use it to query your table. To do this, first get the index from the table, and
then use the `find` method on the index, instead of using it directly on the table.

```cpp
auto index = users.get_index<"byaccount"_n>();
auto iterator = index.find(name("deNotary").value);
```

To modify data in the table using the secondary index, you use the `modify` method on the index, instead of using it
directly on the table.

```cpp
index.modify(iterator, same_payer, [&](auto& row) {
    row.account = name("foobar");
});
```

## Singleton Table

A `singleton` table is a special type of table that can only have one row per scope. This is useful for storing data that
you only want to have one instance of, such as a configuration, or a player's inventory.

The primary differences between a `singleton` table and a multi-index table are:
- Singletons do not need a primary key on the model
- Singletons can store any type of data, not just predefined models

### Defining a table

To define a singleton table, you use the `singleton` template, and pass in the name of the table, and the type of the
data that you want to store.

You also must import the `singleton.hpp` header file.

```cpp
#include <eosio/singleton.hpp>

TABLE ConfigModel {
    bool is_active;
};

using config_table = singleton<"config"_n, ConfigModel>;

using is_active_table = singleton<"isactive"_n, bool>;
```

The `singleton` template is identical to the `multi_index` template, except that it does not support secondary indices.

You've defined one table that stores a `ConfigModel`, and another table that stores a `bool`. Both tables hold the 
exact same data, but the `bool` table is more efficient because it does not need to store the added overhead that is
caused by the `ConfigModel` struct.

### Instantiating a table

Just like the `multi_index` table, you must first instantiate the table, and then you can use it.

```cpp
name thisContract = get_self();
config_table configs(thisContract, thisContract.value);
```

The `singleton` table takes two parameters in its constructor. The first parameter is the contract that the table is
owned by, and the second parameter is the `scope`.

### Getting data

There are a few ways to get data from a `singleton`. 

#### Get or fail

This will error out at runtime if there is no existing data.
To prevent this, you can use the `exists` method to check if there is existing data.

```cpp
if (!configs.exists()) {
    // handle error
}
ConfigModel config = configs.get();
bool isActive = config.is_active;
```

#### Get or default

This will return a default value, but **will not** persist the value.

```cpp
ConfigModel config = configs.get_or_default(ConfigModel{
  .is_active = true
});
```

#### Get or create

This will return a default value, and **will** persist the value.

```cpp
ConfigModel config = configs.get_or_create(ConfigModel{
  .is_active = true
});
```

### Setting data

To persist data in a `singleton`, you can use the `set` method, which takes a reference to the data that you want to set.

```cpp
configs.set(ConfigModel{
    .is_active = true
}, ramPayer);
```

### Removing data

Once you've instantiated a `singleton`, it's easy to remove it. Just called the `remove` method on the instance itself.

```cpp
configs.remove();
```


# Authorization

Authorization is the process of determining whether or not a user has permission to perform a transaction (through actions). 
In blockchain applications this is a key aspect of ensuring the safety of a Smart Contract, and the digital assets that
it controls.

Checking authorizations with deNotary can be done in a few ways.

## Getting the sender

The best way to get the sender of a transaction is to pass it in as an argument to the action.

```cpp
ACTION testauth(name user) {
    print("I was called by ", user);
}
```

This is the most explicit way to get the sender of a transaction, and is the recommended way to do it.

## Require auth

The easiest way to check that an account has signed this transaction and given their authority is to use the `require_auth` function.

```cpp
ACTION testauth(name user) {
    require_auth(user);
}
```

## Require auth2

Like the `require_auth` function, the `require_auth2` function will check that the specified account has signed the transaction.
However, it will also check that the specified permission has signed the transaction.

```cpp
ACTION testauth(name user) {
    require_auth2(user, name("owner"));
}
```

This will check that the specified `user` account has signed the transaction, meaning that the transaction which calls 
this action has been authorized by the `user` account.

## Has auth

The above `require_auth` function will check that the specified account has signed the transaction and fail the transaction
if it has not. However, if you want to check that the specified account has signed the transaction, but not fail the transaction
if it has not, you can use the `has_auth` function.

```cpp
ACTION testauth() {
    name thisContract = get_self();
    if (has_auth(thisContract)) {
        // This contract has signed the transaction
    }
}
```

## Is account

You might also want to check if an account even exists. This can be done with the `is_account` function.

```cpp
ACTION testauth(name user) {
    if(!is_account(user)) {
        // The user account does not exist
    }
}
```
# Assertions

Like every program, bugs can occur and user input must be validated. deNotary provides a clear cut way to do this.

## Reverting state

Assertions are a way to check that a condition is true, and if it is not, the transaction will fail. When a transaction
fails, all state changes that have occurred in the transaction will be rolled back. This means that any changes to 
persisted data / tables will be reverted as if the transaction never happened.

## Check

The `check` function is how you validate conditions in deNotary. 
The function will check that the specified condition is true, and if it is not, the transaction will fail.

```cpp
check(1 == 1, "1 should equal 1");
```

The interface for the `check` function simply takes a condition and a `string` message. If the condition is false, the message
will be thrown as an error and the transaction will revert.

## Logging non-strings

Since the `check` function takes a `string` message, you might be wondering how to log non-strings. 
This depends on the type of data you want to log, but here are some common examples:

#### Logging `name`

```cpp
name thisContract = get_self();
check(false, "This contract is: " + thisContract.to_string());
```

#### Logging `asset`

```cpp
asset myAsset = asset(100, symbol("DNLT", 4));
check(false, "My asset is: " + myAsset.to_string());
```

#### Logging integers

```cpp
int myInt = 100;
check(false, "My int is: " + std::to_string(myInt));
```




# Events

Events are a way for smart contracts to communicate with each other as side-effects of actions.

The most common in-use usage of events is tracking `eosio.token` (`DNLT`) transfers, but they can be used for
any type of communication between contracts.

We will use that exact example below, but first we will cover the basics of events.

## Two sides of an event

Of course, there are two sides to every event: the sender and the receiver.

On one side, you have a `contract::action` that is emitting an event, and on the other side you have a contract that is
listening for that event.

## Event Receiver

Event Receivers are not actions, but rather functions that will be called when another action tags your contract
as a recipient. 

```cpp
#include <eosio/eosio.hpp>
using namespace eosio;

CONTRACT receiver : public contract {
public:
    using contract::contract;

    [[eosio::on_notify("*::transfer")]] 
    void watchtransfer(name from, name to, asset quantity, std::string memo) {
        // Your logic here
    }
};
```

The `on_notify` attribute takes a string as an argument. This string is a filter that will be used to determine
which actions will trigger the `watchtransfer` function. The filter is in the form of `contract::action`, where `contract`
is the name of the contract that is sending the event, and `action` is the name of the action within that contract that
triggered the event.

The `*` character is a wildcard that will match any contract or action. So in the example above, the `watchtransfer` function
will be called whenever any contract sends a `transfer` action to the `receiver` contract. 
The wildcard is supported only on the contract and NOT on the action side of the filter.

Examples:
- `*::transfer` - Match any `transfer` action on any contract
- `*::refund` - Match any `refund` action on any contract
- `yourcontract::transfer` - Match **only** the `transfer` action on `yourcontract`

{% note alert %}

Who can send events?

Any contract can send an event, but only the contract that is specified in the `on_notify` attribute
will be notified. However, each notification adds a small amount of CPU usage to the transaction even if
no recipient is listening for the event.

{% endnote %}

## Event Sender

Event Senders are actions that emit an event to any contract that has been specified in a special 
`require_recipient` function.

```cpp
#include <eosio/eosio.hpp>
using namespace eosio;

CONTRACT token : public contract {
public:
    using contract::contract;

    ACTION transfer(name from, name to, asset quantity, std::string memo) {
        require_recipient(from);
        require_recipient(to);
    }
};
```

The `transfer` action above will emit an event to both the `from` and `to` accounts (this is actually how the `eosio.token` contract works).
So if your contract is either the `from` or `to` account, then you can listen for the `transfer` event. If your account is **not**
either of those accounts, you have no way of listening for the `transfer` event from within the blockchain.


{% note alert %}

Who can receive the event?

Any account can receive an event, but only the account specified in the `require_recipient` function
will be notified. However, if the account receiving the event does not have a smart contract deployed on it, 
then the event will be ignored as it cannot possibly have any logic to handle the event.

{% endnote %}

## Resource usage

Events are a powerful tool, but great power often comes at a cost.
The receiver of an event has the power to take up CPU and NET resources of the original sender of the event.

This is because the sender of the event is the one paying for the CPU and NET resources of the receiver, but often 
they have no control over, or even knowledge of, how much CPU and NET resources the receiver will use.



# Read-only Actions

Though you have direct access to the table data through `get_table_rows` (as discussed in the 
[reading state section](../web-applications/05_reading-state) of the web applications chapter),
the preferred way to read data from a smart contract is through read-only actions.

## What is a read-only action?

A read-only action is an action that does not modify the state of the blockchain.

It is a way to query data from a smart contract without changing its state, while also allowing the 
contract developer to define alternative structures for the data returned that isn't just the raw table data.

## Creating a read-only action

You create these in a similar way to regular actions, but you need to specify that the action is read-only.

```cpp
[[eosio::action, eosio::read_only]]
bool isactive(name user) {
    // Your logic here
    return true;
}
```

## Sending a read-only action

You shouldn't use the normal `push_transaction` or `send_transaction` API methods to call a read-only action.
Read-only actions do not need authorization arrays, or signatures, so to take advantage of this you can 
use the [`send_read_only_transaction` API method](../hyperion-api.md) instead.

### Using Wharfkit

If you are using [Wharfkit](https://wharfkit.com) (and you should be), you can call a read-only action like this:

```javascript
import { APIClient, Chains } from "@wharfkit/antelope"
import { ContractKit } from "@wharfkit/contract"

const contractKit = new ContractKit({
  client: new APIClient('https://history.deNotary.io'),
})

const contract = await contractKit.load("some.contract")

// .readonly(action, data?)
const result = await contract.readonly('isactive', {
    user: 'some.user'
});
```

## Returning complex data

Read-only actions can return complex data structures, not just simple types like `bool` or `uint64_t`.

```cpp
struct Result {
    name user;
    uint64_t balance;
    std::string status;
};

[[eosio::action, eosio::read_only]]
Result getuser(name user) {
    return Result{user, 1000, "active"};
}
```

## Limitations & Benefits

Read-only actions have some limitations:
- They cannot modify the state of the blockchain
- They cannot call other actions that modify state
- They cannot return data to another action, only to external callers (like web applications)

However, they also have benefits:
- They are not billed for CPU or NET usage
- They do not require authorization or signatures 
- You can combine data from multiple tables, saving HTTP requests
- You can return data in a format that is more convenient for your application
# Testing

The easiest way to test deNotary Smart Contracts is using VeRT (VM emulation RunTime for WASM-based blockchain contracts).

It is a JavaScript library that allows you to run deNotary smart contracts in a Node.js environment.
You use it along-side other testing libraries like Mocha, Chai, and Sinon.

This guide will use Mocha as the testing framework, and assumes you already know how mocha works, as well as JavaScript.

## Installation

If you're using [Contract-Flow](https://github.com/cheburashkalev/contract-flow) you already have everything installed, otherwise follow
the installation steps below.

We're going to install
- VeRT
- Mocha
- Chai

```shell
npm install -D @vaulta/vert mocha chai
```

You should also add `"type": "module"` to your `package.json`. 

To make life easier, add a test script to your `package.json` so that we can easily run tests from mocha. (change `.js` to `.ts` if you're using TypeScript)

```json
"scripts": {
  "test": "mocha tests/**/*.spec.js"
},
```

Your `package.json` will look something like this now:

```json
{
  "name": "your-project",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "test": "mocha tests/**/*.spec.js"
  },
  "devDependencies": {
    "@vaulta/vert": "^0.3.24",
    "chai": "^4.3.10",
    "mocha": "^10.2.0"
  }
}
```

## Testing

Create a `tests` directory and a test file that ends with `.spec.js` (or `.spec.ts` if you're using typescript).

### Setup your test file

Let's look at how to import our dependencies, setup the emulator and some accounts, and define a test.

```javascript
// tests/mycontract.spec.js

import { Blockchain, nameToBigInt, expectToThrow } from "@vaulta/vert";
import { assert } from "chai";

// instantiate the blockchain emulator
const blockchain = new Blockchain()

// Load a contract
const contract = blockchain.createContract(
    // The account to set the contract on
    'accountname', 
    // The path to the contract's wasm file
    'build/yourcontract'
)

// Create some accounts to work with
const [alice, bob] = blockchain.createAccounts('alice', 'bob')

// You can clear the tables in the 
// contract before each test
beforeEach(async () => {
    blockchain.resetTables()
})

describe('Testing Suite', () => {
    it('should do X', async () => {
        
        // Your test goes here...
        
    });
});
```

### Sending transactions

You can send transactions to your contract like this:

```javascript
const result = await contract.actions.youraction(
    // Parameters are passed as an array, and must match the types in the contract
    ['yourparams', 1]
).send(
    // To send the transaction you need to pass the name and permission
    // of the account that is sending it within .send()
    'alice@active'
);
```

### Getting table data

You can get the data from a table in your contract like this:

```javascript
const rows = contract.tables.yourtable(
    // Set the scope of the table
    nameToBigInt('accountname')
).getTableRow(
    // Find the row using the primary index
    nameToBigInt('alice')
);

// Make sure the row exists or fail the test
assert(!!rows, "User not found")
```

### Logging console output

If you're printing to the console in your contract, you can access the logs in your test files like this:

```javascript
console.log(contract.bc.console);
````

### Catching errors

If you want to test that your contract throws a specific error, you can use the `expectToThrow` function like this:

```javascript
expectToThrow(
    contract.actions.throwserror([]).send('bob@active'),
    'This will be the error inside check()'
)
```



## Troubleshooting

Sometimes you run into problems. If you have anything that isn't on this list, please reach out in the [Developers Telegram](https://t.me/antelopedevs) group.

### Seeing table deltas

Sometimes it's helpful to see the changes in tables after a transaction.
You can enable storage deltas and then print them out to see what has changed.

```javascript
blockchain.enableStorageDeltas()

contract.actions.youraction([]).send(...)

blockchain.printStorageDeltas()
blockchain.disableStorageDeltas()
```


### Exported memory

VeRT requires exported memory in your contract. 

If you are using CDT to compile your contracts, you need to export memory in your contract manually prior to version 4.1.0.

```bash
# if you don't have wabt:
apt-get install wabt
# export memory
wasm2wat FILENAME.wasm | sed -e 's|(memory |(memory (export "memory") |' > TMP_FILE.wat
wat2wasm -o FILENAME.wasm TMP_FILE.wat
rm TMP_FILE.wat
```

# Token Standard

DNLT token standard is a set of rules that all tokens on a blockchain must follow.
This allows for interoperability between different tokens and applications.

{% note tip %}

deNotary tokens support more than one token per contract, however in practice not 
many contracts will do this.

{% endnote %}

## Actions 

### create

```cpp
[[eosio::action]]
void create(const name& issuer, const asset& maximum_supply);
```

Creates a new token with a maximum supply limit, and sets the issuer account.
The `symbol` of the `asset` defined the precision (decimals) and the token ticker.
For instance, a maximum supply of `1000.0000 XYZ` means that the token has a precision of 4 decimals,
a ticker of `XYZ`, and a maximum supply of `1000`.

**Parameters:**
- `issuer` - The account that creates the token
- `maximum_supply` - The maximum supply set for the token created

**Preconditions:**
- Token symbol must not already exist

### issue

```cpp
[[eosio::action]]
void issue(const name& to, const asset& quantity, const string& memo);
```

Issues a specific quantity of tokens to an account.

**Preconditions:**
- Must be the issuer of the token

**Parameters:**
- `to` - The account to issue tokens to (must be the same as the issuer)
- `quantity` - The amount of tokens to be issued
- `memo` - The memo string that accompanies the token issue transaction

### retire

```cpp
[[eosio::action]]
void retire(const asset& quantity, const string& memo);
```

Effectively burns the specified quantity of tokens, removing them from circulation.
Only the token issuer can retire tokens.

**Parameters:**
- `quantity` - The quantity of tokens to retire
- `memo` - The memo string to accompany the transaction

### transfer

```cpp
[[eosio::action]]
void transfer(const name& from, const name& to, const asset& quantity, const string& memo);
```

Transfers a specified quantity of tokens from one account to another.

**Parameters:**
- `from` - The account to transfer from
- `to` - The account to be transferred to
- `quantity` - The quantity of tokens to be transferred
- `memo` - The memo string to accompany the transaction

### open

```cpp
[[eosio::action]]
void open(const name& owner, const symbol& symbol, const name& ram_payer);
```

Each account's balance is a row in a table, which costs 240 bytes of RAM.
This action creates a row in the table for the owner account and token symbol.
If this is not done, then the first sender of a token to an account that does 
not have tokens will pay the RAM cost of creating the row.

**Parameters:**
- `owner` - The account to be created
- `symbol` - The token to be paid with by ram_payer
- `ram_payer` - The account that supports the cost of this action

Additional information can be found in [issue #62](https://github.com/EOSIO/eosio.contracts/issues/62) and [issue #61](https://github.com/EOSIO/eosio.contracts/issues/61).

### close

```cpp
[[eosio::action]]
void close(const name& owner, const symbol& symbol);
```

This action is the opposite of open. 
It closes the row for an account for a specific token symbol and reclaims the RAM.

**Parameters:**
- `owner` - The owner account to execute the close action for
- `symbol` - The symbol of the token to execute the close action for

**Preconditions:**
- The pair of owner plus symbol must exist, otherwise no action is executed
- If the pair of owner plus symbol exists, the balance must be zero


## Tables

### Account data structure

```cpp
struct [[eosio::table]] account {
    asset    balance;
    uint64_t primary_key() const { return balance.symbol.code().raw(); }
};
```

The `account` struct represents an individual token account and stores the balance for a specific token symbol.


```cpp
typedef eosio::multi_index<"accounts"_n, account> accounts;
```

The `accounts` table stores token balances for all accounts.

- **Table Name:** `accounts`
- **Index Type:** Primary index on the token symbol code (ticker)
- **Scope:** The scope is the account name, which is the owner of the token balance

**Usage:**
- Stores balance information for each account and token combination
- Used during transfers to check balances and update them
- Queried when retrieving an account's balance for a specific token

### Fetching balances using [Wharfkit](https://wharfkit.com/)

For example try fetch DNLT balance

```typescript
import {APIClient} from "@wharfkit/session"

const client = new APIClient({ url: Chains.deNotary.url });

const result = await client.v1.chain.get_table_rows({
    json: true,
    code: 'eosio.token',
    scope: 'SOME_ACCOUNT_HERE',
    table: 'accounts',
});

/*
{
  rows: [
    {
      balance: "100.0000 DNLT",
    }
  ],
  more: false,
}
 */
```

### currency_stats

```cpp
struct [[eosio::table]] currency_stats {
    asset    supply;
    asset    max_supply;
    name     issuer;
    uint64_t primary_key() const { return supply.symbol.code().raw(); }
};
```

The `currency_stats` struct stores information about a token.

**Fields:**
- `supply` - The current supply of the token in circulation
- `max_supply` - The maximum possible supply of the token
- `issuer` - The account name of the token issuer who has authority to issue new tokens

```cpp
typedef eosio::multi_index<"stat"_n, currency_stats> stats;
```

The `stats` table stores information about each token type.

- **Table Name:** `stat`
- **Index Type:** Primary index on the token symbol code (ticker)
- **Scope:** The scope is the token symbol (ticker)

**Usage:**
- Stores supply, maximum supply, and issuer information for each token
- Checked during token operations to validate permissions and limits
- Used to enforce rules like maximum supply constraints
- Queried to get current supply and other token information

### Fetching stats using [Wharfkit](https://wharfkit.com/)
For example try fetch DNLT stat
```typescript
import {APIClient} from "@wharfkit/session"

const client = new APIClient({ url: Chains.deNotary.url });

const result = await client.v1.chain.get_table_rows({
    json: true,
    code: 'eosio.token',
    scope: 'DNLT',
    table: 'stat',
});

/*
{
  rows: [
    {
      supply: "2100000000.0000 DNLT",
      max_supply: "2100000000.0000 DNLT",
      issuer: "eosio.token",
    }
  ],
  more: false,
}

 */
```

# Language Support

Aside from C++, there are a number of community-led initiatives for extending language support for smart contracts
written for deNotary. 

Here is a list of currently maintained projects:

- [AssemblyScript](https://github.com/uuosio/ascdk)
- [Rust](https://github.com/uuosio/rscdk)
- [Golang](https://github.com/uuosio/gscdk)
- [Python](https://github.com/uuosio/pscdk)
# State API

## Servers
- **Production**: `https://history.deNotary.io/api`
- **Development**: `https://dev-history.deNotary.io/api`

## Endpoints

### `/sync`
- **GET**: StateApi status sync
  - **Responses:**
    - `200`: if successful `{"last_block_num":12616900,"head_block_num":19077303,"sync":6460403}`

---

### `/usercount`
- **GET**: User count in network
  - **Responses:**
    - `200`: if successful return `{"usercount":95}`

---

### `/userlist`
- **GET**: User list in network
  - **Parameters:**
    - **skip** (required, integer, int64): The number of users to skip.
      - Example: `1000`
  - **Responses:**
    - `200`: if successful return `[{"account":"eosio.bpay"},{"account":"eosio.vpay"}]`

---

### `/tokenbalance/{token_account}/{token_symbol}/{account_name}`
- **GET**: User token balance
  - **Parameters:**
    - **token_account** (required, string): The token account.
      - Example: `eosio.token`
    - **token_symbol** (required, string): The token symbol.
      - Example: `DNLT`
    - **account_name** (required, string): The account name.
      - Example: `todoboostamg`
  - **Responses:**
    - `200`: if successful return `{"balance":"59321693.8766 DNLT"}`

---

### `/holdercount/{token_account}/{token_symbol}`
- **GET**: Token holders count
  - **Parameters:**
    - **token_account** (required, string): The token account.
      - Example: `eosio.token`
    - **token_symbol** (required, string): The token symbol.
      - Example: `DNLT`
  - **Responses:**
    - `200`: if successful return `{"holders":79}`

---

### `/topholders/{token_account}/{token_symbol}/{limit}`
- **GET**: List topholders of token
  - **Parameters:**
    - **token_account** (required, string): The token account.
      - Example: `eosio.token`
    - **token_symbol** (required, string): The token symbol.
      - Example: `DNLT`
    - **limit** (required, integer, int64): The number of top holders to return.
      - Example: `1000`
  - **Responses:**
    - `200`: if successful return `[{"account":"eosio","amount":140000001,"balance":"140000001.0000 DNLT"}]`
# deNotary Dapps - Beginner Concepts

A lot of tutorials for building decentralized web applications dive straight into the code but do not explain 
the core conceptual differences between web2 development and web3 development. 

This guide will help you wrap your head around how decentralized applications work, what parts of the stack are
different, and how to think about the architecture of your decentralized applications.

## The blockchain comes packed with features

In traditional web2 development you need to roll your entire stack alone. Even if you use cloud providers like AWS, 
you still need to pick and choose which services you want to use and how to integrate them together.

In web3 development, the blockchain comes packed with every feature you need to build most applications.

| Feature | Description                                                                                                                                       |
| --- |---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Database** | The blockchain itself is just a massive database. **You** can also store data on the blockchain and query it.                                     |
| **Data replication** | Because of how a blockchain works, you get data replication across the entire network for **free**.                                               |
| **Authentication** | All blockchains come with built-in authentication and user management.                                                                            |
| **Payments** | One of the core functionalities of a blockchain is decentralized finance, and payments are made very easy.                                        |
| **Serverless Functions** | The blockchain has built-in serverless functions in the form of Smart Contracts.                                                                  |
| **Event Notifications** | You can subscribe to events that happen on the blockchain, similar to a message-queue or pub-sub. |

## You don't need a backend

In web2 development, you need to build a backend to store data and perform business logic. This might be a REST API or serverless functions.

In web3 development, can interact directly with the blockchain. You don't need to run your own backend infrastructure, kube clusters, or serverless functions.
It is very similar to serverless functions, except that the functions are run on a decentralized blockchain instead of a centralized cloud provider.

вќ” **You might still want to run infrastructure**

Using publicly available nodes or API services is great, but you might want to run your own infrastructure for security or performance reasons.
Take an exchange as an example. They generally run their own infrastructure to ensure that they can handle the load and that their data is secure.
Though transactions **sent** to the chain are always backed by cryptography, the results you get from node APIs can be tampered with.

### In some cases a backend helps

There are some cases where you might want to run your own backend. For example, if you want to store data that is not on the blockchain, or if you want to
perform business logic that is either too expensive to run on the blockchain, or takes too long and exceeds the maximum time allowed for smart contract execution.

You might also want to provide your applications with different ways to access the data stored on the blockchain that is easier for you 
to work with, like GraphQL or SQL queries. In that case you might want to build a backend that listens to the blockchain and stores the data you care about in a way that suits your needs. 

## Get comfortable with wallets

A blockchain wallet is a piece of software that manages private keys.
Wallets do not store any blockchain data within them, instead they use the private keys they manage to sign transactions that manipulate the blockchain.

In web2 development, you need to build your own authentication system. You might use a third-party service like Auth0, or you might roll your own.
Once your user logs in, you rely on their session to prove that they are who they say they are. 

You might add in additional security measures like 2FA, IP-user pairing, and a variety of other techniques. 

In web3 development life is simpler, your users will log in with a wallet instead. There are no passwords you need to authenticate yourself. 
You also don't need to rely on a session to prove that their interactions are coming from them, because every interaction (transaction) 
they make will be signed with the private key that their wallet controls.

вќ• **Proving logins**

Some applications want to prove that a user is who they say they are without requiring them to sign a transaction that gets
sent to the blockchain. In that case you can use a technique called **message signing**, where you ask the user to sign a message
with their private key, and then use that signature to prove their identity. 

## Big data doesn't belong on the blockchain

The blockchain is a database, but it is not a database that is meant to store large amounts of data. You can store that data on 
services specifically designed for that purpose, and then store the hash of that data on the blockchain. You will see this pattern
repeated over and over again in decentralized applications.

| Name                                    | Description                                                                                                                                     |
|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| [**IPFS**](https://ipfs.tech/)          | A peer-to-peer hypermedia protocol designed to preserve and grow humanity's knowledge by making the web upgradeable, resilient, and more open.  |
| [**Arweave**](https://www.arweave.org/) | The Arweave network is like Bitcoin, but for data: A permanent and decentralized web inside an open ledger.                                     |


## Your frontend is just an experience

Unlike web2 development, where your frontend is tightly coupled to your backend, in web3 development your frontend is just an experience layer.

Your frontend will interact with the blockchain directly, which means 100% of the security for your applications lives on the blockchain. It's 
important to remember that, because it means that users have the ability to interact with your contracts directly, and 
no matter what controls you build into the frontend, they can always bypass them.

вќ” **Co-signing**

You can actually prevent people from interacting with your contracts directly by creating a backend that co-signs transactions
for every interaction the user takes. This is non-standard and usually indicative of a game theory design flaw, but it 
is used in some cases to prevent botting and other forms of cheating/abuse.
# JavaScript SDK

You can use [WharfKit](https://wharfkit.com/guides) to interact with deNotary from a web browser or Node.js application.

Check out their excellent [Getting Started Guide](https://wharfkit.com/guides/session-kit/getting-started-web-app) to learn how to use the SDK to make a transaction.
# Reading State

Please note that this guide is for reading raw state data. It is preferable to 
use `read-only` actions to read data so that it can be returned in a structured way 
that is useful for your application.

See [Read-only Actions](../smart-contracts/08_read-only-actions) for more information.

## Prerequisites

To follow this guide, you will need:

- An understanding of the deNotary blockchain and how it works.
- A command-line interface to run curl commands.
- Access to a deNotary node or a deNotary API service.

## deNotary Tables

deNotary stores data in tables, which are similar to database tables. Each table has a name and a set of fields. Tables are 
organized into scopes, which are defined by the smart contract that created the table.

To retrieve data from a table, you need to know its name, scope, and the name of the smart contract that created it. You 
can also specify a lower and upper bound to limit the amount of data returned.

## Methods to Retrieve Data from deNotary Tables

### Use get_table_rows Function

The `get_table_rows` function retrieves rows from a table. It takes the following parameters in JSON format:

- `"code"`: the deNotary account name which is the owner of the smart contract that created the table.
- `"scope"`: the scope of the table, it is a deNotary account name.
- `"table"`: a string representing the name of the table.
- `"json"`: (optional) a boolean value that specifies whether to return the row results in JSON format or binary format, defaults to binary.
- `"lower_bound"`: (optional) a string representing the lower bound for the table key, defaults to first value of the index used.
- `"upper_bound"`: (optional) a string representing the upper bound for the table key, defaults to the last value of the index used.
- `"index_position"`: (optional) the position of the index to use if the table has multiple indexes, accepted values are `primary`, `secondary`, `tertiary`, `fourth`, `fifth`, `sixth`, `seventh`, `eighth`, `ninth` , `tenth`, defaults to `primary`.
- `"key_type"`: (optional) a string representing the type of the table key, supported values `i64`, `i128`, `i256`, `float64`, `float128`, `sha256`, `ripemd160`, `name`.
- `"encode_type"`: (optional) a string representing the encoded type of the key_type parameter, either `dec` or `hex`, defaults to `dec`.
- `"limit"`: limits the number of results returned, defaults to 10.
- `"time_limit_ms"`: (optional) the maximum time should spend to retrieve the results, defaults to 10ms.
- `"reverse"`: (options) if `true` the results are retrieved in reverse order, from lower_bound up towards upper_bound, defaults to `false`.

Below is an example that retrieves rows from `abihash` table, owned by the `eosio` account and having as `scope` the `eosio` name.

```shell
curl --request POST \
--url https://history.deNotary.io/v1/chain/get_table_rows \
--header 'content-type: application/json' \
--data '{
"json": true,
"code": "eosio",
"scope": "eosio",
"table": "abihash",
"lower_bound": "eosio",
"limit": 3,
"reverse": false
}'
```

In the example above:

- The rows values are returned as JSON, set by the `json` parameter.
- The table is owned by the account `eosio`, set by the `code` parameter.
- The table scope is `eosio`, set by the `scope` parameter.
- The table name is `abihash.`, set by the `table` parameter.
- The query uses the primary index to search the rows and starts from the `eosio` lower bound index value, set by the `lower_bound` parameter.
- The function will fetch a maximum of 3 rows, set by the `limit` parameter.
- The retrieved rows will be in ascending order, set by the `reverse` parameter.


#### The get_table_rows Result

The JSON returned by the `get_table_rows` has the following structure:

```json
{
  "rows": [
    { },
    ...
    { }
  ],
  "more": true,
  "next_key": ""
}
```

The `"rows"` field is an array of table row objects in JSON representation.
The `"more"` field indicates that there are additional rows beyond the ones returned.
The `"next_key"` field contains the key to be used as the lower bound in the next request to retrieve the next set of rows.

For example, the result from the previous section command contains three rows, and looks similar to the one below:

```json
{
  "rows": [
    {
      "owner": "eosio",
      "hash": "00e166885b16bcce50fea9ea48b6bd79434cb845e8bc93cf356ff787e445088c"
    },
    {
      "owner": "eosio.assert",
      "hash": "aad0ac9f3f3d8f71841d82c52080f99479e869cbde5794208c9cd08e94b7eb0f"
    },
    {
      "owner": "eosio.evm",
      "hash": "9f238b42f5a4be3b7f97861f90d00bbfdae03e707e5209a4c22d70dfbe3bcef7"
    }
  ],
  "more": true,
  "next_key": "6138663584080503808"
}
```

#### The get_table_rows Pagination

Note that the previous command has the `"more"` field set to `true`. That means there's more rows in the table, which match the filter used, that were not returned with the first issued command.

The `"next_key"`, `"lower_bound"` and `"upper_bound"` fields, can be used to implement pagination or iterative retrieval of data from any table in the deNotary blockchain.

To fetch the next set of rows, you can issue another `get_table_rows` request, modifying the lower bound to be the value of the `"next_key"` field:

```shell
curl --request POST \
--url https://history.deNotary.io/v1/chain/get_table_rows \
--header 'content-type: application/json' \
--data '{
"json": true,
"code": "eosio",
"scope": "eosio",
"table": "abihash",
"lower_bound": "6138663584080503808",
"limit": 3,
"reverse": false
}'
```

The above command returns the subsequent 3 rows from the `abihash` table with the producer name value greater than `"6138663584080503808"`. By iterating this process, you can retrieve all the rows in the table.

If the response from the second request includes `"more": false`, it means that you have fetched all the available rows, which match the filter, and there is no need for further requests.

### Use get_table_by_scope Function

The purpose of `get_table_by_scope` is to scan the table names under a given `code` account, using `scope` as the primary key. 
If you already know the table name, e.g. `mytable`, it is not necessary to use `get_table_by_scope` unless you want to find out what 
are the scopes that have defined the `mytable` table.

These are the input parameters supported by `get_table_by_scope`:

- `"code"`: the deNotary account name which is the owner of the smart contract that created the table.
- `"table"`: a string representing the name of the table.
- `"lower_bound"` (optional): This field specifies the lower bound of the scope when querying for table rows. It determines the starting point for fetching rows based on the scope value. Defaults to first value of the scope.
- `"upper_bound"` (optional): This field specifies the upper bound of the scope when querying for table rows. It determines the ending point for fetching rows based on the scope value.  Defaults to last value of the scope.
- `"limit"` (optional): This field indicates the maximum number of rows to be returned in the function. It allows you to control the number of rows retrieved in a single request.
- `"reverse"` (optional): if `true` the results are retrieved in reverse order, from lower_bound up towards upper_bound, defaults to `false`.
- `"time_limit_ms"`: (optional) the maximum time should spend to retrieve the results, defaults to 10ms.

Below is an example JSON payload for the get_table_by_scope function:

```json
{
  "code": "accountname1",
  "table": "tablename",
  "lower_bound": "accountname2",
  "limit": 10,
  "reverse": false,
}
```

In the example above:

- The table is owned by the account `accountname1`, set by the `code` parameter.
- The table name is `tablename.`, set by the `table` parameter.
- The query starts from the `accountname2` scope value, set by the `lower_bound` parameter.
- The function will fetch a maximum of 10 rows, set by the `limit` parameter.
- The retrieved rows will be in ascending order, set by the `reverse` parameter.

#### The get_table_by_scope Result

The `get_table_by_scope` returns a JSON object containing information about the tables within the specified scope. The return JSON has the following fields:

- `"rows"`: This field contains an array of tables.
- `"more"`: This field indicates whether there are more results available. If it is set to true, it means there are additional rows that can be fetched using pagination. See previous section for more details on how to retrieve additional rows.

Each table row is represented by a JSON object that contains the following fields:

- `"code"`: The account name of the contract that owns the table.
- `"scope"`: The scope within the contract in which the table is found. It represents a specific instance or category within the contract.
- `"table"`: The name of the table as specified by the contract ABI.
- `"payer"`: The account name of the payer who covers the RAM cost for storing the row.
- `"count"`: The number of rows in the table multiplied by the number of indices defined by the table (including the primary index). For example, if the table has only the primary index defined then the `count` represents the number of rows in the table; for each additional secondary index defined for the table the count represents the number of rows multiplied by N where N = 1 + the number of secondary indices.

##### Empty Result

It is possible that the returned JSON looks like the one below:

```json
{
    "rows":[],
    "more": "accountname"
}
```

The above result means your request did not finish its execution due to the transaction time limit imposed by the blockchain configuration. The result tells you it did not find any table (`rows` field is empty) from the specified `lower_bound` to the `"accountname"` bound. In this case you must execute the request again with `lower_bound` set to the value provided by the `"more"` field, in this case `accountname`.

#### Real Example

For a real example, you can list the first three tables named `accounts` owned by the `eosio.token` account starting with the lower bound scope `abc`:

```shell
curl --request POST \
--url https://history.deNotary.io/v1/chain/get_table_by_scope \
--header 'content-type: application/json' \
--data '{
"json": true,
"code": "eosio.token",
"table": "accounts",
"lower_bound": "abc",
"upper_bound": "",
"reverse": false,
"limit": "3"
}'
```

The result looks similar to the one below:

```json
{
  "rows": [
    {
      "code": "eosio.token",
      "scope": "abc",
      "table": "accounts",
      "payer": "abc.com",
      "count": 1
    },
    {
      "code": "eosio.token",
      "scope": "abc.bank",
      "table": "accounts",
      "payer": "alibaba.com",
      "count": 1
    },
    {
      "code": "eosio.token",
      "scope": "abc.com",
      "table": "accounts",
      "payer": "vuniyuoxoeub",
      "count": 1
    }
  ],
  "more": "abc.gm"
}
```





