#pragma once

#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/time.hpp>

#include <request_key.hpp>

#include <string>

using namespace eosio;
using std::string;

class [[eosio::contract("verification")]] verification : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void record(
        const name& submitter,
        const checksum256& object_hash,
        const string& canonicalization_profile,
        const string& client_reference
    );

private:
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

    static constexpr name authorized_writer = "managementel"_n;

    void validate_client_reference(const string& client_reference) const;
    void validate_printable_ascii_text(
        const string& value,
        uint32_t max_length,
        const char* field_name,
        bool allow_empty
    ) const;
    void validate_text(const string& value, uint32_t max_length, const char* field_name, bool allow_empty) const;
};
