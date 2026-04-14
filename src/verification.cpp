#include <verification.hpp>

#include <eosio/dispatcher.hpp>

#include <array>

namespace {
struct token_stat_row {
    asset supply;
    asset max_supply;
    name issuer;

    uint64_t primary_key() const { return supply.symbol.code().raw(); }
};

using token_stat_table = eosio::multi_index<"stat"_n, token_stat_row>;

void validate_token_contract_stat(const eosio::name& token_contract, const eosio::symbol& token_symbol) {
    token_stat_table token_stats(token_contract, token_symbol.code().raw());
    auto token_stat = token_stats.find(token_symbol.code().raw());
    eosio::check(token_stat != token_stats.end(), "token symbol is not available in token contract stat table");
    eosio::check(
        token_stat->supply.symbol == token_symbol,
        "token symbol precision does not match token contract stat"
    );
}

bool is_zero_checksum(const eosio::checksum256& value) {
    const auto bytes = value.extract_as_byte_array();
    for (auto byte : bytes) {
        if (byte != 0) {
            return false;
        }
    }
    return true;
}
}  // namespace

void verification::issuekyc(
    const name& account,
    uint8_t level,
    const string& provider,
    const string& jurisdiction,
    const time_point_sec& expires_at
) {
    require_auth(get_self());
    check(is_account(account), "account does not exist");
    validate_printable_ascii_text(provider, 64, "provider", false);
    validate_printable_ascii_text(jurisdiction, 32, "jurisdiction", false);
    validate_future_time(expires_at, "expires_at");

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

void verification::renewkyc(const name& account, const time_point_sec& expires_at) {
    require_auth(get_self());
    validate_future_time(expires_at, "expires_at");

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

void verification::revokekyc(const name& account) {
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

void verification::suspendkyc(const name& account) {
    require_auth(get_self());

    kyc_table kyc_records(get_self(), get_self().value);
    auto existing = kyc_records.find(account.value);
    check(existing != kyc_records.end(), "kyc record does not exist");
    check(existing->active, "kyc record is already inactive");

    kyc_records.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
    });
}

void verification::addschema(
    uint64_t id,
    const string& version,
    const checksum256& canonicalization_hash,
    const checksum256& hash_policy
) {
    require_auth(get_self());
    validate_registry_id(id, "id");
    validate_printable_ascii_text(version, 32, "version", false);

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

void verification::updateschema(
    uint64_t id,
    const string& version,
    const checksum256& canonicalization_hash,
    const checksum256& hash_policy
) {
    require_auth(get_self());
    validate_registry_id(id, "id");
    validate_printable_ascii_text(version, 32, "version", false);

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

void verification::deprecate(uint64_t id) {
    require_auth(get_self());
    validate_registry_id(id, "id");

    schema_table schemas(get_self(), get_self().value);
    auto existing = schemas.find(id);
    check(existing != schemas.end(), "schema does not exist");
    check(existing->active, "schema is already inactive");

    schemas.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification::setpolicy(
    uint64_t id,
    bool allow_single,
    bool allow_batch,
    bool require_kyc,
    uint8_t min_kyc_level,
    bool active
) {
    require_auth(get_self());
    validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    const bool allow_zk = existing == policies.end() ? false : existing->allow_zk;
    validate_policy_settings(allow_single, allow_batch, require_kyc, min_kyc_level, allow_zk, active);

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

void verification::enablezk(uint64_t id) {
    require_auth(get_self());
    validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    check(existing != policies.end(), "policy does not exist");
    check(existing->active, "policy is inactive");
    validate_policy_settings(
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

void verification::disablezk(uint64_t id) {
    require_auth(get_self());
    validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    check(existing != policies.end(), "policy does not exist");

    policies.modify(existing, get_self(), [&](auto& row) {
        row.allow_zk = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification::submit(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& object_hash,
    const checksum256& external_ref
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    validate_nonzero_checksum(external_ref, "external_ref");

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
        row.status = commitment_status_active;
        row.superseded_by = 0;
    });
}

void verification::supersede(uint64_t id, uint64_t successor_id) {
    validate_registry_id(id, "id");
    validate_registry_id(successor_id, "successor_id");
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
        row.status = commitment_status_superseded;
        row.status_changed_at = time_point_sec(current_time_point());
        row.superseded_by = successor_id;
    });
}

void verification::revokecmmt(uint64_t id) {
    require_auth(get_self());
    validate_registry_id(id, "id");

    commitment_table commitments(get_self(), get_self().value);
    auto existing = commitments.find(id);
    check(existing != commitments.end(), "commitment does not exist");
    validate_commitment_is_active(*existing);

    commitments.modify(existing, get_self(), [&](auto& row) {
        row.status = commitment_status_revoked;
        row.status_changed_at = time_point_sec(current_time_point());
    });
}

void verification::expirecmmt(uint64_t id) {
    require_auth(get_self());
    validate_registry_id(id, "id");

    commitment_table commitments(get_self(), get_self().value);
    auto existing = commitments.find(id);
    check(existing != commitments.end(), "commitment does not exist");
    validate_commitment_is_active(*existing);

    commitments.modify(existing, get_self(), [&](auto& row) {
        row.status = commitment_status_expired;
        row.status_changed_at = time_point_sec(current_time_point());
    });
}

void verification::submitroot(
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
    validate_nonzero_checksum(root_hash, "root_hash");
    validate_nonzero_checksum(external_ref, "external_ref");

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
        row.status = batch_status_open;
    });
}

void verification::linkmanifest(uint64_t id, const checksum256& manifest_hash) {
    validate_registry_id(id, "id");
    validate_nonzero_checksum(manifest_hash, "manifest_hash");

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

void verification::closebatch(uint64_t id) {
    validate_registry_id(id, "id");

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
        row.status = batch_status_closed;
        row.status_changed_at = time_point_sec(current_time_point());
    });
}

void verification::record(
    const name& submitter,
    const checksum256& object_hash,
    const string& canonicalization_profile,
    const string& client_reference
) {
    require_auth(get_self());
    check(is_account(submitter), "submitter account does not exist");
    validate_printable_ascii_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_client_reference(client_reference);
    validate_new_request(submitter, client_reference);

    store_proof(submitter, object_hash, canonicalization_profile, client_reference);
}

void verification::setpaytoken(
    const name& token_contract,
    const asset& price
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_payment_price(price, "price");
    validate_token_contract_stat(token_contract, price.symbol);

    payment_token_table payment_tokens(get_self(), get_self().value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, price.symbol.code());
    auto existing = by_token.find(key);

    if (existing == by_token.end()) {
        payment_tokens.emplace(get_self(), [&](auto& row) {
            row.config_id = payment_tokens.available_primary_key();
            if (row.config_id == 0) {
                row.config_id = 1;
            }
            row.token_contract = token_contract;
            row.price = price;
            row.updated_at = time_point_sec(current_time_point());
        });
        return;
    }

    by_token.modify(existing, get_self(), [&](auto& row) {
        row.price = price;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification::rmpaytoken(const name& token_contract, const symbol& token_symbol) {
    require_auth(get_self());
    check(token_symbol.is_valid(), "token_symbol is invalid");

    payment_token_table payment_tokens(get_self(), get_self().value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol.code());
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "payment token config does not exist");

    by_token.erase(existing);
}

void verification::withdraw(
    const name& token_contract,
    const name& to,
    const asset& quantity,
    const string& memo
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    check(is_account(to), "to account does not exist");
    validate_nonnegative_asset(quantity, "quantity");
    check(quantity.amount > 0, "quantity must be positive");
    validate_text(memo, 128, "memo", true);

    action(
        permission_level{get_self(), "active"_n},
        token_contract,
        "transfer"_n,
        std::make_tuple(get_self(), to, quantity, memo)
    ).send();
}

void verification::ontransfer(const name& from, const name& to, const asset& quantity, const string& memo) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    check(quantity.amount > 0, "payment must be positive");

    auto [object_hash, hash_algorithm, canonicalization_profile, client_reference] = parse_payment_memo(memo);
    const auto parsed_hash = parse_hash(object_hash);

    validate_text(hash_algorithm, 16, "hash_algorithm", false);
    validate_printable_ascii_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_client_reference(client_reference);
    check(hash_algorithm == "SHA-256", "only SHA-256 is currently supported");
    validate_new_request(from, client_reference);

    const name payment_token_contract = get_first_receiver();
    const auto expected_price = resolve_price(payment_token_contract, quantity.symbol);
    check(quantity == expected_price, "incorrect payment amount");

    store_proof(from, parsed_hash, canonicalization_profile, client_reference);
}

uint128_t verification::make_payment_key(const name& token_contract, const symbol_code& token_symbol) const {
    return (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.raw();
}

verification::payment_token verification::get_payment_token(
    const name& token_contract,
    const symbol_code& token_symbol
) const {
    payment_token_table payment_tokens(get_self(), get_self().value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "payment token is not configured");
    return *existing;
}

verification::kyc_row verification::require_kyc_record(const name& account) const {
    kyc_table kyc_records(get_self(), get_self().value);
    auto existing = kyc_records.find(account.value);
    check(existing != kyc_records.end(), "kyc record does not exist");
    return *existing;
}

verification::schema_row verification::require_schema(uint64_t id) const {
    validate_registry_id(id, "id");

    schema_table schemas(get_self(), get_self().value);
    auto existing = schemas.find(id);
    check(existing != schemas.end(), "schema does not exist");
    return *existing;
}

verification::policy_row verification::require_policy(uint64_t id) const {
    validate_registry_id(id, "id");

    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    check(existing != policies.end(), "policy does not exist");
    return *existing;
}

uint64_t verification::next_batch_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    if (state.next_batch_id == 0) {
        state.next_batch_id = 1;
    }

    const uint64_t allocated = state.next_batch_id;
    ++state.next_batch_id;
    counters.set(state, get_self());

    return allocated;
}

uint64_t verification::next_commitment_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    if (state.next_commitment_id == 0) {
        state.next_commitment_id = 1;
    }

    const uint64_t allocated = state.next_commitment_id;
    ++state.next_commitment_id;
    counters.set(state, get_self());

    return allocated;
}

asset verification::resolve_price(const name& token_contract, const symbol& token_symbol) const {
    check(is_account(token_contract), "token_contract does not exist");
    check(token_symbol.is_valid(), "token_symbol is invalid");

    const auto payment_token = get_payment_token(token_contract, token_symbol.code());
    check(
        payment_token.price.symbol == token_symbol,
        "token_symbol precision does not match configured payment token"
    );

    return payment_token.price;
}

checksum256 verification::parse_hash(const string& hex) const {
    check(hex.size() == hash_size * 2, "object hash must be 64 hex characters");

    std::array<uint8_t, hash_size> bytes{};
    for (size_t i = 0; i < bytes.size(); ++i) {
        const auto high = from_hex(hex[i * 2]);
        const auto low = from_hex(hex[i * 2 + 1]);
        bytes[i] = static_cast<uint8_t>((high << 4) | low);
    }

    return checksum256(bytes);
}

void verification::validate_nonzero_checksum(const checksum256& value, const char* field_name) const {
    check(!is_zero_checksum(value), string(field_name) + " cannot be zero");
}

void verification::validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const {
    batch_table batches(get_self(), get_self().value);
    auto by_request = batches.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    check(by_request.find(request_key) == by_request.end(), "duplicate batch request for submitter");
}

void verification::validate_batch_is_open(const batch_row& batch) const {
    check(batch.status == batch_status_open, "batch is not open");
}

void verification::validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const {
    commitment_table commitments(get_self(), get_self().value);
    auto by_request = commitments.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    check(by_request.find(request_key) == by_request.end(), "duplicate request for submitter");
}

void verification::validate_commitment_can_be_successor(
    const commitment_row& current,
    const commitment_row& successor
) const {
    validate_commitment_is_active(successor);
    check(successor.submitter == current.submitter, "successor must have the same submitter");
    check(successor.schema_id == current.schema_id, "successor must have the same schema_id");
    check(successor.policy_id == current.policy_id, "successor must have the same policy_id");
    check(successor.created_at >= current.created_at, "successor must not predate current commitment");
}

void verification::validate_commitment_is_active(const commitment_row& commitment) const {
    check(commitment.status == commitment_status_active, "commitment is not active");
}

void verification::validate_future_time(const time_point_sec& value, const char* field_name) const {
    check(value > time_point_sec(current_time_point()), string(field_name) + " must be in the future");
}

void verification::validate_registry_id(uint64_t id, const char* field_name) const {
    check(id > 0, string(field_name) + " must be greater than zero");
}

void verification::validate_client_reference(const string& client_reference) const {
    validate_printable_ascii_text(client_reference, 128, "client_reference", false);

    for (char ch : client_reference) {
        check(ch != '|', "client_reference cannot contain '|'");
    }
}

void verification::validate_printable_ascii_text(
    const string& value,
    uint32_t max_length,
    const char* field_name,
    bool allow_empty
) const {
    validate_text(value, max_length, field_name, allow_empty);

    for (char ch : value) {
        const unsigned char code = static_cast<unsigned char>(ch);
        check(code >= 32 && code <= 126, string(field_name) + " must use printable ASCII characters");
    }
}

void verification::validate_policy_settings(
    bool allow_single,
    bool allow_batch,
    bool require_kyc,
    uint8_t min_kyc_level,
    bool allow_zk,
    bool active
) const {
    if (!require_kyc) {
        check(min_kyc_level == 0, "min_kyc_level must be zero when require_kyc is false");
    }

    if (active) {
        check(
            allow_single || allow_batch || allow_zk,
            "active policy must enable at least one supported mode"
        );
    }
}

void verification::validate_payment_price(const asset& price, const char* field_name) const {
    check(price.is_valid(), string(field_name) + " is invalid");
    check(price.amount > 0, string(field_name) + " must be positive");
    check(price.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

void verification::validate_nonnegative_asset(const asset& quantity, const char* field_name) const {
    check(quantity.is_valid(), string(field_name) + " is invalid");
    check(quantity.amount >= 0, string(field_name) + " cannot be negative");
    check(quantity.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

std::tuple<string, string, string, string> verification::parse_payment_memo(const string& memo) const {
    const auto first = memo.find('|');
    const auto second = memo.find('|', first == string::npos ? first : first + 1);
    const auto third = memo.find('|', second == string::npos ? second : second + 1);

    check(
        first != string::npos &&
        second != string::npos &&
        third != string::npos &&
        memo.find('|', third + 1) == string::npos,
        "memo format must be hash|algorithm|canonicalization|client_reference"
    );

    return std::make_tuple(
        memo.substr(0, first),
        memo.substr(first + 1, second - first - 1),
        memo.substr(second + 1, third - second - 1),
        memo.substr(third + 1)
    );
}

uint8_t verification::from_hex(char c) const {
    if (c >= '0' && c <= '9') {
        return static_cast<uint8_t>(c - '0');
    }
    if (c >= 'a' && c <= 'f') {
        return static_cast<uint8_t>(10 + (c - 'a'));
    }
    if (c >= 'A' && c <= 'F') {
        return static_cast<uint8_t>(10 + (c - 'A'));
    }

    check(false, "object hash contains non-hex characters");
    return 0;
}

void verification::validate_new_request(const name& submitter, const string& client_reference) const {
    proof_table proofs(get_self(), get_self().value);
    auto by_request = proofs.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, client_reference);
    check(by_request.find(request_key) == by_request.end(), "duplicate client_reference for submitter");
}

void verification::store_proof(
    const name& submitter,
    const checksum256& object_hash,
    const string& canonicalization_profile,
    const string& client_reference
) {
    proof_table proofs(get_self(), get_self().value);
    uint64_t next_id = static_cast<uint64_t>(current_time_point().sec_since_epoch());
    while (proofs.find(next_id) != proofs.end()) {
        ++next_id;
    }

    proofs.emplace(get_self(), [&](auto& row) {
        row.proof_id = next_id;
        row.writer = get_self();
        row.submitter = submitter;
        row.object_hash = object_hash;
        row.canonicalization_profile = canonicalization_profile;
        row.client_reference = client_reference;
        row.submitted_at = time_point_sec(current_time_point());
    });
}

void verification::validate_text(
    const string& value,
    uint32_t max_length,
    const char* field_name,
    bool allow_empty
) const {
    if (!allow_empty) {
        check(!value.empty(), string(field_name) + " cannot be empty");
    }
    check(value.size() <= max_length, string(field_name) + " is too long");
}

extern "C" {
    [[eosio::wasm_entry]]
    void apply(uint64_t receiver, uint64_t code, uint64_t action) {
        if (code == receiver) {
            switch (action) {
                EOSIO_DISPATCH_HELPER(
                    verification,
                    (issuekyc)(renewkyc)(revokekyc)(suspendkyc)
                    (addschema)(updateschema)(deprecate)
                    (setpolicy)(enablezk)(disablezk)
                    (submit)(supersede)(revokecmmt)(expirecmmt)
                    (submitroot)(linkmanifest)(closebatch)
                    (record)(setpaytoken)(rmpaytoken)(withdraw)
                )
            }
            return;
        }

        if (action == "transfer"_n.value) {
            eosio::execute_action(name(receiver), name(code), &verification::ontransfer);
        }
    }
}
