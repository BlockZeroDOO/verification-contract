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
#include <verification_billing_tables.hpp>
#include <verification_core.hpp>
#include <verification_retail_payment_tables.hpp>
#include <verification_tables.hpp>
#include <verification_validators.hpp>

#include <string>
#include <tuple>

using namespace eosio;
using std::string;

class [[eosio::contract("verif")]] verification_enterprise : public contract {
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
    void setauthsrcs(const name& billing_account, const name& retail_payment_account);

    [[eosio::action]]
    void submit(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& object_hash,
        const checksum256& external_ref,
        uint64_t billable_bytes
    );

    [[eosio::action]]
    void submitroot(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& root_hash,
        uint32_t leaf_count,
        const checksum256& manifest_hash,
        const checksum256& external_ref,
        uint64_t billable_bytes
    );

    [[eosio::action]]
    void withdraw(
        const name& token_contract,
        const name& to,
        const asset& quantity,
        const string& memo
    );

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
    using enterprise_usage_auth_row = verification_billing_tables::usage_auth_row;
    using enterprise_usage_auth_table = verification_billing_tables::usage_auth_table;
    using retail_usage_auth_row = verification_retail_payment_tables::usage_auth_row;
    using retail_usage_auth_table = verification_retail_payment_tables::usage_auth_table;

    struct usage_authorization_ref {
        name source_contract;
        uint64_t auth_id;
    };

    struct [[eosio::table("authsources")]] auth_source_config {
        name billing_account = "verifbill"_n;
        name retail_payment_account = "verifretpay"_n;
    };

    using auth_source_singleton = singleton<"authsources"_n, auth_source_config>;

    static constexpr uint8_t enterprise_mode_single = 0;
    static constexpr uint8_t enterprise_mode_batch = 1;

    schema_row require_schema(uint64_t id) const;
    policy_row require_policy(uint64_t id) const;
    auth_source_config get_auth_source_config() const;
    usage_authorization_ref require_usage_authorization(
        uint8_t mode,
        const name& submitter,
        const checksum256& external_ref,
        uint64_t billable_bytes,
        uint64_t billable_kib
    ) const;
    void consume_usage_authorization(const usage_authorization_ref& authorization) const;
    uint64_t next_batch_id();
    uint64_t next_commitment_id();
    void validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const;
    void validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const;
};
