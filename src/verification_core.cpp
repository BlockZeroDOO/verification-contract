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
using verification_tables::policy_row;
using verification_tables::policy_table;
using verification_tables::schema_row;
using verification_tables::schema_table;

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

void validate_batch_request_unique(const name& self, const name& submitter, const checksum256& external_ref) {
    batch_table batches(self, self.value);
    auto by_request = batches.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    check(by_request.find(request_key) == by_request.end(), "duplicate batch request for submitter");
}

void validate_commitment_request_unique(const name& self, const name& submitter, const checksum256& external_ref) {
    commitment_table commitments(self, self.value);
    auto by_request = commitments.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    check(by_request.find(request_key) == by_request.end(), "duplicate request for submitter");
}

}  // namespace verification_core
