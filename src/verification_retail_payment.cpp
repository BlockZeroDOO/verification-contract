#include <verification_retail_payment.hpp>

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

void verification_retail_payment::setprice(uint8_t mode, const name& token_contract, const asset& price) {
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

void verification_retail_payment::setverifacct(const name& verification_account) {
    require_auth(get_self());
    check(is_account(verification_account), "verification_account does not exist");

    retail_payment_config_singleton config(get_self(), get_self().value);
    config.set(retail_payment_config{verification_account}, get_self());
}

void verification_retail_payment::consume(uint64_t auth_id) {
    const auto config = get_retail_payment_config();
    check(
        has_auth(get_self()) || has_auth(config.verification_account),
        "missing required authority of retail payment contract or verif"
    );
    verification_validators::validate_registry_id(auth_id, "auth_id");

    usage_auth_table usage_auths(get_self(), get_self().value);
    auto existing = usage_auths.find(auth_id);
    check(existing != usage_auths.end(), "retail usage authorization does not exist");
    check(!existing->consumed, "retail usage authorization is already consumed");

    usage_auths.modify(existing, get_self(), [&](auto& row) {
        row.consumed = true;
        row.consumed_at = time_point_sec(current_time_point());
    });
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
    const auto mode = std::get<0>(parsed_payment);
    const auto submitter = std::get<1>(parsed_payment);
    const auto external_ref = std::get<2>(parsed_payment);
    check(from == submitter, "payer must match submitter for retail flow");

    require_accepted_token(get_first_receiver(), quantity.symbol.code());
    const auto tariff = require_tariff(mode, get_first_receiver(), quantity.symbol);
    check(quantity == tariff.price, "retail payment must match exact configured tariff");

    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    usage_auth_table usage_auths(get_self(), get_self().value);
    auto by_request = usage_auths.get_index<"byrequest"_n>();
    check(by_request.find(request_key) == by_request.end(), "retail usage authorization already exists for request");

    const auto now = time_point_sec(current_time_point());
    usage_auths.emplace(get_self(), [&](auto& row) {
        row.auth_id = next_retail_auth_id();
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
            check(existing->price.symbol == token_symbol, "retail tariff symbol precision mismatch");
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

uint64_t verification_retail_payment::next_retail_auth_id() {
    retail_counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : retail_counter_state{};
    const uint64_t allocated = state.next_auth_id == 0 ? 1 : state.next_auth_id;
    state.next_auth_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

verification_retail_payment::retail_payment_config verification_retail_payment::get_retail_payment_config() const {
    retail_payment_config_singleton config(get_self(), get_self().value);
    return config.exists() ? config.get() : retail_payment_config{};
}

std::tuple<uint8_t, name, checksum256> verification_retail_payment::parse_payment_memo(const string& memo) const {
    const auto first = memo.find('|');
    const auto second = memo.find('|', first == string::npos ? first : first + 1);

    check(
        first != string::npos &&
        second != string::npos &&
        memo.find('|', second + 1) == string::npos,
        "retail memo format must be mode|submitter|external_ref"
    );

    const auto mode_value = memo.substr(0, first);
    const auto submitter_value = memo.substr(first + 1, second - first - 1);
    const auto external_ref_value = memo.substr(second + 1);

    verification_validators::validate_printable_ascii_text(mode_value, 16, "mode", false);
    verification_validators::validate_printable_ascii_text(submitter_value, 13, "submitter", false);
    verification_validators::validate_printable_ascii_text(external_ref_value, 64, "external_ref", false);
    check(external_ref_value.size() == 64, "external_ref must be 64 hex characters");

    const auto submitter = name(submitter_value);
    check(submitter.value > 0, "submitter in retail memo is invalid");
    check(is_account(submitter), "submitter account does not exist");

    return std::make_tuple(parse_mode_label(mode_value), submitter, verification_validators::parse_hash(external_ref_value));
}
