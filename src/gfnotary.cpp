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

void gfnotary::withdraw(const name& to, const asset& quantity, const string& memo) {
    require_auth(get_self());
    check(is_account(to), "to account does not exist");
    check(quantity.symbol == gft_symbol(), "only GFT withdrawals are allowed");
    check(quantity.amount > 0, "quantity must be positive");
    validate_text(memo, 128, "memo", true);

    action(
        permission_level{get_self(), "active"_n},
        token_contract(),
        "transfer"_n,
        std::make_tuple(get_self(), to, quantity, memo)
    ).send();
}

void gfnotary::ontransfer(const name& from, const name& to, const asset& quantity, const string& memo) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    check(get_first_receiver() == token_contract(), "unsupported token contract");
    check(quantity.symbol == gft_symbol(), "payment must be in GFT");
    check(quantity.amount > 0, "payment must be positive");

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

    const asset expected_price = resolve_price(from);
    check(quantity == expected_price, "incorrect payment amount for current pricing tier");

    store_proof(from, object_hash, hash_algorithm, canonicalization_profile, client_reference, quantity);
}

asset gfnotary::quote(const name& account) const {
    check(is_account(account), "account does not exist");
    return resolve_price(account);
}

bool gfnotary::iswhuser(const name& account) const {
    wholesale_table wholesale(get_self(), get_self().value);
    return wholesale.find(account.value) != wholesale.end();
}

symbol gfnotary::gft_symbol() const {
    return symbol(symbol_code("GFT"), 4);
}

name gfnotary::token_contract() const {
    return "eosio.token"_n;
}

asset gfnotary::retail_price() const {
    return asset{10000, gft_symbol()};
}

asset gfnotary::wholesale_price() const {
    return asset{1000, gft_symbol()};
}

asset gfnotary::resolve_price(const name& account) const {
    return iswhuser(account) ? wholesale_price() : retail_price();
}

void gfnotary::validate_hash(const string& hex) const {
    check(hex.size() == hash_size * 2, "object hash must be 64 hex characters");

    for (char ch : hex) {
        (void)from_hex(ch);
    }
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
