#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/time.hpp>

namespace verification_retail_payment_tables {

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

struct [[eosio::table("rtltokens")]] accepted_token_row {
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
    "rtltokens"_n,
    accepted_token_row,
    indexed_by<"bytokensym"_n, const_mem_fun<accepted_token_row, uint128_t, &accepted_token_row::bytokensym>>
>;

struct [[eosio::table("rtltariffs")]] tariff_row {
    uint64_t config_id;
    uint8_t mode;
    name token_contract;
    asset price_per_kib;
    bool active;
    time_point_sec updated_at;

    uint64_t primary_key() const { return config_id; }
    uint64_t bymode() const { return static_cast<uint64_t>(mode); }
    uint128_t bytokensym() const {
        return (static_cast<uint128_t>(token_contract.value) << 64) |
               price_per_kib.symbol.code().raw();
    }
};

using tariff_table = multi_index<
    "rtltariffs"_n,
    tariff_row,
    indexed_by<"bymode"_n, const_mem_fun<tariff_row, uint64_t, &tariff_row::bymode>>,
    indexed_by<"bytokensym"_n, const_mem_fun<tariff_row, uint128_t, &tariff_row::bytokensym>>
>;

struct [[eosio::table("rtlcounters")]] retail_counter_state {
    uint64_t next_token_id = 1;
    uint64_t next_tariff_id = 1;
};

using retail_counter_singleton = singleton<"rtlcounters"_n, retail_counter_state>;

}  // namespace verification_retail_payment_tables
