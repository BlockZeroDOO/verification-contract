#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/time.hpp>

namespace verification_billing_tables {

using eosio::asset;
using eosio::checksum256;
using eosio::const_mem_fun;
using eosio::indexed_by;
using eosio::multi_index;
using eosio::name;
using eosio::singleton;
using eosio::symbol;
using eosio::symbol_code;
using eosio::time_point_sec;

struct [[eosio::table("billtokens")]] accepted_token_row {
    uint64_t config_id;
    name token_contract;
    symbol token_symbol;
    bool enabled;
    time_point_sec updated_at;

    uint64_t primary_key() const { return config_id; }
    uint128_t bytokensym() const {
        return (static_cast<uint128_t>(token_contract.value) << 64) |
               token_symbol.code().raw();
    }
};

using accepted_token_table = multi_index<
    "billtokens"_n,
    accepted_token_row,
    indexed_by<"bytokensym"_n, const_mem_fun<accepted_token_row, uint128_t, &accepted_token_row::bytokensym>>
>;

struct [[eosio::table("plans")]] plan_row {
    uint64_t plan_id;
    name plan_code;
    name token_contract;
    asset price;
    uint32_t duration_sec;
    uint64_t single_quota;
    uint64_t batch_quota;
    bool active;
    time_point_sec updated_at;

    uint64_t primary_key() const { return plan_id; }
    uint64_t bycode() const { return plan_code.value; }
    uint128_t bytokensym() const {
        return (static_cast<uint128_t>(token_contract.value) << 64) |
               price.symbol.code().raw();
    }
};

using plan_table = multi_index<
    "plans"_n,
    plan_row,
    indexed_by<"bycode"_n, const_mem_fun<plan_row, uint64_t, &plan_row::bycode>>,
    indexed_by<"bytokensym"_n, const_mem_fun<plan_row, uint128_t, &plan_row::bytokensym>>
>;

struct [[eosio::table("packs")]] pack_row {
    uint64_t pack_id;
    name pack_code;
    name token_contract;
    asset price;
    uint64_t single_units;
    uint64_t batch_units;
    bool active;
    time_point_sec updated_at;

    uint64_t primary_key() const { return pack_id; }
    uint64_t bycode() const { return pack_code.value; }
    uint128_t bytokensym() const {
        return (static_cast<uint128_t>(token_contract.value) << 64) |
               price.symbol.code().raw();
    }
};

using pack_table = multi_index<
    "packs"_n,
    pack_row,
    indexed_by<"bycode"_n, const_mem_fun<pack_row, uint64_t, &pack_row::bycode>>,
    indexed_by<"bytokensym"_n, const_mem_fun<pack_row, uint128_t, &pack_row::bytokensym>>
>;

struct [[eosio::table("entitlements")]] entitlement_row {
    uint64_t entitlement_id;
    name payer;
    uint8_t kind;
    uint64_t plan_id;
    uint64_t pack_id;
    uint64_t single_remaining;
    uint64_t batch_remaining;
    time_point_sec active_from;
    time_point_sec expires_at;
    uint8_t status;
    time_point_sec updated_at;

    uint64_t primary_key() const { return entitlement_id; }
    uint64_t bypayer() const { return payer.value; }
    uint64_t bystatus() const { return static_cast<uint64_t>(status); }
};

using entitlement_table = multi_index<
    "entitlements"_n,
    entitlement_row,
    indexed_by<"bypayer"_n, const_mem_fun<entitlement_row, uint64_t, &entitlement_row::bypayer>>,
    indexed_by<"bystatus"_n, const_mem_fun<entitlement_row, uint64_t, &entitlement_row::bystatus>>
>;

struct [[eosio::table("usageauths")]] usage_auth_row {
    uint64_t auth_id;
    name payer;
    name submitter;
    uint8_t mode;
    checksum256 request_key;
    uint64_t entitlement_id;
    bool consumed;
    time_point_sec created_at;
    time_point_sec consumed_at;
    time_point_sec expires_at;

    uint64_t primary_key() const { return auth_id; }
    checksum256 byrequest() const { return request_key; }
    uint64_t bysubmitter() const { return submitter.value; }
};

using usage_auth_table = multi_index<
    "usageauths"_n,
    usage_auth_row,
    indexed_by<"byrequest"_n, const_mem_fun<usage_auth_row, checksum256, &usage_auth_row::byrequest>>,
    indexed_by<"bysubmitter"_n, const_mem_fun<usage_auth_row, uint64_t, &usage_auth_row::bysubmitter>>
>;

struct [[eosio::table("billcounters")]] counter_state {
    uint64_t next_token_id = 1;
    uint64_t next_plan_id = 1;
    uint64_t next_pack_id = 1;
    uint64_t next_entitlement_id = 1;
    uint64_t next_usageauth_id = 1;
};

using counter_singleton = singleton<"billcounters"_n, counter_state>;

}  // namespace verification_billing_tables
