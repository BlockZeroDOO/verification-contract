#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <request_key.hpp>

#include <string>
#include <tuple>

using namespace eosio;
using std::string;

class [[eosio::contract("managementel")]] managementel : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void addwhuser(const name& account, const string& note);

    [[eosio::action]]
    void rmwhuser(const name& account);

    [[eosio::action]]
    void addnporg(const name& account, const string& note);

    [[eosio::action]]
    void rmnporg(const name& account);

    [[eosio::action]]
    void setpaytoken(
        const name& token_contract,
        const asset& retail_price,
        const asset& wholesale_price
    );

    [[eosio::action]]
    void rmpaytoken(const name& token_contract, const symbol& token_symbol);

    [[eosio::action]]
    void submitfree(
        const name& submitter,
        const string& object_hash,
        const string& hash_algorithm,
        const string& canonicalization_profile,
        const string& client_reference
    );

    [[eosio::action]]
    void setfreecfg(
        bool enabled,
        uint32_t daily_free_limit
    );

    [[eosio::action]]
    void withdraw(
        const name& token_contract,
        const name& to,
        const asset& quantity,
        const string& memo
    );

    asset quote(
        const name& account,
        const name& token_contract,
        const symbol& token_symbol
    ) const;

    bool iswhuser(const name& account) const;

    bool isnporg(const name& account) const;

    [[eosio::on_notify("*::transfer")]]
    void ontransfer(const name& from, const name& to, const asset& quantity, const string& memo);

private:
    struct [[eosio::table("wholesale")]] wholesale_user {
        name account;
        string note;
        time_point_sec added_at;

        uint64_t primary_key() const { return account.value; }
    };

    struct [[eosio::table("nonprofit")]] nonprofit_org {
        name account;
        string note;
        time_point_sec added_at;

        uint64_t primary_key() const { return account.value; }
    };

    struct [[eosio::table("paytokens")]] payment_token {
        uint64_t config_id;
        name token_contract;
        asset retail_price;
        asset wholesale_price;
        time_point_sec updated_at;

        uint64_t primary_key() const { return config_id; }
        uint128_t bytokensym() const {
            return (static_cast<uint128_t>(token_contract.value) << 64) |
                   wholesale_price.symbol.code().raw();
        }
    };

    struct pricing_decision {
        asset price;
        bool wholesale_pricing;
    };

    struct [[eosio::table("freepolicy")]] free_policy {
        bool enabled = false;
        time_point_sec window_start;
        uint32_t daily_free_limit = 0;
        uint32_t used_in_window = 0;
        time_point_sec updated_at;
    };

    struct [[eosio::table("freeusage")]] free_usage_row {
        name account;
        time_point_sec last_submit_at;
        uint64_t primary_key() const { return account.value; }
    };

    struct verification_proof_row {
        uint64_t proof_id;
        name writer;
        name submitter;
        checksum256 object_hash;
        string canonicalization_profile;
        string client_reference;
        time_point_sec submitted_at;

        uint64_t primary_key() const { return proof_id; }
        checksum256 by_request() const {
            return verification_common::compute_request_key(submitter, client_reference);
        }
    };

    using wholesale_table = multi_index<"wholesale"_n, wholesale_user>;
    using nonprofit_table = multi_index<"nonprofit"_n, nonprofit_org>;
    using payment_token_table = multi_index<
        "paytokens"_n,
        payment_token,
        indexed_by<"bytokensym"_n, const_mem_fun<payment_token, uint128_t, &payment_token::bytokensym>>
    >;
    using free_usage_table = multi_index<"freeusage"_n, free_usage_row>;
    using free_policy_singleton = singleton<"freepolicy"_n, free_policy>;
    using verification_proof_table = multi_index<
        "proofs"_n,
        verification_proof_row,
        indexed_by<"byrequest"_n, const_mem_fun<verification_proof_row, checksum256, &verification_proof_row::by_request>>
    >;

    static constexpr uint8_t hash_size = 32;
    static constexpr uint32_t seconds_per_day = 24 * 60 * 60;
    static constexpr uint32_t nonprofit_cooldown_sec = 60;
    static constexpr name verification_account = "verification"_n;

    free_policy get_free_policy() const;
    time_point_sec current_day_start(const time_point_sec& timestamp) const;
    uint128_t make_payment_key(const name& token_contract, const symbol_code& token_symbol) const;
    payment_token get_payment_token(const name& token_contract, const symbol_code& token_symbol) const;
    void consume_free_allowance(const name& submitter);
    pricing_decision resolve_pricing(const name& account, const name& token_contract, const symbol& token_symbol) const;
    pricing_decision resolve_paid_pricing(const name& account, const name& token_contract, const symbol& token_symbol) const;
    pricing_decision resolve_token_pricing(
        const name& token_contract,
        const symbol& token_symbol,
        bool wholesale_pricing
    ) const;
    asset resolve_price(const name& account, const name& token_contract, const symbol& token_symbol) const;
    checksum256 parse_hash(const string& hex) const;
    void validate_client_reference(const string& client_reference) const;
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
    void record_proof(
        const name& submitter,
        const checksum256& object_hash,
        const string& canonicalization_profile,
        const string& client_reference
    );
    void validate_text(const string& value, uint32_t max_length, const char* field_name, bool allow_empty) const;
};
