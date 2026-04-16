#include <verification_enterprise.hpp>

namespace {
bool is_zero_checksum(const eosio::checksum256& value) {
    return verification_validators::is_zero_checksum(value);
}
}  // namespace

void verification_enterprise::issuekyc(
    const name& account,
    uint8_t level,
    const string& provider,
    const string& jurisdiction,
    const time_point_sec& expires_at
) {
    require_auth(get_self());
    check(is_account(account), "account does not exist");
    verification_validators::validate_printable_ascii_text(provider, 64, "provider", false);
    verification_validators::validate_printable_ascii_text(jurisdiction, 32, "jurisdiction", false);
    verification_validators::validate_future_time(expires_at, "expires_at");

    kyc_table kyc_records(get_self(), get_self().value);
    check(kyc_records.find(account.value) == kyc_records.end(), "kyc record already exists");

    const auto now = time_point_sec(current_time_point());
    kyc_records.emplace(get_self(), [&](auto& row) {
        row.account = account;
        row.level = level;
        row.provider = provider;
        row.jurisdiction = jurisdiction;
        row.active = true;
        row.issued_at = now;
        row.expires_at = expires_at;
    });
}

void verification_enterprise::renewkyc(const name& account, const time_point_sec& expires_at) {
    require_auth(get_self());
    verification_validators::validate_future_time(expires_at, "expires_at");

    kyc_table kyc_records(get_self(), get_self().value);
    auto existing = kyc_records.find(account.value);
    check(existing != kyc_records.end(), "kyc record does not exist");

    const auto now = time_point_sec(current_time_point());
    kyc_records.modify(existing, get_self(), [&](auto& row) {
        row.active = true;
        row.issued_at = now;
        row.expires_at = expires_at;
    });
}

void verification_enterprise::revokekyc(const name& account) {
    require_auth(get_self());

    kyc_table kyc_records(get_self(), get_self().value);
    auto existing = kyc_records.find(account.value);
    check(existing != kyc_records.end(), "kyc record does not exist");

    const auto now = time_point_sec(current_time_point());
    kyc_records.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
        row.expires_at = now;
    });
}

void verification_enterprise::suspendkyc(const name& account) {
    require_auth(get_self());

    kyc_table kyc_records(get_self(), get_self().value);
    auto existing = kyc_records.find(account.value);
    check(existing != kyc_records.end(), "kyc record does not exist");
    check(existing->active, "kyc record is already inactive");

    kyc_records.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
    });
}

void verification_enterprise::addschema(
    uint64_t id,
    const string& version,
    const checksum256& canonicalization_hash,
    const checksum256& hash_policy
) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");
    verification_validators::validate_printable_ascii_text(version, 32, "version", false);

    schema_table schemas(get_self(), get_self().value);
    check(schemas.find(id) == schemas.end(), "schema already exists");

    const auto now = time_point_sec(current_time_point());
    schemas.emplace(get_self(), [&](auto& row) {
        row.id = id;
        row.version = version;
        row.canonicalization_hash = canonicalization_hash;
        row.hash_policy = hash_policy;
        row.active = true;
        row.created_at = now;
        row.updated_at = now;
    });
}

void verification_enterprise::updateschema(
    uint64_t id,
    const string& version,
    const checksum256& canonicalization_hash,
    const checksum256& hash_policy
) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");
    verification_validators::validate_printable_ascii_text(version, 32, "version", false);

    schema_table schemas(get_self(), get_self().value);
    auto existing = schemas.find(id);
    check(existing != schemas.end(), "schema does not exist");
    check(existing->active, "schema is inactive");

    schemas.modify(existing, get_self(), [&](auto& row) {
        row.version = version;
        row.canonicalization_hash = canonicalization_hash;
        row.hash_policy = hash_policy;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::deprecate(uint64_t id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");

    schema_table schemas(get_self(), get_self().value);
    auto existing = schemas.find(id);
    check(existing != schemas.end(), "schema does not exist");
    check(existing->active, "schema is already inactive");

    schemas.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::setpolicy(
    uint64_t id,
    bool allow_single,
    bool allow_batch,
    bool require_kyc,
    uint8_t min_kyc_level,
    bool active
) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    const bool allow_zk = existing == policies.end() ? false : existing->allow_zk;
    verification_validators::validate_policy_settings(
        allow_single, allow_batch, require_kyc, min_kyc_level, allow_zk, active
    );

    const auto now = time_point_sec(current_time_point());
    if (existing == policies.end()) {
        policies.emplace(get_self(), [&](auto& row) {
            row.id = id;
            row.allow_single = allow_single;
            row.allow_batch = allow_batch;
            row.require_kyc = require_kyc;
            row.min_kyc_level = min_kyc_level;
            row.allow_zk = false;
            row.active = active;
            row.created_at = now;
            row.updated_at = now;
        });
        return;
    }

    policies.modify(existing, get_self(), [&](auto& row) {
        row.allow_single = allow_single;
        row.allow_batch = allow_batch;
        row.require_kyc = require_kyc;
        row.min_kyc_level = min_kyc_level;
        row.active = active;
        row.updated_at = now;
    });
}

void verification_enterprise::enablezk(uint64_t id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    check(existing != policies.end(), "policy does not exist");
    check(existing->active, "policy is inactive");
    verification_validators::validate_policy_settings(
        existing->allow_single,
        existing->allow_batch,
        existing->require_kyc,
        existing->min_kyc_level,
        true,
        existing->active
    );

    policies.modify(existing, get_self(), [&](auto& row) {
        row.allow_zk = true;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::disablezk(uint64_t id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    check(existing != policies.end(), "policy does not exist");

    policies.modify(existing, get_self(), [&](auto& row) {
        row.allow_zk = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::submit(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& object_hash,
    const checksum256& external_ref
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    verification_validators::validate_nonzero_checksum(object_hash, "object_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");

    const auto schema = require_schema(schema_id);
    check(schema.active, "schema is inactive");

    const auto policy = require_policy(policy_id);
    check(policy.active, "policy is inactive");
    check(policy.allow_single, "policy does not allow single submissions");

    if (policy.require_kyc) {
        const auto kyc = require_kyc_record(submitter);
        check(kyc.active, "kyc record is inactive");
        check(kyc.expires_at > time_point_sec(current_time_point()), "kyc record is expired");
        check(kyc.level >= policy.min_kyc_level, "kyc level is below policy minimum");
    }

    const auto usage_auth = require_usage_authorization(enterprise_mode_single, submitter, external_ref);
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    validate_commitment_request_unique(submitter, external_ref);

    commitment_table commitments(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());
    const auto commitment_id = next_commitment_id();
    commitments.emplace(get_self(), [&](auto& row) {
        row.id = commitment_id;
        row.submitter = submitter;
        row.schema_id = schema_id;
        row.policy_id = policy_id;
        row.object_hash = object_hash;
        row.external_ref = external_ref;
        row.request_key = request_key;
        row.block_num = static_cast<uint32_t>(eosio::tapos_block_num());
        row.created_at = now;
        row.status_changed_at = now;
        row.status = verification_core::commitment_status_active;
        row.superseded_by = 0;
    });

    consume_usage_authorization(usage_auth.auth_id);
}

void verification_enterprise::supersede(uint64_t id, uint64_t successor_id) {
    verification_validators::validate_registry_id(id, "id");
    verification_validators::validate_registry_id(successor_id, "successor_id");
    check(id != successor_id, "successor_id must be different from id");

    commitment_table commitments(get_self(), get_self().value);
    auto existing = commitments.find(id);
    check(existing != commitments.end(), "commitment does not exist");
    check(
        has_auth(existing->submitter) || has_auth(get_self()),
        "missing required authority of submitter or contract"
    );
    validate_commitment_is_active(*existing);

    auto successor = commitments.find(successor_id);
    check(successor != commitments.end(), "successor commitment does not exist");
    validate_commitment_can_be_successor(*existing, *successor);

    commitments.modify(existing, get_self(), [&](auto& row) {
        row.status = verification_core::commitment_status_superseded;
        row.status_changed_at = time_point_sec(current_time_point());
        row.superseded_by = successor_id;
    });
}

void verification_enterprise::revokecmmt(uint64_t id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");

    commitment_table commitments(get_self(), get_self().value);
    auto existing = commitments.find(id);
    check(existing != commitments.end(), "commitment does not exist");
    validate_commitment_is_active(*existing);

    commitments.modify(existing, get_self(), [&](auto& row) {
        row.status = verification_core::commitment_status_revoked;
        row.status_changed_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::expirecmmt(uint64_t id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");

    commitment_table commitments(get_self(), get_self().value);
    auto existing = commitments.find(id);
    check(existing != commitments.end(), "commitment does not exist");
    validate_commitment_is_active(*existing);

    commitments.modify(existing, get_self(), [&](auto& row) {
        row.status = verification_core::commitment_status_expired;
        row.status_changed_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::submitroot(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& root_hash,
    uint32_t leaf_count,
    const checksum256& external_ref
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    check(leaf_count > 0, "leaf_count must be greater than zero");
    verification_validators::validate_nonzero_checksum(root_hash, "root_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");

    const auto schema = require_schema(schema_id);
    check(schema.active, "schema is inactive");

    const auto policy = require_policy(policy_id);
    check(policy.active, "policy is inactive");
    check(policy.allow_batch, "policy does not allow batch submissions");

    if (policy.require_kyc) {
        const auto kyc = require_kyc_record(submitter);
        check(kyc.active, "kyc record is inactive");
        check(kyc.expires_at > time_point_sec(current_time_point()), "kyc record is expired");
        check(kyc.level >= policy.min_kyc_level, "kyc level is below policy minimum");
    }

    const auto usage_auth = require_usage_authorization(enterprise_mode_batch, submitter, external_ref);
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    validate_batch_request_unique(submitter, external_ref);

    batch_table batches(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());
    const auto batch_id = next_batch_id();
    batches.emplace(get_self(), [&](auto& row) {
        row.id = batch_id;
        row.submitter = submitter;
        row.root_hash = root_hash;
        row.leaf_count = leaf_count;
        row.schema_id = schema_id;
        row.policy_id = policy_id;
        row.manifest_hash = checksum256{};
        row.external_ref = external_ref;
        row.request_key = request_key;
        row.block_num = static_cast<uint32_t>(eosio::tapos_block_num());
        row.created_at = now;
        row.manifest_linked_at = time_point_sec{};
        row.status_changed_at = now;
        row.status = verification_core::batch_status_open;
    });

    consume_usage_authorization(usage_auth.auth_id);
}

void verification_enterprise::linkmanifest(uint64_t id, const checksum256& manifest_hash) {
    verification_validators::validate_registry_id(id, "id");
    verification_validators::validate_nonzero_checksum(manifest_hash, "manifest_hash");

    batch_table batches(get_self(), get_self().value);
    auto existing = batches.find(id);
    check(existing != batches.end(), "batch does not exist");
    check(
        has_auth(existing->submitter) || has_auth(get_self()),
        "missing required authority of submitter or contract"
    );
    validate_batch_is_open(*existing);
    check(is_zero_checksum(existing->manifest_hash), "manifest is already linked");

    batches.modify(existing, get_self(), [&](auto& row) {
        row.manifest_hash = manifest_hash;
        row.manifest_linked_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::closebatch(uint64_t id) {
    verification_validators::validate_registry_id(id, "id");

    batch_table batches(get_self(), get_self().value);
    auto existing = batches.find(id);
    check(existing != batches.end(), "batch does not exist");
    check(
        has_auth(existing->submitter) || has_auth(get_self()),
        "missing required authority of submitter or contract"
    );
    validate_batch_is_open(*existing);
    check(!is_zero_checksum(existing->manifest_hash), "manifest is not linked");

    batches.modify(existing, get_self(), [&](auto& row) {
        row.status = verification_core::batch_status_closed;
        row.status_changed_at = time_point_sec(current_time_point());
    });
}

void verification_enterprise::withdraw(
    const name& token_contract,
    const name& to,
    const asset& quantity,
    const string& memo
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    check(is_account(to), "to account does not exist");
    verification_validators::validate_nonnegative_asset(quantity, "quantity");
    check(quantity.amount > 0, "quantity must be positive");
    verification_validators::validate_text(memo, 128, "memo", true);

    action(
        permission_level{get_self(), "active"_n},
        token_contract,
        "transfer"_n,
        std::make_tuple(get_self(), to, quantity, memo)
    ).send();
}

verification_enterprise::kyc_row verification_enterprise::require_kyc_record(const name& account) const {
    return verification_core::require_kyc_record(get_self(), account);
}

verification_enterprise::schema_row verification_enterprise::require_schema(uint64_t id) const {
    return verification_core::require_schema(get_self(), id);
}

verification_enterprise::policy_row verification_enterprise::require_policy(uint64_t id) const {
    return verification_core::require_policy(get_self(), id);
}

verification_enterprise::usage_auth_row verification_enterprise::require_usage_authorization(
    uint8_t mode,
    const name& submitter,
    const checksum256& external_ref
) const {
    usage_auth_table usage_auths(billing_account, billing_account.value);
    auto by_request = usage_auths.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    auto existing = by_request.find(request_key);
    check(existing != by_request.end(), "enterprise usage authorization is missing");
    check(!existing->consumed, "enterprise usage authorization is already consumed");
    check(existing->submitter == submitter, "enterprise usage authorization submitter does not match request");
    check(existing->mode == mode, "enterprise usage authorization mode does not match request");
    check(existing->expires_at > time_point_sec(current_time_point()), "enterprise usage authorization is expired");
    return *existing;
}

void verification_enterprise::consume_usage_authorization(uint64_t auth_id) const {
    action(
        permission_level{get_self(), "active"_n},
        billing_account,
        "consume"_n,
        std::make_tuple(auth_id)
    ).send();
}

uint64_t verification_enterprise::next_batch_id() {
    return verification_core::next_batch_id(get_self());
}

uint64_t verification_enterprise::next_commitment_id() {
    return verification_core::next_commitment_id(get_self());
}

void verification_enterprise::validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const {
    verification_core::validate_batch_request_unique(get_self(), submitter, external_ref);
}

void verification_enterprise::validate_batch_is_open(const batch_row& batch) const {
    verification_core::validate_batch_is_open(batch);
}

void verification_enterprise::validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const {
    verification_core::validate_commitment_request_unique(get_self(), submitter, external_ref);
}

void verification_enterprise::validate_commitment_can_be_successor(
    const commitment_row& current,
    const commitment_row& successor
) const {
    verification_core::validate_commitment_can_be_successor(current, successor);
}

void verification_enterprise::validate_commitment_is_active(const commitment_row& commitment) const {
    verification_core::validate_commitment_is_active(commitment);
}
