#include <verification_retail_payment.hpp>

#include <limits>
#include <vector>

namespace {
struct token_stat_row {
    eosio::asset supply;
    eosio::asset max_supply;
    eosio::name issuer;

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

std::vector<string> split_memo_fields(const string& memo) {
    std::vector<string> fields;
    size_t start = 0;
    while (true) {
        const auto separator = memo.find('|', start);
        if (separator == string::npos) {
            fields.push_back(memo.substr(start));
            break;
        }
        fields.push_back(memo.substr(start, separator - start));
        start = separator + 1;
    }
    return fields;
}

uint64_t parse_decimal_u64(const string& value, const char* field_name) {
    verification_validators::validate_printable_ascii_text(value, 20, field_name, false);
    check(!value.empty(), string(field_name) + " must not be empty");

    uint64_t parsed = 0;
    for (char ch : value) {
        check(ch >= '0' && ch <= '9', string(field_name) + " must be a decimal integer");
        const auto digit = static_cast<uint64_t>(ch - '0');
        check(
            parsed <= (std::numeric_limits<uint64_t>::max() - digit) / 10,
            string(field_name) + " exceeds supported range"
        );
        parsed = (parsed * 10) + digit;
    }

    return parsed;
}
}  // namespace

void verification_retail_payment::settoken(const name& token_contract, const symbol& token_symbol) {
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

void verification_retail_payment::rmtoken(const name& token_contract, const symbol_code& token_symbol) {
    require_auth(get_self());

    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "retail payment token is not configured");

    tariff_table tariffs(get_self(), get_self().value);
    auto by_tariff_token = tariffs.get_index<"bytokensym"_n>();
    check(by_tariff_token.find(key) == by_tariff_token.end(), "cannot remove token with active retail tariffs");

    by_token.erase(existing);
}

void verification_retail_payment::setprice(uint8_t mode, const name& token_contract, const asset& price_per_kib) {
    require_auth(get_self());
    check(mode == retail_mode_single || mode == retail_mode_batch, "unsupported retail tariff mode");
    check(is_account(token_contract), "token_contract does not exist");
    verification_validators::validate_payment_price(price_per_kib, "price_per_kib");
    validate_token_contract_stat(token_contract, price_per_kib.symbol);
    require_accepted_token(token_contract, price_per_kib.symbol.code());

    tariff_table tariffs(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());
    const auto key = make_payment_key(token_contract, price_per_kib.symbol.code());

    for (auto existing = tariffs.begin(); existing != tariffs.end(); ++existing) {
        if (existing->mode == mode && existing->bytokensym() == key) {
            tariffs.modify(existing, get_self(), [&](auto& row) {
                row.price_per_kib = price_per_kib;
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
        row.price_per_kib = price_per_kib;
        row.active = true;
        row.updated_at = now;
    });
}

void verification_retail_payment::setverifacct(const name& verification_account) {
    require_auth(get_self());
    check(is_account(verification_account), "verification_account does not exist");

    retail_payment_config_singleton config(get_self(), get_self().value);
    config.set(retail_payment_config{verification_account}, get_self());
}

void verification_retail_payment::withdraw(
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

void verification_retail_payment::ontransfer(
    const name& from,
    const name& to,
    const asset& quantity,
    const string& memo
) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    verification_validators::validate_payment_price(quantity, "quantity");

    const auto parsed_payment = parse_payment_memo(memo);
    const auto mode = parsed_payment.mode;
    const auto submitter = parsed_payment.submitter;
    const auto external_ref = parsed_payment.external_ref;
    const auto billable_bytes = mode == retail_mode_single
        ? verification_request_size::compute_single_registry_bytes(
            submitter,
            parsed_payment.schema_id,
            parsed_payment.policy_id,
            parsed_payment.object_hash,
            external_ref
        )
        : verification_request_size::compute_batch_registry_bytes(
            submitter,
            parsed_payment.schema_id,
            parsed_payment.policy_id,
            parsed_payment.root_hash,
            parsed_payment.leaf_count,
            parsed_payment.manifest_hash,
            external_ref
        );
    const auto billable_kib = verification_validators::derive_billable_kib(billable_bytes);
    check(from == submitter, "payer must match submitter for retail flow");

    require_accepted_token(get_first_receiver(), quantity.symbol.code());
    const auto tariff = require_tariff(mode, get_first_receiver(), quantity.symbol);

    const auto price_per_kib_amount = static_cast<uint64_t>(tariff.price_per_kib.amount);
    check(
        billable_kib <= static_cast<uint64_t>(std::numeric_limits<int64_t>::max()) / price_per_kib_amount,
        "retail payment amount exceeds supported range"
    );
    const auto expected_amount = static_cast<int64_t>(price_per_kib_amount * billable_kib);
    check(quantity == asset(expected_amount, tariff.price_per_kib.symbol), "retail payment must match exact size-based tariff");

    check(parsed_payment.atomic, "retail memo must use atomic contract-only format");

    const auto config = get_retail_payment_config();
    if (mode == retail_mode_single) {
        action(
            permission_level{get_self(), "active"_n},
            config.verification_account,
            "retailsub"_n,
            std::make_tuple(
                submitter,
                parsed_payment.schema_id,
                parsed_payment.policy_id,
                parsed_payment.object_hash,
                external_ref
            )
        ).send();
        return;
    }

    action(
        permission_level{get_self(), "active"_n},
        config.verification_account,
        "retailbatch"_n,
        std::make_tuple(
            submitter,
            parsed_payment.schema_id,
            parsed_payment.policy_id,
            parsed_payment.root_hash,
            parsed_payment.leaf_count,
            parsed_payment.manifest_hash,
            external_ref
        )
    ).send();
}

uint128_t verification_retail_payment::make_payment_key(const name& token_contract, const symbol_code& token_symbol) const {
    return (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.raw();
}

verification_retail_payment::accepted_token_row verification_retail_payment::require_accepted_token(
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

verification_retail_payment::tariff_row verification_retail_payment::require_tariff(
    uint8_t mode,
    const name& token_contract,
    const symbol& token_symbol
) const {
    tariff_table tariffs(get_self(), get_self().value);
    const auto key = make_payment_key(token_contract, token_symbol.code());

    for (auto existing = tariffs.begin(); existing != tariffs.end(); ++existing) {
        if (existing->mode == mode && existing->bytokensym() == key) {
            check(existing->active, "retail tariff is inactive");
            check(existing->price_per_kib.symbol == token_symbol, "retail tariff symbol precision mismatch");
            return *existing;
        }
    }

    check(false, "retail tariff is not configured");
    return tariff_row{};
}

uint64_t verification_retail_payment::next_retail_token_id() {
    retail_counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : retail_counter_state{};
    const uint64_t allocated = state.next_token_id == 0 ? 1 : state.next_token_id;
    state.next_token_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_retail_payment::next_retail_tariff_id() {
    retail_counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : retail_counter_state{};
    const uint64_t allocated = state.next_tariff_id == 0 ? 1 : state.next_tariff_id;
    state.next_tariff_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

verification_retail_payment::retail_payment_config verification_retail_payment::get_retail_payment_config() const {
    retail_payment_config_singleton config(get_self(), get_self().value);
    return config.exists() ? config.get() : retail_payment_config{};
}

verification_retail_payment::parsed_payment_memo verification_retail_payment::parse_payment_memo(const string& memo) const {
    const auto fields = split_memo_fields(memo);
    check(
        fields.size() == 6 || fields.size() == 8,
        "retail memo format must use the atomic retail variant"
    );

    const auto& mode_value = fields[0];
    const auto& submitter_value = fields[1];
    verification_validators::validate_printable_ascii_text(mode_value, 16, "mode", false);
    verification_validators::validate_printable_ascii_text(submitter_value, 13, "submitter", false);

    parsed_payment_memo parsed{};
    parsed.mode = parse_mode_label(mode_value);
    parsed.submitter = name(submitter_value);
    check(parsed.submitter.value > 0, "submitter in retail memo is invalid");
    check(is_account(parsed.submitter), "submitter account does not exist");

    parsed.atomic = true;
    parsed.schema_id = parse_decimal_u64(fields[2], "schema_id");
    parsed.policy_id = parse_decimal_u64(fields[3], "policy_id");

    if (fields.size() == 6) {
        check(parsed.mode == retail_mode_single, "single atomic retail memo must use single mode");
        verification_validators::validate_printable_ascii_text(fields[4], 64, "object_hash", false);
        verification_validators::validate_printable_ascii_text(fields[5], 64, "external_ref", false);
        check(fields[4].size() == 64, "object_hash must be 64 hex characters");
        check(fields[5].size() == 64, "external_ref must be 64 hex characters");
        parsed.object_hash = verification_validators::parse_hash(fields[4]);
        parsed.external_ref = verification_validators::parse_hash(fields[5]);
        return parsed;
    }

    check(parsed.mode == retail_mode_batch, "batch atomic retail memo must use batch mode");
    verification_validators::validate_printable_ascii_text(fields[4], 64, "root_hash", false);
    verification_validators::validate_printable_ascii_text(fields[5], 20, "leaf_count", false);
    verification_validators::validate_printable_ascii_text(fields[6], 64, "manifest_hash", false);
    verification_validators::validate_printable_ascii_text(fields[7], 64, "external_ref", false);
    check(fields[4].size() == 64, "root_hash must be 64 hex characters");
    check(fields[6].size() == 64, "manifest_hash must be 64 hex characters");
    check(fields[7].size() == 64, "external_ref must be 64 hex characters");
    parsed.root_hash = verification_validators::parse_hash(fields[4]);
    const auto parsed_leaf_count = parse_decimal_u64(fields[5], "leaf_count");
    check(parsed_leaf_count <= static_cast<uint64_t>(std::numeric_limits<uint32_t>::max()), "leaf_count exceeds supported range");
    parsed.leaf_count = static_cast<uint32_t>(parsed_leaf_count);
    check(parsed.leaf_count > 0, "leaf_count must be greater than zero");
    parsed.manifest_hash = verification_validators::parse_hash(fields[6]);
    parsed.external_ref = verification_validators::parse_hash(fields[7]);
    return parsed;
}
