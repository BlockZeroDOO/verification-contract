#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/eosio.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <string>
#include <tuple>
#include <vector>

using namespace eosio;
using std::string;

class [[eosio::contract("gfnotary")]] gfnotary : public contract {
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
    void submitfree(
        const name& submitter,
        const string& object_hash,
        const string& hash_algorithm,
        const string& canonicalization_profile,
        const string& client_reference
    );

    [[eosio::action]]
    void withdraw(const name& to, const asset& quantity, const string& memo);

    [[eosio::action, eosio::read_only]]
    asset quote(const name& account) const;

    [[eosio::action, eosio::read_only]]
    bool iswhuser(const name& account) const;

    [[eosio::action, eosio::read_only]]
    bool isnporg(const name& account) const;

    [[eosio::on_notify("eosio.token::transfer")]]
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

    struct [[eosio::table("proofs")]] proof_row {
        uint64_t proof_id;
        name submitter;
        string object_hash;
        string hash_algorithm;
        string canonicalization_profile;
        string client_reference;
        asset price_charged;
        bool wholesale_pricing;
        time_point_sec submitted_at;

        uint64_t primary_key() const { return proof_id; }
        uint64_t by_submitter() const { return submitter.value; }
    };

    using wholesale_table = multi_index<"wholesale"_n, wholesale_user>;
    using nonprofit_table = multi_index<"nonprofit"_n, nonprofit_org>;
    using proof_table = multi_index<
        "proofs"_n,
        proof_row,
        indexed_by<"bysubmitter"_n, const_mem_fun<proof_row, uint64_t, &proof_row::by_submitter>>
    >;

    static constexpr uint8_t hash_size = 32;

    symbol gft_symbol() const;
    name token_contract() const;
    asset nonprofit_price() const;
    asset retail_price() const;
    asset wholesale_price() const;
    asset resolve_price(const name& account) const;
    void validate_hash(const string& hex) const;
    std::vector<string> split_memo(const string& memo, char delimiter) const;
    uint8_t from_hex(char c) const;
    void store_proof(
        const name& submitter,
        const string& object_hash,
        const string& hash_algorithm,
        const string& canonicalization_profile,
        const string& client_reference,
        const asset& price
    );
    void validate_text(const string& value, uint32_t max_length, const char* field_name, bool allow_empty) const;
};
