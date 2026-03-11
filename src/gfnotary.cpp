#include <gfnotary.hpp>

#include <eosio/dispatcher.hpp>

void gfnotary::addwhuser(const name& account, const string& note) {
    require_auth(get_self());
    check(is_account(account), "account does not exist");
    check(!isnporg(account), "account is already marked as nonprofit");
    validate_printable_ascii_text(note, 256, "note", true);

    wholesale_table wholesale(get_self(), get_self().value);
    auto existing = wholesale.find(account.value);
    check(existing == wholesale.end(), "account is already marked as wholesale");

    wholesale.emplace(get_self(), [&](auto& row) {
        row.account = account;
        row.note = note;
        row.added_at = time_point_sec(current_time_point());
    });
}

void gfnotary::rmwhuser(const name& account) {
    require_auth(get_self());

    wholesale_table wholesale(get_self(), get_self().value);
    auto existing = wholesale.find(account.value);
    check(existing != wholesale.end(), "account is not in wholesale table");

    wholesale.erase(existing);
}

void gfnotary::addnporg(const name& account, const string& note) {
    require_auth(get_self());
    check(is_account(account), "account does not exist");
    check(!iswhuser(account), "account is already marked as wholesale");
    validate_printable_ascii_text(note, 256, "note", true);

    nonprofit_table nonprofits(get_self(), get_self().value);
    auto existing = nonprofits.find(account.value);
    check(existing == nonprofits.end(), "account is already marked as nonprofit");

    nonprofits.emplace(get_self(), [&](auto& row) {
        row.account = account;
        row.note = note;
        row.added_at = time_point_sec(current_time_point());
    });
}

void gfnotary::rmnporg(const name& account) {
    require_auth(get_self());

    nonprofit_table nonprofits(get_self(), get_self().value);
    auto existing = nonprofits.find(account.value);
    check(existing != nonprofits.end(), "account is not in nonprofit table");

    nonprofits.erase(existing);

    free_usage_table free_usage(get_self(), get_self().value);
    auto usage = free_usage.find(account.value);
    if (usage != free_usage.end()) {
        free_usage.erase(usage);
    }
}

void gfnotary::setpaytoken(
    const name& token_contract,
    const asset& retail_price,
    const asset& wholesale_price,
    const asset& storage_price
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_payment_price(retail_price, "retail_price");
    validate_payment_price(wholesale_price, "wholesale_price");
    validate_nonnegative_asset(storage_price, "storage_price");
    check(
        retail_price.symbol == wholesale_price.symbol,
        "retail_price and wholesale_price must use the same symbol"
    );
    check(
        retail_price.symbol == storage_price.symbol,
        "storage_price must use the same symbol as retail_price"
    );
    check(
        wholesale_price.amount <= retail_price.amount,
        "wholesale_price cannot exceed retail_price"
    );

    payment_token_table payment_tokens(get_self(), get_self().value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    auto key = make_payment_key(token_contract, retail_price.symbol.code());
    auto existing = by_token.find(key);

    if (existing == by_token.end()) {
        payment_tokens.emplace(get_self(), [&](auto& row) {
            row.config_id = payment_tokens.available_primary_key();
            if (row.config_id == 0) {
                row.config_id = 1;
            }
            row.token_contract = token_contract;
            row.retail_price = retail_price;
            row.wholesale_price = wholesale_price;
            row.storage_price = storage_price;
            row.updated_at = time_point_sec(current_time_point());
        });
        return;
    }

    by_token.modify(existing, get_self(), [&](auto& row) {
        row.retail_price = retail_price;
        row.wholesale_price = wholesale_price;
        row.storage_price = storage_price;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void gfnotary::rmpaytoken(const name& token_contract, const symbol& token_symbol) {
    require_auth(get_self());
    check(token_symbol.is_valid(), "token_symbol is invalid");

    payment_token_table payment_tokens(get_self(), get_self().value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    auto key = make_payment_key(token_contract, token_symbol.code());
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "payment token config does not exist");

    by_token.erase(existing);
}

void gfnotary::submitfree(
    const name& submitter,
    const string& object_hash,
    const string& hash_algorithm,
    const string& canonicalization_profile,
    const string& client_reference
) {
    require_auth(submitter);
    check(is_account(submitter), "submitter account does not exist");
    check(isnporg(submitter), "submitter is not in nonprofit table");

    validate_hash(object_hash);
    validate_text(hash_algorithm, 16, "hash_algorithm", false);
    validate_printable_ascii_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_client_reference(client_reference);
    check(hash_algorithm == "SHA-256", "only SHA-256 is currently supported");
    const auto request_key = compute_request_key(submitter, client_reference);
    validate_new_request(request_key);
    consume_free_allowance(submitter);

    store_proof(
        submitter,
        object_hash,
        hash_algorithm,
        canonicalization_profile,
        client_reference,
        name{},
        nonprofit_price(),
        false
    );
}

void gfnotary::setfreecfg(
    bool enabled,
    uint32_t daily_free_limit
) {
    require_auth(get_self());

    const time_point_sec now = time_point_sec(current_time_point());
    const time_point_sec window_start = current_day_start(now);

    if (enabled) {
        check(daily_free_limit > 0, "daily_free_limit must be positive when free submissions are enabled");
    }

    free_policy_singleton policy_store(get_self(), get_self().value);
    free_policy policy;
    if (policy_store.exists()) {
        policy = policy_store.get();
        if (policy.window_start != window_start) {
            policy.window_start = window_start;
            policy.used_in_window = 0;
        }
    } else {
        policy.window_start = window_start;
        policy.used_in_window = 0;
    }

    policy.enabled = enabled;
    policy.daily_free_limit = daily_free_limit;
    policy.updated_at = now;
    policy_store.set(policy, get_self());
}

void gfnotary::withdraw(
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

void gfnotary::ontransfer(const name& from, const name& to, const asset& quantity, const string& memo) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    check(quantity.amount > 0, "payment must be positive");
    check(!isnporg(from), "nonprofit accounts must use submitfree");

    auto [object_hash, hash_algorithm, canonicalization_profile, client_reference] = parse_payment_memo(memo);

    validate_hash(object_hash);
    validate_text(hash_algorithm, 16, "hash_algorithm", false);
    validate_printable_ascii_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_client_reference(client_reference);
    check(hash_algorithm == "SHA-256", "only SHA-256 is currently supported");
    const auto request_key = compute_request_key(from, client_reference);
    validate_new_request(request_key);

    const name payment_token_contract = get_first_receiver();
    const auto pricing = resolve_paid_pricing(from, payment_token_contract, quantity.symbol);
    check(quantity == pricing.price, "incorrect payment amount for current pricing tier");

    store_proof(
        from,
        object_hash,
        hash_algorithm,
        canonicalization_profile,
        client_reference,
        payment_token_contract,
        quantity,
        pricing.wholesale_pricing
    );
}

asset gfnotary::quote(
    const name& account,
    const name& token_contract,
    const symbol& token_symbol
) const {
    check(is_account(account), "account does not exist");
    return resolve_price(account, token_contract, token_symbol);
}

bool gfnotary::iswhuser(const name& account) const {
    wholesale_table wholesale(get_self(), get_self().value);
    return wholesale.find(account.value) != wholesale.end();
}

bool gfnotary::isnporg(const name& account) const {
    nonprofit_table nonprofits(get_self(), get_self().value);
    return nonprofits.find(account.value) != nonprofits.end();
}

symbol gfnotary::free_symbol() const {
    return symbol(symbol_code("FREE"), 4);
}

asset gfnotary::nonprofit_price() const {
    return asset{0, free_symbol()};
}

gfnotary::free_policy gfnotary::get_free_policy() const {
    free_policy_singleton policy_store(get_self(), get_self().value);
    check(policy_store.exists(), "free submission config is not set");
    return policy_store.get();
}

time_point_sec gfnotary::current_day_start(const time_point_sec& timestamp) const {
    const uint32_t timestamp_seconds = timestamp.sec_since_epoch();
    return time_point_sec((timestamp_seconds / seconds_per_day) * seconds_per_day);
}

uint128_t gfnotary::make_payment_key(const name& token_contract, const symbol_code& token_symbol) const {
    return (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.raw();
}

gfnotary::payment_token gfnotary::get_payment_token(
    const name& token_contract,
    const symbol_code& token_symbol
) const {
    payment_token_table payment_tokens(get_self(), get_self().value);
    auto by_token = payment_tokens.get_index<"bytokensym"_n>();
    auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "payment token is not configured");
    return *existing;
}

void gfnotary::consume_free_allowance(const name& submitter) {
    free_policy_singleton policy_store(get_self(), get_self().value);
    auto policy = get_free_policy();
    check(policy.enabled, "free submissions are disabled");

    const time_point_sec now = time_point_sec(current_time_point());
    const time_point_sec window_start = current_day_start(now);
    if (policy.window_start != window_start) {
        policy.window_start = window_start;
        policy.used_in_window = 0;
    }
    check(
        policy.used_in_window < policy.daily_free_limit,
        "daily sponsor pool exhausted"
    );

    free_usage_table usage_table(get_self(), get_self().value);
    auto usage = usage_table.find(submitter.value);

    if (usage == usage_table.end()) {
        usage_table.emplace(get_self(), [&](auto& row) {
            row.account = submitter;
            row.last_submit_at = now;
        });
    } else {
        const uint64_t now_seconds = static_cast<uint64_t>(now.sec_since_epoch());
        const uint64_t last_submit_seconds = static_cast<uint64_t>(usage->last_submit_at.sec_since_epoch());
        if (last_submit_seconds > 0) {
            check(
                now_seconds >= last_submit_seconds + nonprofit_cooldown_sec,
                "submitfree cooldown is still active"
            );
        }

        usage_table.modify(usage, get_self(), [&](auto& row) {
            row.last_submit_at = now;
        });
    }

    policy.used_in_window += 1;
    policy.updated_at = now;
    policy_store.set(policy, get_self());
}

gfnotary::pricing_decision gfnotary::resolve_pricing(
    const name& account,
    const name& token_contract,
    const symbol& token_symbol
) const {
    if (isnporg(account)) {
        return pricing_decision{asset{0, token_symbol}, false};
    }

    return resolve_token_pricing(token_contract, token_symbol, iswhuser(account));
}

asset gfnotary::resolve_price(
    const name& account,
    const name& token_contract,
    const symbol& token_symbol
) const {
    return resolve_pricing(account, token_contract, token_symbol).price;
}

gfnotary::pricing_decision gfnotary::resolve_paid_pricing(
    const name& account,
    const name& token_contract,
    const symbol& token_symbol
) const {
    return resolve_token_pricing(token_contract, token_symbol, iswhuser(account));
}

gfnotary::pricing_decision gfnotary::resolve_token_pricing(
    const name& token_contract,
    const symbol& token_symbol,
    bool wholesale_pricing
) const {
    check(is_account(token_contract), "token_contract does not exist");
    check(token_symbol.is_valid(), "token_symbol is invalid");

    auto payment_token = get_payment_token(token_contract, token_symbol.code());
    check(
        payment_token.retail_price.symbol == token_symbol,
        "token_symbol precision does not match configured payment token"
    );

    return pricing_decision{
        wholesale_pricing ? payment_token.wholesale_price : payment_token.retail_price,
        wholesale_pricing
    };
}

checksum256 gfnotary::compute_request_key(const name& submitter, const string& client_reference) {
    string payload = submitter.to_string();
    payload.push_back(':');
    payload += client_reference;
    return sha256(payload.data(), static_cast<uint32_t>(payload.size()));
}

void gfnotary::validate_new_request(const checksum256& request_key) const {
    proof_table proofs(get_self(), get_self().value);
    auto by_request = proofs.get_index<"byrequest"_n>();
    auto existing_request = by_request.find(request_key);
    check(existing_request == by_request.end(), "duplicate client_reference for submitter");
}

void gfnotary::validate_hash(const string& hex) const {
    check(hex.size() == hash_size * 2, "object hash must be 64 hex characters");

    for (char ch : hex) {
        (void)from_hex(ch);
    }
}

void gfnotary::validate_client_reference(const string& client_reference) const {
    validate_printable_ascii_text(client_reference, 128, "client_reference", false);

    for (char ch : client_reference) {
        check(ch != '|', "client_reference cannot contain '|'");
    }
}

void gfnotary::validate_printable_ascii_text(
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

void gfnotary::validate_payment_price(const asset& price, const char* field_name) const {
    check(price.is_valid(), string(field_name) + " is invalid");
    check(price.amount > 0, string(field_name) + " must be positive");
    check(price.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

void gfnotary::validate_nonnegative_asset(const asset& quantity, const char* field_name) const {
    check(quantity.is_valid(), string(field_name) + " is invalid");
    check(quantity.amount >= 0, string(field_name) + " cannot be negative");
    check(quantity.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

std::tuple<string, string, string, string> gfnotary::parse_payment_memo(const string& memo) const {
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

uint8_t gfnotary::from_hex(char c) const {
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

void gfnotary::store_proof(
    const name& submitter,
    const string& object_hash,
    const string& hash_algorithm,
    const string& canonicalization_profile,
    const string& client_reference,
    const name& payment_token_contract,
    const asset& price,
    bool wholesale_pricing
) {
    proof_table proofs(get_self(), get_self().value);

    uint64_t next_id = proofs.available_primary_key();
    if (next_id == 0) {
        next_id = 1;
    }

    proofs.emplace(get_self(), [&](auto& row) {
        row.proof_id = next_id;
        row.submitter = submitter;
        row.object_hash = object_hash;
        row.hash_algorithm = hash_algorithm;
        row.canonicalization_profile = canonicalization_profile;
        row.client_reference = client_reference;
        row.payment_token_contract = payment_token_contract;
        row.price_charged = price;
        row.wholesale_pricing = wholesale_pricing;
        row.submitted_at = time_point_sec(current_time_point());
    });
}

void gfnotary::validate_text(
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
                    gfnotary,
                    (addwhuser)(rmwhuser)(addnporg)(rmnporg)(setpaytoken)(rmpaytoken)(submitfree)
                    (setfreecfg)(withdraw)
                )
            }
            return;
        }

        if (action == "transfer"_n.value) {
            eosio::execute_action(name(receiver), name(code), &gfnotary::ontransfer);
        }
    }
}
