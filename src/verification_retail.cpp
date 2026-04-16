#include <verification_retail.hpp>

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
    return verification_validators::is_zero_checksum(value);
}

uint8_t parse_mode_label(const string& value) {
    if (value == "single") {
        return 0;
    }
    if (value == "batch") {
        return 1;
    }

    eosio::check(false, "unsupported retail payment mode");
    return 0;
}
}  // namespace

void verification_retail::addschema(
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

void verification_retail::updateschema(
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

void verification_retail::deprecate(uint64_t id) {
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

void verification_retail::setpolicy(
    uint64_t id,
    bool allow_single,
    bool allow_batch,
    bool active
) {
    require_auth(get_self());
    verification_validators::validate_registry_id(id, "id");
    policy_table policies(get_self(), get_self().value);
    auto existing = policies.find(id);
    verification_validators::validate_policy_settings(allow_single, allow_batch, active);

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

void verification_retail::submit(
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

    const auto receipt = require_pending_receipt(retail_mode_single, submitter, external_ref);
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
    });

    consume_receipt(receipt.receipt_id);
}

void verification_retail::submitroot(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& root_hash,
    uint32_t leaf_count,
    const checksum256& manifest_hash,
    const checksum256& external_ref
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    check(leaf_count > 0, "leaf_count must be greater than zero");
    verification_validators::validate_nonzero_checksum(root_hash, "root_hash");
    verification_validators::validate_nonzero_checksum(manifest_hash, "manifest_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");

    const auto schema = require_schema(schema_id);
    check(schema.active, "schema is inactive");

    const auto policy = require_policy(policy_id);
    check(policy.active, "policy is inactive");
    check(policy.allow_batch, "policy does not allow batch submissions");

    const auto receipt = require_pending_receipt(retail_mode_batch, submitter, external_ref);
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
        row.external_ref = external_ref;
        row.request_key = request_key;
        row.block_num = static_cast<uint32_t>(eosio::tapos_block_num());
        row.created_at = now;
    });

    consume_receipt(receipt.receipt_id);
}

void verification_retail::settoken(const name& token_contract, const symbol& token_symbol) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    check(token_symbol.is_valid(), "token_symbol is invalid");
    validate_token_contract_stat(token_contract, token_symbol);

    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol.code());
    auto existing = by_token.find(key);
    const auto now = time_point_sec(current_time_point());

    if (existing == by_token.end()) {
        tokens.emplace(get_self(), [&](auto& row) {
            row.config_id = next_retail_token_id();
            row.token_contract = token_contract;
            row.token_symbol = token_symbol;
            row.enabled = true;
            row.updated_at = now;
        });
        return;
    }

    by_token.modify(existing, get_self(), [&](auto& row) {
        row.enabled = true;
        row.updated_at = now;
    });
}

void verification_retail::rmtoken(const name& token_contract, const symbol_code& token_symbol) {
    require_auth(get_self());

    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "retail token is not configured");

    tariff_table tariffs(get_self(), get_self().value);
    auto by_tariff_token = tariffs.get_index<"bytokensym"_n>();
    check(by_tariff_token.find(key) == by_tariff_token.end(), "cannot remove token with active retail tariffs");

    by_token.erase(existing);
}

void verification_retail::setprice(uint8_t mode, const name& token_contract, const asset& price) {
    require_auth(get_self());
    check(mode == retail_mode_single || mode == retail_mode_batch, "unsupported retail tariff mode");
    check(is_account(token_contract), "token_contract does not exist");
    verification_validators::validate_payment_price(price, "price");
    validate_token_contract_stat(token_contract, price.symbol);
    require_accepted_token(token_contract, price.symbol.code());

    tariff_table tariffs(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());
    const auto key = make_payment_key(token_contract, price.symbol.code());

    for (auto existing = tariffs.begin(); existing != tariffs.end(); ++existing) {
        if (existing->mode == mode && existing->bytokensym() == key) {
            tariffs.modify(existing, get_self(), [&](auto& row) {
                row.price = price;
                row.active = true;
                row.updated_at = now;
            });
            return;
        }
    }

    tariffs.emplace(get_self(), [&](auto& row) {
        row.config_id = next_retail_tariff_id();
        row.mode = mode;
        row.token_contract = token_contract;
        row.price = price;
        row.active = true;
        row.updated_at = now;
    });
}

void verification_retail::withdraw(
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

void verification_retail::ontransfer(const name& from, const name& to, const asset& quantity, const string& memo) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    verification_validators::validate_payment_price(quantity, "quantity");

    const auto [parsed_mode, parsed_submitter, parsed_external_ref] = parse_payment_memo(memo);
    const auto mode = parsed_mode;
    const auto submitter = parsed_submitter;
    const auto external_ref = parsed_external_ref;
    check(from == submitter, "payer must match submitter for retail flow");

    require_accepted_token(get_first_receiver(), quantity.symbol.code());
    const auto tariff = require_tariff(mode, get_first_receiver(), quantity.symbol);
    check(quantity == tariff.price, "retail payment must match exact configured tariff");

    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    payment_receipt_table receipts(get_self(), get_self().value);
    auto by_request = receipts.get_index<"byrequest"_n>();
    check(by_request.find(request_key) == by_request.end(), "retail payment receipt already exists for request");

    const auto now = time_point_sec(current_time_point());
    receipts.emplace(get_self(), [&](auto& row) {
        row.receipt_id = next_retail_receipt_id();
        row.mode = mode;
        row.payer = from;
        row.submitter = submitter;
        row.external_ref = external_ref;
        row.request_key = request_key;
        row.token_contract = get_first_receiver();
        row.quantity = quantity;
        row.consumed = false;
        row.created_at = now;
        row.consumed_at = time_point_sec{};
    });
}

uint128_t verification_retail::make_payment_key(const name& token_contract, const symbol_code& token_symbol) const {
    return (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.raw();
}

verification_retail::schema_row verification_retail::require_schema(uint64_t id) const {
    return verification_core::require_schema(get_self(), id);
}

verification_retail::policy_row verification_retail::require_policy(uint64_t id) const {
    return verification_core::require_policy(get_self(), id);
}

uint64_t verification_retail::next_batch_id() {
    return verification_core::next_batch_id(get_self());
}

uint64_t verification_retail::next_commitment_id() {
    return verification_core::next_commitment_id(get_self());
}

void verification_retail::validate_batch_request_unique(const name& submitter, const checksum256& external_ref) const {
    verification_core::validate_batch_request_unique(get_self(), submitter, external_ref);
}

void verification_retail::validate_commitment_request_unique(const name& submitter, const checksum256& external_ref) const {
    verification_core::validate_commitment_request_unique(get_self(), submitter, external_ref);
}

verification_retail::accepted_token_row verification_retail::require_accepted_token(
    const name& token_contract,
    const symbol_code& token_symbol
) const {
    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "retail payment token is not configured");
    check(existing->enabled, "retail payment token is disabled");
    return *existing;
}

verification_retail::tariff_row verification_retail::require_tariff(
    uint8_t mode,
    const name& token_contract,
    const symbol& token_symbol
) const {
    tariff_table tariffs(get_self(), get_self().value);
    const auto key = make_payment_key(token_contract, token_symbol.code());

    for (auto existing = tariffs.begin(); existing != tariffs.end(); ++existing) {
        if (existing->mode == mode && existing->bytokensym() == key) {
            check(existing->active, "retail tariff is inactive");
            check(existing->price.symbol == token_symbol, "retail tariff symbol precision mismatch");
            return *existing;
        }
    }

    check(false, "retail tariff is not configured");
    return tariff_row{};
}

verification_retail::payment_receipt_row verification_retail::require_pending_receipt(
    uint8_t mode,
    const name& submitter,
    const checksum256& external_ref
) const {
    payment_receipt_table receipts(get_self(), get_self().value);
    auto by_request = receipts.get_index<"byrequest"_n>();
    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    auto existing = by_request.find(request_key);
    check(existing != by_request.end(), "retail payment receipt is missing");
    check(!existing->consumed, "retail payment receipt is already consumed");
    check(existing->mode == mode, "retail payment receipt mode does not match request");
    check(existing->submitter == submitter, "retail payment receipt submitter does not match request");
    check(existing->external_ref == external_ref, "retail payment receipt external_ref does not match request");
    return *existing;
}

uint64_t verification_retail::next_retail_token_id() {
    retail_counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : retail_counter_state{};
    if (state.next_token_id == 0) {
        state.next_token_id = 1;
    }
    const uint64_t allocated = state.next_token_id;
    ++state.next_token_id;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_retail::next_retail_tariff_id() {
    retail_counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : retail_counter_state{};
    if (state.next_tariff_id == 0) {
        state.next_tariff_id = 1;
    }
    const uint64_t allocated = state.next_tariff_id;
    ++state.next_tariff_id;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_retail::next_retail_receipt_id() {
    retail_counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : retail_counter_state{};
    if (state.next_receipt_id == 0) {
        state.next_receipt_id = 1;
    }
    const uint64_t allocated = state.next_receipt_id;
    ++state.next_receipt_id;
    counters.set(state, get_self());
    return allocated;
}

std::tuple<uint8_t, name, checksum256> verification_retail::parse_payment_memo(const string& memo) const {
    const auto first = memo.find('|');
    const auto second = memo.find('|', first == string::npos ? first : first + 1);

    check(
        first != string::npos &&
        second != string::npos &&
        memo.find('|', second + 1) == string::npos,
        "retail memo format must be mode|submitter|external_ref"
    );

    const auto mode_label = memo.substr(0, first);
    const auto submitter_value = memo.substr(first + 1, second - first - 1);
    const auto external_ref_hex = memo.substr(second + 1);

    verification_validators::validate_printable_ascii_text(mode_label, 16, "mode", false);
    verification_validators::validate_printable_ascii_text(submitter_value, 13, "submitter", false);

    const name submitter = name(submitter_value);
    check(submitter.length() > 0, "submitter in retail memo is invalid");
    check(is_account(submitter), "submitter account does not exist");

    return std::make_tuple(
        parse_mode_label(mode_label),
        submitter,
        verification_validators::parse_hash(external_ref_hex)
    );
}

void verification_retail::consume_receipt(uint64_t receipt_id) {
    payment_receipt_table receipts(get_self(), get_self().value);
    auto existing = receipts.find(receipt_id);
    check(existing != receipts.end(), "retail payment receipt does not exist");
    check(!existing->consumed, "retail payment receipt is already consumed");

    receipts.modify(existing, get_self(), [&](auto& row) {
        row.consumed = true;
        row.consumed_at = time_point_sec(current_time_point());
    });
}
