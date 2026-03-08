#include "gfnotary.hpp"

void gfnotary::addwhuser(const name& account, const string& note) {
    require_auth(get_self());
    check(is_account(account), "account does not exist");
    validate_text(note, 256, "note", true);

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
    validate_text(note, 256, "note", true);

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
}

void gfnotary::setpaytoken(
    const name& token_contract,
    const asset& retail_price,
    const asset& wholesale_price
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_payment_price(retail_price, "retail_price");
    validate_payment_price(wholesale_price, "wholesale_price");
    check(
        retail_price.symbol == wholesale_price.symbol,
        "retail_price and wholesale_price must use the same symbol"
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
            row.updated_at = time_point_sec(current_time_point());
        });
        return;
    }

    by_token.modify(existing, get_self(), [&](auto& row) {
        row.retail_price = retail_price;
        row.wholesale_price = wholesale_price;
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
    validate_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_text(client_reference, 128, "client_reference", true);
    check(hash_algorithm == "SHA-256", "only SHA-256 is currently supported");

    store_proof(
        submitter,
        object_hash,
        hash_algorithm,
        canonicalization_profile,
        client_reference,
        name{},
        nonprofit_price()
    );
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
    check(quantity.amount > 0, "quantity must be positive");
    validate_text(memo, 128, "memo", true);

    get_payment_token(token_contract, quantity.symbol.code());

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

    auto parts = split_memo(memo, '|');
    check(parts.size() == 3 || parts.size() == 4, "memo format must be hash|algorithm|canonicalization|client_reference");

    const string& object_hash = parts[0];
    const string& hash_algorithm = parts[1];
    const string& canonicalization_profile = parts[2];
    const string client_reference = parts.size() == 4 ? parts[3] : "";

    validate_hash(object_hash);
    validate_text(hash_algorithm, 16, "hash_algorithm", false);
    validate_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_text(client_reference, 128, "client_reference", true);
    check(hash_algorithm == "SHA-256", "only SHA-256 is currently supported");

    const name payment_token_contract = get_first_receiver();
    const asset expected_price = resolve_price(from, payment_token_contract, quantity.symbol);
    check(quantity == expected_price, "incorrect payment amount for current pricing tier");

    store_proof(
        from,
        object_hash,
        hash_algorithm,
        canonicalization_profile,
        client_reference,
        payment_token_contract,
        quantity
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

asset gfnotary::resolve_price(
    const name& account,
    const name& token_contract,
    const symbol& token_symbol
) const {
    check(is_account(token_contract), "token_contract does not exist");
    check(token_symbol.is_valid(), "token_symbol is invalid");

    auto payment_token = get_payment_token(token_contract, token_symbol.code());
    check(
        payment_token.retail_price.symbol == token_symbol,
        "token_symbol precision does not match configured payment token"
    );

    if (isnporg(account)) {
        return asset{0, token_symbol};
    }

    return iswhuser(account) ? payment_token.wholesale_price : payment_token.retail_price;
}

void gfnotary::validate_hash(const string& hex) const {
    check(hex.size() == hash_size * 2, "object hash must be 64 hex characters");

    for (char ch : hex) {
        (void)from_hex(ch);
    }
}

void gfnotary::validate_payment_price(const asset& price, const char* field_name) const {
    check(price.is_valid(), string(field_name) + " is invalid");
    check(price.amount > 0, string(field_name) + " must be positive");
    check(price.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

std::vector<string> gfnotary::split_memo(const string& memo, char delimiter) const {
    std::vector<string> parts;
    string current;

    for (char ch : memo) {
        if (ch == delimiter) {
            parts.push_back(current);
            current.clear();
            continue;
        }

        current.push_back(ch);
    }

    parts.push_back(current);
    return parts;
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
    const asset& price
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
        row.wholesale_pricing = iswhuser(submitter);
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
