#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <request_key.hpp>
#include <verification_retail_payment_tables.hpp>
#include <verification_validators.hpp>

#include <string>
#include <tuple>

using namespace eosio;
using std::string;

class [[eosio::contract("verifretpay")]] verification_retail_payment : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void settoken(const name& token_contract, const symbol& token_symbol);

    [[eosio::action]]
    void rmtoken(const name& token_contract, const symbol_code& token_symbol);

    [[eosio::action]]
    void setprice(uint8_t mode, const name& token_contract, const asset& price);

    [[eosio::action]]
    void consume(uint64_t auth_id);

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
    using accepted_token_row = verification_retail_payment_tables::accepted_token_row;
    using accepted_token_table = verification_retail_payment_tables::accepted_token_table;
    using tariff_row = verification_retail_payment_tables::tariff_row;
    using tariff_table = verification_retail_payment_tables::tariff_table;
    using usage_auth_row = verification_retail_payment_tables::usage_auth_row;
    using usage_auth_table = verification_retail_payment_tables::usage_auth_table;
    using retail_counter_state = verification_retail_payment_tables::retail_counter_state;
    using retail_counter_singleton = verification_retail_payment_tables::retail_counter_singleton;

    static constexpr name verification_account = "verif"_n;
    static constexpr uint8_t retail_mode_single = 0;
    static constexpr uint8_t retail_mode_batch = 1;

    uint128_t make_payment_key(const name& token_contract, const symbol_code& token_symbol) const;
    accepted_token_row require_accepted_token(const name& token_contract, const symbol_code& token_symbol) const;
    tariff_row require_tariff(uint8_t mode, const name& token_contract, const symbol& token_symbol) const;
    uint64_t next_retail_token_id();
    uint64_t next_retail_tariff_id();
    uint64_t next_retail_auth_id();
    std::tuple<uint8_t, name, checksum256> parse_payment_memo(const string& memo) const;
};
