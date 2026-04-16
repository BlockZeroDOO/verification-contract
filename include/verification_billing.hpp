#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <request_key.hpp>
#include <verification_billing_tables.hpp>
#include <verification_validators.hpp>

#include <string>
#include <tuple>

using namespace eosio;
using std::string;

class [[eosio::contract("verifbill")]] verification_billing : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void settoken(const name& token_contract, const symbol& token_symbol);

    [[eosio::action]]
    void rmtoken(const name& token_contract, const symbol_code& token_symbol);

    [[eosio::action]]
    void setplan(
        const name& plan_code,
        const name& token_contract,
        const asset& price,
        uint32_t duration_sec,
        uint64_t single_quota,
        uint64_t batch_quota,
        bool active
    );

    [[eosio::action]]
    void deactplan(uint64_t plan_id);

    [[eosio::action]]
    void setpack(
        const name& pack_code,
        const name& token_contract,
        const asset& price,
        uint64_t single_units,
        uint64_t batch_units,
        bool active
    );

    [[eosio::action]]
    void deactpack(uint64_t pack_id);

    [[eosio::action]]
    void setverifacct(const name& verification_account);

    [[eosio::action]]
    void use(const name& payer, const name& submitter, uint8_t mode, const checksum256& external_ref);

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
    using accepted_token_row = verification_billing_tables::accepted_token_row;
    using accepted_token_table = verification_billing_tables::accepted_token_table;
    using plan_row = verification_billing_tables::plan_row;
    using plan_table = verification_billing_tables::plan_table;
    using pack_row = verification_billing_tables::pack_row;
    using pack_table = verification_billing_tables::pack_table;
    using entitlement_row = verification_billing_tables::entitlement_row;
    using entitlement_table = verification_billing_tables::entitlement_table;
    using usage_auth_row = verification_billing_tables::usage_auth_row;
    using usage_auth_table = verification_billing_tables::usage_auth_table;
    using counter_state = verification_billing_tables::counter_state;
    using counter_singleton = verification_billing_tables::counter_singleton;

    struct [[eosio::table("billconfig")]] billing_config {
        name verification_account = "verif"_n;
    };

    using billing_config_singleton = singleton<"billconfig"_n, billing_config>;

    static constexpr uint8_t entitlement_kind_plan = 0;
    static constexpr uint8_t entitlement_kind_pack = 1;
    static constexpr uint8_t entitlement_status_active = 0;
    static constexpr uint8_t entitlement_status_exhausted = 1;
    static constexpr uint8_t entitlement_status_expired = 2;
    static constexpr uint8_t enterprise_mode_single = 0;
    static constexpr uint8_t enterprise_mode_batch = 1;
    static constexpr uint32_t usage_auth_ttl_sec = 600;

    uint128_t make_payment_key(const name& token_contract, const symbol_code& token_symbol) const;
    accepted_token_row require_accepted_token(const name& token_contract, const symbol_code& token_symbol) const;
    plan_row require_plan_by_id(uint64_t plan_id) const;
    pack_row require_pack_by_id(uint64_t pack_id) const;
    uint64_t next_token_id();
    uint64_t next_plan_id();
    uint64_t next_pack_id();
    uint64_t next_entitlement_id();
    uint64_t next_usageauth_id();
    billing_config get_billing_config() const;
    std::tuple<string, name, name> parse_purchase_memo(const string& memo) const;
    entitlement_row allocate_usage(const name& payer, uint8_t mode);
};
