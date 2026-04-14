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

#include <string>
#include <tuple>

using namespace eosio;
using std::string;

class [[eosio::contract("verification")]] verification : public contract {
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
    void supersede(uint64_t id);

    [[eosio::action]]
    void revokecmmt(uint64_t id);

    [[eosio::action]]
    void expirecmmt(uint64_t id);

    [[eosio::action]]
    void record(
        const name& submitter,
        const checksum256& object_hash,
        const string& canonicalization_profile,
        const string& client_reference
    );

    [[eosio::action]]
    void setpaytoken(
        const name& token_contract,
        const asset& price
    );

    [[eosio::action]]
    void rmpaytoken(const name& token_contract, const symbol& token_symbol);

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
    struct [[eosio::table("kyc")]] kyc_row {
        name account;
        uint8_t level;
        string provider;
        string jurisdiction;
        bool active;
        time_point_sec issued_at;
        time_point_sec expires_at;

        uint64_t primary_key() const { return account.value; }
    };

    using kyc_table = multi_index<"kyc"_n, kyc_row>;

    struct [[eosio::table("schemas")]] schema_row {
        uint64_t id;
        string version;
        checksum256 canonicalization_hash;
        checksum256 hash_policy;
        bool active;
        time_point_sec created_at;
        time_point_sec updated_at;

        uint64_t primary_key() const { return id; }
    };

    using schema_table = multi_index<"schemas"_n, schema_row>;

    struct [[eosio::table("policies")]] policy_row {
        uint64_t id;
        bool allow_single;
        bool allow_batch;
        bool require_kyc;
        uint8_t min_kyc_level;
        bool allow_zk;
        bool active;
        time_point_sec created_at;
        time_point_sec updated_at;

        uint64_t primary_key() const { return id; }
    };

    using policy_table = multi_index<"policies"_n, policy_row>;

    struct [[eosio::table("commitments")]] commitment_row {
        uint64_t id;
        name submitter;
        uint64_t schema_id;
        uint64_t policy_id;
        checksum256 object_hash;
        checksum256 external_ref;
        checksum256 request_key;
        uint32_t block_num;
        time_point_sec created_at;
        uint8_t status;

        uint64_t primary_key() const { return id; }
        uint64_t by_submitter() const { return submitter.value; }
        uint64_t by_schema_id() const { return schema_id; }
        uint64_t by_policy_id() const { return policy_id; }
        uint64_t by_status() const { return static_cast<uint64_t>(status); }
        checksum256 by_request() const { return request_key; }
        checksum256 by_external_ref() const { return external_ref; }
    };

    using commitment_table = multi_index<
        "commitments"_n,
        commitment_row,
        indexed_by<"bysubmitter"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_submitter>>,
        indexed_by<"byschemaid"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_schema_id>>,
        indexed_by<"bypolicyid"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_policy_id>>,
        indexed_by<"bystatus"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_status>>,
        indexed_by<"byrequest"_n, const_mem_fun<commitment_row, checksum256, &commitment_row::by_request>>,
        indexed_by<"byexternal"_n, const_mem_fun<commitment_row, checksum256, &commitment_row::by_external_ref>>
    >;

    struct [[eosio::table("counters")]] counter_state {
        uint64_t next_commitment_id = 1;
        uint64_t next_batch_id = 1;
        uint64_t next_proof_id = 1;
    };

    using counter_singleton = singleton<"counters"_n, counter_state>;

    struct [[eosio::table("proofs")]] proof_row {
        uint64_t proof_id;
        name writer;
        name submitter;
        checksum256 object_hash;
        string canonicalization_profile;
        string client_reference;
        time_point_sec submitted_at;

        uint64_t primary_key() const { return proof_id; }
        uint64_t by_submitter() const { return submitter.value; }
        checksum256 by_request() const { return verification_common::compute_request_key(submitter, client_reference); }
    };

    using proof_table = multi_index<
        "proofs"_n,
        proof_row,
        indexed_by<"bysubmitter"_n, const_mem_fun<proof_row, uint64_t, &proof_row::by_submitter>>,
        indexed_by<"byrequest"_n, const_mem_fun<proof_row, checksum256, &proof_row::by_request>>
    >;

    struct [[eosio::table("paytokens")]] payment_token {
        uint64_t config_id;
        name token_contract;
        asset price;
        time_point_sec updated_at;

        uint64_t primary_key() const { return config_id; }
        uint128_t bytokensym() const {
            return (static_cast<uint128_t>(token_contract.value) << 64) |
                   price.symbol.code().raw();
        }
    };

    using payment_token_table = multi_index<
        "paytokens"_n,
        payment_token,
        indexed_by<"bytokensym"_n, const_mem_fun<payment_token, uint128_t, &payment_token::bytokensym>>
    >;

    static constexpr uint8_t hash_size = 32;
    static constexpr uint8_t commitment_status_active = 0;
    static constexpr uint8_t commitment_status_superseded = 1;
    static constexpr uint8_t commitment_status_revoked = 2;
    static constexpr uint8_t commitment_status_expired = 3;

    uint128_t make_payment_key(const name& token_contract, const symbol_code& token_symbol) const;
    payment_token get_payment_token(const name& token_contract, const symbol_code& token_symbol) const;
    kyc_row require_kyc_record(const name& account) const;
    schema_row require_schema(uint64_t id) const;
    policy_row require_policy(uint64_t id) const;
    uint64_t next_commitment_id();
    asset resolve_price(const name& token_contract, const symbol& token_symbol) const;
    checksum256 parse_hash(const string& hex) const;
    void validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const;
    void validate_commitment_is_active(const commitment_row& commitment) const;
    void validate_future_time(const time_point_sec& value, const char* field_name) const;
    void validate_registry_id(uint64_t id, const char* field_name) const;
    void validate_client_reference(const string& client_reference) const;
    void validate_policy_settings(
        bool allow_single,
        bool allow_batch,
        bool require_kyc,
        uint8_t min_kyc_level,
        bool allow_zk,
        bool active
    ) const;
    void validate_printable_ascii_text(
        const string& value,
        uint32_t max_length,
        const char* field_name,
        bool allow_empty
    ) const;
    void validate_payment_price(const asset& price, const char* field_name) const;
    void validate_nonnegative_asset(const asset& quantity, const char* field_name) const;
    std::tuple<string, string, string, string> parse_payment_memo(const string& memo) const;
    uint8_t from_hex(char c) const;
    void validate_new_request(const name& submitter, const string& client_reference) const;
    void store_proof(
        const name& submitter,
        const checksum256& object_hash,
        const string& canonicalization_profile,
        const string& client_reference
    );
    void validate_text(const string& value, uint32_t max_length, const char* field_name, bool allow_empty) const;
};
