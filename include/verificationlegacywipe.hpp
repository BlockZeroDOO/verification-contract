#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/time.hpp>

#include <string>

using namespace eosio;
using std::string;

class [[eosio::contract("verificationlegacywipe")]] verificationlegacywipe : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void wipeall(uint32_t max_rows);

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
        asset storage_price;
        time_point_sec updated_at;

        uint64_t primary_key() const { return config_id; }
    };

    struct [[eosio::table("proofs")]] proof_row {
        uint64_t proof_id;
        name submitter;
        checksum256 object_hash;
        string canonicalization_profile;
        string client_reference;
        name payment_token_contract;
        asset price_charged;
        bool wholesale_pricing;
        time_point_sec submitted_at;

        uint64_t primary_key() const { return proof_id; }
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

    using wholesale_table = multi_index<"wholesale"_n, wholesale_user>;
    using nonprofit_table = multi_index<"nonprofit"_n, nonprofit_org>;
    using payment_token_table = multi_index<"paytokens"_n, payment_token>;
    using proof_table = multi_index<"proofs"_n, proof_row>;
    using free_usage_table = multi_index<"freeusage"_n, free_usage_row>;
    using free_policy_singleton = singleton<"freepolicy"_n, free_policy>;

    template <typename Table>
    uint32_t erase_rows(Table& table, uint32_t remaining);
};
