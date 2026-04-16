#include <verification_enterprise.hpp>

namespace {
bool is_zero_checksum(const eosio::checksum256& value) {
    return verification_validators::is_zero_checksum(value);
}
}  // namespace

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
    bool active
) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");
    verification_validators::validate_policy_settings(allow_single, allow_batch, active);

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    const auto now = time_point_sec(current_time_point());
    if (existing == policies.end()) {
        policies.emplace(get_self(), [&](auto& row) {
            row.id = id;
            row.allow_single = allow_single;
            row.allow_batch = allow_batch;
            row.active = active;
            row.created_at = now;
            row.updated_at = now;
        });
        return;
    }

    policies.modify(existing, get_self(), [&](auto& row) {
        row.allow_single = allow_single;
        row.allow_batch = allow_batch;
        row.active = active;
        row.updated_at = now;
    });
}

void verification_enterprise::setauthsrcs(const name& billing_account, const name& retail_payment_account) {
    require_auth(get_self());
    check(is_account(billing_account), "billing_account does not exist");
    check(is_account(retail_payment_account), "retail_payment_account does not exist");
    check(billing_account != retail_payment_account, "billing_account and retail_payment_account must differ");

    auth_source_singleton auth_sources(get_self(), get_self().value);
    auth_sources.set(auth_source_config{billing_account, retail_payment_account}, get_self());
}

void verification_enterprise::submit(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& object_hash,
    const checksum256& external_ref,
    uint64_t billable_bytes
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    verification_validators::validate_nonzero_checksum(object_hash, "object_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");
    verification_validators::validate_billable_bytes(billable_bytes, "billable_bytes");
    const auto billable_kib = verification_validators::derive_billable_kib(billable_bytes);

    const auto schema = require_schema(schema_id);
    check(schema.active, "schema is inactive");

    const auto policy = require_policy(policy_id);
    check(policy.active, "policy is inactive");
    check(policy.allow_single, "policy does not allow single submissions");

    const auto usage_auth = require_usage_authorization(
        enterprise_mode_single,
        submitter,
        external_ref,
        billable_bytes,
        billable_kib
    );
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
        row.billable_bytes = billable_bytes;
        row.billable_kib = billable_kib;
        row.external_ref = external_ref;
        row.request_key = request_key;
        row.block_num = static_cast<uint32_t>(eosio::tapos_block_num());
        row.created_at = now;
    });

    consume_usage_authorization(usage_auth);
}

void verification_enterprise::submitroot(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& root_hash,
    uint32_t leaf_count,
    const checksum256& manifest_hash,
    const checksum256& external_ref,
    uint64_t billable_bytes
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    check(leaf_count > 0, "leaf_count must be greater than zero");
    verification_validators::validate_nonzero_checksum(root_hash, "root_hash");
    verification_validators::validate_nonzero_checksum(manifest_hash, "manifest_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");
    verification_validators::validate_billable_bytes(billable_bytes, "billable_bytes");
    const auto billable_kib = verification_validators::derive_billable_kib(billable_bytes);

    const auto schema = require_schema(schema_id);
    check(schema.active, "schema is inactive");

    const auto policy = require_policy(policy_id);
    check(policy.active, "policy is inactive");
    check(policy.allow_batch, "policy does not allow batch submissions");

    const auto usage_auth = require_usage_authorization(
        enterprise_mode_batch,
        submitter,
        external_ref,
        billable_bytes,
        billable_kib
    );
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
        row.manifest_hash = manifest_hash;
        row.billable_bytes = billable_bytes;
        row.billable_kib = billable_kib;
        row.external_ref = external_ref;
        row.request_key = request_key;
        row.block_num = static_cast<uint32_t>(eosio::tapos_block_num());
        row.created_at = now;
    });

    consume_usage_authorization(usage_auth);
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

verification_enterprise::schema_row verification_enterprise::require_schema(uint64_t id) const {
    return verification_core::require_schema(get_self(), id);
}

verification_enterprise::policy_row verification_enterprise::require_policy(uint64_t id) const {
    return verification_core::require_policy(get_self(), id);
}

verification_enterprise::auth_source_config verification_enterprise::get_auth_source_config() const {
    auth_source_singleton auth_sources(get_self(), get_self().value);
    return auth_sources.exists() ? auth_sources.get() : auth_source_config{};
}

verification_enterprise::usage_authorization_ref verification_enterprise::require_usage_authorization(
    uint8_t mode,
    const name& submitter,
    const checksum256& external_ref,
    uint64_t billable_bytes,
    uint64_t billable_kib
) const {
    const auto auth_sources = get_auth_source_config();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    const auto now = time_point_sec(current_time_point());

    bool has_enterprise_auth = false;
    bool has_retail_auth = false;
    uint64_t auth_id = 0;
    name source_contract = name{};

    {
        enterprise_usage_auth_table usage_auths(auth_sources.billing_account, auth_sources.billing_account.value);
        auto by_request = usage_auths.get_index<"byrequest"_n>();
        auto existing = by_request.find(request_key);
        if (existing != by_request.end() &&
            !existing->consumed &&
            existing->submitter == submitter &&
            existing->mode == mode &&
            existing->billable_bytes == billable_bytes &&
            existing->billable_kib == billable_kib &&
            existing->expires_at > now) {
            has_enterprise_auth = true;
            auth_id = existing->auth_id;
            source_contract = auth_sources.billing_account;
        }
    }

    {
        retail_usage_auth_table usage_auths(auth_sources.retail_payment_account, auth_sources.retail_payment_account.value);
        auto by_request = usage_auths.get_index<"byrequest"_n>();
        auto existing = by_request.find(request_key);
        if (existing != by_request.end() &&
            !existing->consumed &&
            existing->submitter == submitter &&
            existing->mode == mode &&
            existing->external_ref == external_ref &&
            existing->billable_bytes == billable_bytes &&
            existing->billable_kib == billable_kib) {
            has_retail_auth = true;
            auth_id = existing->auth_id;
            source_contract = auth_sources.retail_payment_account;
        }
    }

    check(
        has_enterprise_auth || has_retail_auth,
        "usage authorization is missing for request"
    );
    check(
        !(has_enterprise_auth && has_retail_auth),
        "multiple usage authorizations exist for request"
    );

    return usage_authorization_ref{source_contract, auth_id};
}

void verification_enterprise::consume_usage_authorization(const usage_authorization_ref& authorization) const {
    action(
        permission_level{get_self(), "active"_n},
        authorization.source_contract,
        "consume"_n,
        std::make_tuple(authorization.auth_id)
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

void verification_enterprise::validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const {
    verification_core::validate_commitment_request_unique(get_self(), submitter, external_ref);
}
