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
    uint64_t billable_bytes;
    uint64_t billable_kib;
    checksum256 external_ref;
    checksum256 request_key;
    time_point_sec created_at;

    uint64_t primary_key() const { return id; }
    uint64_t by_submitter() const { return submitter.value; }
    uint64_t by_schema_id() const { return schema_id; }
    uint64_t by_policy_id() const { return policy_id; }
    checksum256 by_request() const { return request_key; }
    checksum256 by_external_ref() const { return external_ref; }
};

using commitment_table = multi_index<
    "commitments"_n,
    commitment_row,
    indexed_by<"bysubmitter"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_submitter>>,
    indexed_by<"byschemaid"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_schema_id>>,
    indexed_by<"bypolicyid"_n, const_mem_fun<commitment_row, uint64_t, &commitment_row::by_policy_id>>,
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
    uint64_t billable_bytes;
    uint64_t billable_kib;
    checksum256 external_ref;
    checksum256 request_key;
    time_point_sec created_at;

    uint64_t primary_key() const { return id; }
    uint64_t by_submitter() const { return submitter.value; }
    uint64_t by_schema_id() const { return schema_id; }
    uint64_t by_policy_id() const { return policy_id; }
    checksum256 by_request() const { return request_key; }
    checksum256 by_external_ref() const { return external_ref; }
};

using batch_table = multi_index<
    "batches"_n,
    batch_row,
    indexed_by<"bysubmitter"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_submitter>>,
    indexed_by<"byschemaid"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_schema_id>>,
    indexed_by<"bypolicyid"_n, const_mem_fun<batch_row, uint64_t, &batch_row::by_policy_id>>,
    indexed_by<"byrequest"_n, const_mem_fun<batch_row, checksum256, &batch_row::by_request>>,
    indexed_by<"byexternal"_n, const_mem_fun<batch_row, checksum256, &batch_row::by_external_ref>>
>;

struct [[eosio::table("counters")]] counter_state {
    uint64_t next_commitment_id = 1;
    uint64_t next_batch_id = 1;
};

using counter_singleton = singleton<"counters"_n, counter_state>;

}  // namespace verification_tables
