#if defined(VERIFICATION_RETAIL_BUILD)
#include <verification_retail.hpp>
#elif defined(VERIFICATION_ENTERPRISE_BUILD)
#include <verification_enterprise.hpp>
#else
#include <verification_core.hpp>
#endif

#include <eosio/system.hpp>

namespace verification_core {

using namespace eosio;
using verification_tables::batch_row;
using verification_tables::batch_table;
using verification_tables::commitment_row;
using verification_tables::commitment_table;
using verification_tables::counter_singleton;
using verification_tables::counter_state;
using verification_tables::kyc_row;
using verification_tables::kyc_table;
using verification_tables::payment_token;
using verification_tables::payment_token_table;
using verification_tables::policy_row;
using verification_tables::policy_table;
using verification_tables::proof_table;
using verification_tables::schema_row;
using verification_tables::schema_table;

uint128_t make_payment_key(const name& token_contract, const symbol_code& token_symbol) {
    return (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.raw();
}

payment_token get_payment_token(const name& self, const name& token_contract, const symbol_code& token_symbol) {
    payment_token_table payment_tokens(self, self.value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "payment token is not configured");
    return *existing;
}

kyc_row require_kyc_record(const name& self, const name& account) {
    kyc_table kyc_records(self, self.value);
    auto existing = kyc_records.find(account.value);
    check(existing != kyc_records.end(), "kyc record does not exist");
    return *existing;
}

schema_row require_schema(const name& self, uint64_t id) {
    verification_validators::validate_registry_id(id, "id");

    schema_table schemas(self, self.value);
    auto existing = schemas.find(id);
    check(existing != schemas.end(), "schema does not exist");
    return *existing;
}

policy_row require_policy(const name& self, uint64_t id) {
    verification_validators::validate_registry_id(id, "id");

    policy_table policies(self, self.value);
    auto existing = policies.find(id);
    check(existing != policies.end(), "policy does not exist");
    return *existing;
}

uint64_t next_batch_id(const name& self) {
    counter_singleton counters(self, self.value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    if (state.next_batch_id == 0) {
        state.next_batch_id = 1;
    }

    const uint64_t allocated = state.next_batch_id;
    ++state.next_batch_id;
    counters.set(state, self);

    return allocated;
}

uint64_t next_commitment_id(const name& self) {
    counter_singleton counters(self, self.value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    if (state.next_commitment_id == 0) {
        state.next_commitment_id = 1;
    }

    const uint64_t allocated = state.next_commitment_id;
    ++state.next_commitment_id;
    counters.set(state, self);

    return allocated;
}

asset resolve_price(const name& self, const name& token_contract, const symbol& token_symbol) {
    check(is_account(token_contract), "token_contract does not exist");
    check(token_symbol.is_valid(), "token_symbol is invalid");

    const auto configured = get_payment_token(self, token_contract, token_symbol.code());
    check(
        configured.price.symbol == token_symbol,
        "token_symbol precision does not match configured payment token"
    );

    return configured.price;
}

void validate_batch_request_unique(const name& self, const name& submitter, const checksum256& external_ref) {
    batch_table batches(self, self.value);
    auto by_request = batches.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    check(by_request.find(request_key) == by_request.end(), "duplicate batch request for submitter");
}

void validate_batch_is_open(const batch_row& batch) {
    check(batch.status == batch_status_open, "batch is not open");
}

void validate_commitment_request_unique(const name& self, const name& submitter, const checksum256& external_ref) {
    commitment_table commitments(self, self.value);
    auto by_request = commitments.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    check(by_request.find(request_key) == by_request.end(), "duplicate request for submitter");
}

void validate_commitment_can_be_successor(const commitment_row& current, const commitment_row& successor) {
    validate_commitment_is_active(successor);
    check(successor.submitter == current.submitter, "successor must have the same submitter");
    check(successor.schema_id == current.schema_id, "successor must have the same schema_id");
    check(successor.policy_id == current.policy_id, "successor must have the same policy_id");
    check(successor.created_at >= current.created_at, "successor must not predate current commitment");
}

void validate_commitment_is_active(const commitment_row& commitment) {
    check(commitment.status == commitment_status_active, "commitment is not active");
}

void validate_new_request(const name& self, const name& submitter, const std::string& client_reference) {
    proof_table proofs(self, self.value);
    auto by_request = proofs.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, client_reference);
    check(by_request.find(request_key) == by_request.end(), "duplicate client_reference for submitter");
}

void store_proof(
    const name& self,
    const name& submitter,
    const checksum256& object_hash,
    const std::string& canonicalization_profile,
    const std::string& client_reference
) {
    proof_table proofs(self, self.value);
    uint64_t next_id = static_cast<uint64_t>(current_time_point().sec_since_epoch());
    while (proofs.find(next_id) != proofs.end()) {
        ++next_id;
    }

    proofs.emplace(self, [&](auto& row) {
        row.proof_id = next_id;
        row.writer = self;
        row.submitter = submitter;
        row.object_hash = object_hash;
        row.canonicalization_profile = canonicalization_profile;
        row.client_reference = client_reference;
        row.submitted_at = time_point_sec(current_time_point());
    });
}

}  // namespace verification_core
