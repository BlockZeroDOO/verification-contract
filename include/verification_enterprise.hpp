#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <request_key.hpp>
#include <verification_core.hpp>
#include <verification_request_size.hpp>
#include <verification_tables.hpp>
#include <verification_validators.hpp>

#include <string>

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
    void billsubmit(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& object_hash,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void retailsub(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& object_hash,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void billbatch(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& root_hash,
        uint32_t leaf_count,
        const checksum256& manifest_hash,
        const checksum256& external_ref
    );

    [[eosio::action]]
    void retailbatch(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& root_hash,
        uint32_t leaf_count,
        const checksum256& manifest_hash,
        const checksum256& external_ref
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

    struct [[eosio::table("authsources")]] auth_source_config {
        name billing_account = "verifbill"_n;
        name retail_payment_account = "verifretpay"_n;
    };

    using auth_source_singleton = singleton<"authsources"_n, auth_source_config>;

    schema_row require_schema(uint64_t id) const;
    policy_row require_policy(uint64_t id) const;
    auth_source_config get_auth_source_config() const;
    void require_internal_registry_caller(const name& expected_contract) const;
    void anchor_single_request(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& object_hash,
        const checksum256& external_ref
    );
    void anchor_batch_request(
        const name& submitter,
        uint64_t schema_id,
        uint64_t policy_id,
        const checksum256& root_hash,
        uint32_t leaf_count,
        const checksum256& manifest_hash,
        const checksum256& external_ref
    );
    uint64_t next_batch_id();
    uint64_t next_commitment_id();
    void validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const;
    void validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const;
};
