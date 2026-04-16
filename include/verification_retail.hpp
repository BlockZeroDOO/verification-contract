#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>
#include <eosio/transaction.hpp>

#include <request_key.hpp>
#include <verification_core.hpp>
#include <verification_retail_tables.hpp>
#include <verification_tables.hpp>
#include <verification_validators.hpp>

#include <string>
#include <tuple>

using namespace eosio;
using std::string;

class [[eosio::contract("verifretail")]] verification_retail : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void addschema(
        uint64_t id,
        const string& version,
        const checksum256& canonicalization_hash,
        const checksum256& hash_policy
    );

    [[eosio::action]]
    void updateschema(
        uint64_t id,
        const string& version,
        const checksum256& canonicalization_hash,
        const checksum256& hash_policy
    );

    [[eosio::action]]
    void deprecate(uint64_t id);

    [[eosio::action]]
    void setpolicy(
        uint64_t id,
        bool allow_single,
        bool allow_batch,
        bool active
    );

    [[eosio::action]]
    void submit(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& object_hash,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void submitroot(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& root_hash,
        uint32_t leaf_count,
        const checksum256& manifest_hash,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void settoken(const name& token_contract, const symbol& token_symbol);

    [[eosio::action]]
    void rmtoken(const name& token_contract, const symbol_code& token_symbol);

    [[eosio::action]]
    void setprice(uint8_t mode, const name& token_contract, const asset& price);

    [[eosio::action]]
    void withdraw(
        const name& token_contract,
        const name& to,
        const asset& quantity,
        const string& memo
    );

    [[eosio::on_notify("*::transfer")]]
    void ontransfer(const name& from, const name& to, const asset& quantity, const string& memo);

private:
    using schema_row = verification_tables::schema_row;
    using schema_table = verification_tables::schema_table;
    using policy_row = verification_tables::policy_row;
    using policy_table = verification_tables::policy_table;
    using commitment_row = verification_tables::commitment_row;
    using commitment_table = verification_tables::commitment_table;
    using batch_row = verification_tables::batch_row;
    using batch_table = verification_tables::batch_table;
    using counter_state = verification_tables::counter_state;
    using counter_singleton = verification_tables::counter_singleton;
    using accepted_token_row = verification_retail_tables::accepted_token_row;
    using accepted_token_table = verification_retail_tables::accepted_token_table;
    using tariff_row = verification_retail_tables::tariff_row;
    using tariff_table = verification_retail_tables::tariff_table;
    using payment_receipt_row = verification_retail_tables::payment_receipt_row;
    using payment_receipt_table = verification_retail_tables::payment_receipt_table;
    using retail_counter_state = verification_retail_tables::retail_counter_state;
    using retail_counter_singleton = verification_retail_tables::retail_counter_singleton;

    static constexpr uint8_t retail_mode_single = 0;
    static constexpr uint8_t retail_mode_batch = 1;

    uint128_t make_payment_key(const name& token_contract, const symbol_code& token_symbol) const;
    schema_row require_schema(uint64_t id) const;
    policy_row require_policy(uint64_t id) const;
    uint64_t next_batch_id();
    uint64_t next_commitment_id();
    void validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const;
    void validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const;
    accepted_token_row require_accepted_token(const name& token_contract, const symbol_code& token_symbol) const;
    tariff_row require_tariff(uint8_t mode, const name& token_contract, const symbol& token_symbol) const;
    payment_receipt_row require_pending_receipt(
        uint8_t mode,
        const name& submitter,
        const checksum256& external_ref
    ) const;
    uint64_t next_retail_token_id();
    uint64_t next_retail_tariff_id();
    uint64_t next_retail_receipt_id();
    std::tuple<uint8_t, name, checksum256> parse_payment_memo(const string& memo) const;
    void consume_receipt(uint64_t receipt_id);
};
