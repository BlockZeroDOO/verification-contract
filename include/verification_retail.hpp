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

class [[eosio::contract("verification_retail")]] verification_retail : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void issuekyc(
        const name& account,
        uint8_t level,
        const string& provider,
        const string& jurisdiction,
        const time_point_sec& expires_at
    );

    [[eosio::action]]
    void renewkyc(const name& account, const time_point_sec& expires_at);

    [[eosio::action]]
    void revokekyc(const name& account);

    [[eosio::action]]
    void suspendkyc(const name& account);

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
        bool require_kyc,
        uint8_t min_kyc_level,
        bool active
    );

    [[eosio::action]]
    void enablezk(uint64_t id);

    [[eosio::action]]
    void disablezk(uint64_t id);

    [[eosio::action]]
    void submit(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& object_hash,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void supersede(uint64_t id, uint64_t successor_id);

    [[eosio::action]]
    void revokecmmt(uint64_t id);

    [[eosio::action]]
    void expirecmmt(uint64_t id);

    [[eosio::action]]
    void submitroot(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& root_hash,
        uint32_t leaf_count,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void linkmanifest(uint64_t id, const checksum256& manifest_hash);

    [[eosio::action]]
    void closebatch(uint64_t id);

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
    using kyc_row = verification_tables::kyc_row;
    using kyc_table = verification_tables::kyc_table;
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
    using proof_row = verification_tables::proof_row;
    using proof_table = verification_tables::proof_table;
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
    kyc_row require_kyc_record(const name& account) const;
    schema_row require_schema(uint64_t id) const;
    policy_row require_policy(uint64_t id) const;
    uint64_t next_batch_id();
    uint64_t next_commitment_id();
    void validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const;
    void validate_batch_is_open(const batch_row& batch) const;
    void validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const;
    void validate_commitment_can_be_successor(const commitment_row& current, const commitment_row& successor) const;
    void validate_commitment_is_active(const commitment_row& commitment) const;
    void validate_new_request(const name& submitter, const string& client_reference) const;
    void store_proof(
        const name& submitter,
        const checksum256& object_hash,
        const string& canonicalization_profile,
        const string& client_reference
    );
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

