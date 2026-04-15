#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/time.hpp>

#include <request_key.hpp>

#include <string>

namespace verification_tables {

using eosio::checksum256;
using eosio::const_mem_fun;
using eosio::indexed_by;
using eosio::multi_index;
using eosio::name;
using eosio::singleton;
using eosio::time_point_sec;
using eosio::asset;
using std::string;

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
    time_point_sec status_changed_at;
    uint8_t status;
    uint64_t superseded_by;

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

struct [[eosio::table("batches")]] batch_row {
    uint64_t id;
    name submitter;
    checksum256 root_hash;
    uint32_t leaf_count;
    uint64_t schema_id;
    uint64_t policy_id;
    checksum256 manifest_hash;
    checksum256 external_ref;
    checksum256 request_key;
    uint32_t block_num;
    time_point_sec created_at;
    time_point_sec manifest_linked_at;
    time_point_sec status_changed_at;
    uint8_t status;

    uint64_t primary_key() const { return id; }
    uint64_t by_submitter() const { return submitter.value; }
    uint64_t by_schema_id() const { return schema_id; }
    uint64_t by_policy_id() const { return policy_id; }
    uint64_t by_status() const { return static_cast<uint64_t>(status); }
    checksum256 by_request() const { return request_key; }
    checksum256 by_external_ref() const { return external_ref; }
};

using batch_table = multi_index<
    "batches"_n,
    batch_row,
    indexed_by<"bysubmitter"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_submitter>>,
    indexed_by<"byschemaid"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_schema_id>>,
    indexed_by<"bypolicyid"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_policy_id>>,
    indexed_by<"bystatus"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_status>>,
    indexed_by<"byrequest"_n, const_mem_fun<batch_row, checksum256, &batch_row::by_request>>,
    indexed_by<"byexternal"_n, const_mem_fun<batch_row, checksum256, &batch_row::by_external_ref>>
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

}  // namespace verification_tables
