#include <verification_billing.hpp>

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

void validate_plan_config(
    const eosio::name& plan_code,
    const eosio::asset& price,
    uint32_t duration_sec,
    uint64_t included_kib
) {
    eosio::check(plan_code.value > 0, "plan_code is invalid");
    verification_validators::validate_payment_price(price, "price");
    eosio::check(duration_sec > 0, "duration_sec must be greater than zero");
    eosio::check(included_kib > 0, "plan must provide positive included_kib");
}

void validate_pack_config(
    const eosio::name& pack_code,
    const eosio::asset& price,
    uint64_t included_kib
) {
    eosio::check(pack_code.value > 0, "pack_code is invalid");
    verification_validators::validate_payment_price(price, "price");
    eosio::check(included_kib > 0, "pack must provide positive included_kib");
}
}  // namespace

void verification_billing::settoken(const name& token_contract, const symbol& token_symbol) {
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
            row.config_id = next_token_id();
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

void verification_billing::rmtoken(const name& token_contract, const symbol_code& token_symbol) {
    require_auth(get_self());

    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "billing token is not configured");

    plan_table plans(get_self(), get_self().value);
    for (auto itr = plans.begin(); itr != plans.end(); ++itr) {
        check(!(itr->active && itr->bytokensym() == key), "cannot remove token with active plans");
    }

    pack_table packs(get_self(), get_self().value);
    for (auto itr = packs.begin(); itr != packs.end(); ++itr) {
        check(!(itr->active && itr->bytokensym() == key), "cannot remove token with active packs");
    }

    by_token.erase(existing);
}

void verification_billing::setplan(
    const name& plan_code,
    const name& token_contract,
    const asset& price,
    uint32_t duration_sec,
    uint64_t included_kib,
    bool active
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_plan_config(plan_code, price, duration_sec, included_kib);
    validate_token_contract_stat(token_contract, price.symbol);
    require_accepted_token(token_contract, price.symbol.code());

    plan_table plans(get_self(), get_self().value);
    auto by_code = plans.get_index<"bycode"_n>();
    auto existing = by_code.find(plan_code.value);
    const auto now = time_point_sec(current_time_point());

    if (existing == by_code.end()) {
        plans.emplace(get_self(), [&](auto& row) {
            row.plan_id = next_plan_id();
            row.plan_code = plan_code;
            row.token_contract = token_contract;
            row.price = price;
            row.duration_sec = duration_sec;
            row.included_kib = included_kib;
            row.active = active;
            row.updated_at = now;
        });
        return;
    }

    by_code.modify(existing, get_self(), [&](auto& row) {
        row.token_contract = token_contract;
        row.price = price;
        row.duration_sec = duration_sec;
        row.included_kib = included_kib;
        row.active = active;
        row.updated_at = now;
    });
}

void verification_billing::deactplan(uint64_t plan_id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(plan_id, "plan_id");

    plan_table plans(get_self(), get_self().value);
    auto existing = plans.find(plan_id);
    check(existing != plans.end(), "plan does not exist");

    plans.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_billing::setpack(
    const name& pack_code,
    const name& token_contract,
    const asset& price,
    uint64_t included_kib,
    bool active
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_pack_config(pack_code, price, included_kib);
    validate_token_contract_stat(token_contract, price.symbol);
    require_accepted_token(token_contract, price.symbol.code());

    pack_table packs(get_self(), get_self().value);
    auto by_code = packs.get_index<"bycode"_n>();
    auto existing = by_code.find(pack_code.value);
    const auto now = time_point_sec(current_time_point());

    if (existing == by_code.end()) {
        packs.emplace(get_self(), [&](auto& row) {
            row.pack_id = next_pack_id();
            row.pack_code = pack_code;
            row.token_contract = token_contract;
            row.price = price;
            row.included_kib = included_kib;
            row.active = active;
            row.updated_at = now;
        });
        return;
    }

    by_code.modify(existing, get_self(), [&](auto& row) {
        row.token_contract = token_contract;
        row.price = price;
        row.included_kib = included_kib;
        row.active = active;
        row.updated_at = now;
    });
}

void verification_billing::deactpack(uint64_t pack_id) {
    require_auth(get_self());
    verification_validators::validate_registry_id(pack_id, "pack_id");

    pack_table packs(get_self(), get_self().value);
    auto existing = packs.find(pack_id);
    check(existing != packs.end(), "pack does not exist");

    packs.modify(existing, get_self(), [&](auto& row) {
        row.active = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_billing::setverifacct(const name& verification_account) {
    require_auth(get_self());
    check(is_account(verification_account), "verification_account does not exist");

    billing_config_singleton config(get_self(), get_self().value);
    config.set(billing_config{verification_account}, get_self());
}

void verification_billing::submit(
    const name& payer,
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& object_hash,
    const checksum256& external_ref,
    uint64_t billable_bytes
) {
    check(is_account(payer), "payer account does not exist");
    check(is_account(submitter), "submitter account does not exist");
    verification_validators::validate_nonzero_checksum(object_hash, "object_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");
    verification_validators::validate_billable_bytes(billable_bytes, "billable_bytes");
    require_auth(payer);
    require_contract_only_submitter(payer, submitter);

    const auto billable_kib = verification_validators::derive_billable_kib(billable_bytes);
    const auto entitlement = select_entitlement(payer, billable_kib);
    const auto config = get_billing_config();

    action(
        permission_level{get_self(), "active"_n},
        config.verification_account,
        "billsubmit"_n,
        std::make_tuple(
            submitter,
            schema_id,
            policy_id,
            object_hash,
            external_ref,
            billable_bytes
        )
    ).send();

    consume_entitlement_kib(entitlement.entitlement_id, billable_kib);
}

void verification_billing::submitroot(
    const name& payer,
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& root_hash,
    uint32_t leaf_count,
    const checksum256& manifest_hash,
    const checksum256& external_ref,
    uint64_t billable_bytes
) {
    check(is_account(payer), "payer account does not exist");
    check(is_account(submitter), "submitter account does not exist");
    check(leaf_count > 0, "leaf_count must be greater than zero");
    verification_validators::validate_nonzero_checksum(root_hash, "root_hash");
    verification_validators::validate_nonzero_checksum(manifest_hash, "manifest_hash");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");
    verification_validators::validate_billable_bytes(billable_bytes, "billable_bytes");
    require_auth(payer);
    require_contract_only_submitter(payer, submitter);

    const auto billable_kib = verification_validators::derive_billable_kib(billable_bytes);
    const auto entitlement = select_entitlement(payer, billable_kib);
    const auto config = get_billing_config();

    action(
        permission_level{get_self(), "active"_n},
        config.verification_account,
        "billbatch"_n,
        std::make_tuple(
            submitter,
            schema_id,
            policy_id,
            root_hash,
            leaf_count,
            manifest_hash,
            external_ref,
            billable_bytes
        )
    ).send();

    consume_entitlement_kib(entitlement.entitlement_id, billable_kib);
}

void verification_billing::cleanentls(uint32_t limit) {
    require_auth(get_self());
    check(limit > 0, "limit must be greater than zero");
    check(limit <= cleanup_limit_max, "limit exceeds cleanup maximum");

    entitlement_table entitlements(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());
    uint32_t removed = 0;

    auto itr = entitlements.begin();
    while (itr != entitlements.end() && removed < limit) {
        auto current = itr;
        ++itr;

        uint8_t desired_status = current->status;
        const bool has_expiry = current->expires_at.sec_since_epoch() > 0;
        if (has_expiry && current->expires_at <= now) {
            desired_status = entitlement_status_expired;
        } else if (current->kib_remaining == 0) {
            desired_status = entitlement_status_exhausted;
        } else {
            desired_status = entitlement_status_active;
        }

        if (desired_status != current->status) {
            entitlements.modify(current, get_self(), [&](auto& row) {
                row.status = desired_status;
                row.updated_at = now;
            });
            current = entitlements.find(current->entitlement_id);
            check(current != entitlements.end(), "entitlement disappeared during cleanup");
        }

        if (current->status == entitlement_status_active) {
            continue;
        }

        entitlements.erase(current);
        ++removed;
    }
}

void verification_billing::withdraw(
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

void verification_billing::ontransfer(const name& from, const name& to, const asset& quantity, const string& memo) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    verification_validators::validate_payment_price(quantity, "quantity");
    const auto parsed_purchase = parse_purchase_memo(memo);
    const auto purchase_kind = std::get<0>(parsed_purchase);
    const auto payer = std::get<1>(parsed_purchase);
    const auto code = std::get<2>(parsed_purchase);
    check(from == payer, "transfer payer must match purchase memo payer");
    require_accepted_token(get_first_receiver(), quantity.symbol.code());

    entitlement_table entitlements(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());

    if (purchase_kind == "plan") {
        plan_table plans(get_self(), get_self().value);
        auto by_code = plans.get_index<"bycode"_n>();
        auto existing = by_code.find(code.value);
        check(existing != by_code.end(), "plan code is not configured");
        check(existing->active, "plan is inactive");
        check(existing->token_contract == get_first_receiver(), "plan token contract does not match payment");
        check(existing->price == quantity, "plan payment must match exact configured price");

        entitlements.emplace(get_self(), [&](auto& row) {
            row.entitlement_id = next_entitlement_id();
            row.payer = payer;
            row.kind = entitlement_kind_plan;
            row.plan_id = existing->plan_id;
            row.pack_id = 0;
            row.kib_remaining = existing->included_kib;
            row.active_from = now;
            row.expires_at = time_point_sec(now.sec_since_epoch() + existing->duration_sec);
            row.status = entitlement_status_active;
            row.updated_at = now;
        });
        return;
    }

    if (purchase_kind == "pack") {
        pack_table packs(get_self(), get_self().value);
        auto by_code = packs.get_index<"bycode"_n>();
        auto existing = by_code.find(code.value);
        check(existing != by_code.end(), "pack code is not configured");
        check(existing->active, "pack is inactive");
        check(existing->token_contract == get_first_receiver(), "pack token contract does not match payment");
        check(existing->price == quantity, "pack payment must match exact configured price");

        entitlements.emplace(get_self(), [&](auto& row) {
            row.entitlement_id = next_entitlement_id();
            row.payer = payer;
            row.kind = entitlement_kind_pack;
            row.plan_id = 0;
            row.pack_id = existing->pack_id;
            row.kib_remaining = existing->included_kib;
            row.active_from = now;
            row.expires_at = time_point_sec{};
            row.status = entitlement_status_active;
            row.updated_at = now;
        });
        return;
    }

    check(false, "enterprise purchase kind must be plan or pack");
}

uint128_t verification_billing::make_payment_key(const name& token_contract, const symbol_code& token_symbol) const {
    return (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.raw();
}

verification_billing::accepted_token_row verification_billing::require_accepted_token(
    const name& token_contract,
    const symbol_code& token_symbol
) const {
    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const auto key = make_payment_key(token_contract, token_symbol);
    auto existing = by_token.find(key);
    check(existing != by_token.end(), "enterprise billing token is not configured");
    check(existing->enabled, "enterprise billing token is disabled");
    return *existing;
}

verification_billing::plan_row verification_billing::require_plan_by_id(uint64_t plan_id) const {
    verification_validators::validate_registry_id(plan_id, "plan_id");
    plan_table plans(get_self(), get_self().value);
    auto existing = plans.find(plan_id);
    check(existing != plans.end(), "plan does not exist");
    return *existing;
}

verification_billing::pack_row verification_billing::require_pack_by_id(uint64_t pack_id) const {
    verification_validators::validate_registry_id(pack_id, "pack_id");
    pack_table packs(get_self(), get_self().value);
    auto existing = packs.find(pack_id);
    check(existing != packs.end(), "pack does not exist");
    return *existing;
}

uint64_t verification_billing::next_token_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    const auto allocated = state.next_token_id == 0 ? 1 : state.next_token_id;
    state.next_token_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_billing::next_plan_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    const auto allocated = state.next_plan_id == 0 ? 1 : state.next_plan_id;
    state.next_plan_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_billing::next_pack_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    const auto allocated = state.next_pack_id == 0 ? 1 : state.next_pack_id;
    state.next_pack_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_billing::next_entitlement_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    const auto allocated = state.next_entitlement_id == 0 ? 1 : state.next_entitlement_id;
    state.next_entitlement_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

verification_billing::billing_config verification_billing::get_billing_config() const {
    billing_config_singleton config(get_self(), get_self().value);
    return config.exists() ? config.get() : billing_config{};
}

std::tuple<string, name, name> verification_billing::parse_purchase_memo(const string& memo) const {
    const auto first = memo.find('|');
    const auto second = memo.find('|', first == string::npos ? first : first + 1);

    check(
        first != string::npos &&
        second != string::npos &&
        memo.find('|', second + 1) == string::npos,
        "enterprise memo format must be kind|payer|code"
    );

    const auto kind = memo.substr(0, first);
    const auto payer_value = memo.substr(first + 1, second - first - 1);
    const auto code_value = memo.substr(second + 1);

    verification_validators::validate_printable_ascii_text(kind, 16, "kind", false);
    verification_validators::validate_printable_ascii_text(payer_value, 13, "payer", false);
    verification_validators::validate_printable_ascii_text(code_value, 13, "code", false);

    const name payer = name(payer_value);
    const name code = name(code_value);
    check(payer.value > 0, "payer in enterprise memo is invalid");
    check(code.value > 0, "code in enterprise memo is invalid");
    check(is_account(payer), "payer account does not exist");

    return std::make_tuple(kind, payer, code);
}

verification_billing::entitlement_row verification_billing::select_entitlement(
    const name& payer,
    uint64_t required_kib
) {
    entitlement_table entitlements(get_self(), get_self().value);
    auto by_payer = entitlements.get_index<"bypayer"_n>();
    const auto now = time_point_sec(current_time_point());
    bool found_candidate = false;
    entitlement_row candidate{};

    auto prefers = [](const entitlement_row& lhs, const entitlement_row& rhs) {
        const bool lhs_has_expiry = lhs.expires_at.sec_since_epoch() > 0;
        const bool rhs_has_expiry = rhs.expires_at.sec_since_epoch() > 0;

        if (lhs_has_expiry != rhs_has_expiry) {
            return lhs_has_expiry;
        }

        if (lhs_has_expiry && rhs_has_expiry && lhs.expires_at != rhs.expires_at) {
            return lhs.expires_at < rhs.expires_at;
        }

        return lhs.entitlement_id < rhs.entitlement_id;
    };

    for (auto itr = by_payer.find(payer.value); itr != by_payer.end() && itr->payer == payer; ) {
        auto current = itr;
        ++itr;

        if (current->status != entitlement_status_active) {
            continue;
        }

        const bool has_expiry = current->expires_at.sec_since_epoch() > 0;
        if (has_expiry && current->expires_at <= now) {
            by_payer.modify(current, get_self(), [&](auto& row) {
                row.status = entitlement_status_expired;
                row.updated_at = now;
            });
            continue;
        }

        if (current->kib_remaining == 0) {
            by_payer.modify(current, get_self(), [&](auto& row) {
                row.status = entitlement_status_exhausted;
                row.updated_at = now;
            });
            continue;
        }

        if (current->kib_remaining < required_kib) {
            continue;
        }

        if (!found_candidate || prefers(*current, candidate)) {
            candidate = *current;
            found_candidate = true;
        }
    }

    check(found_candidate, "payer does not have active enterprise entitlement with enough remaining KiB");
    return candidate;
}

void verification_billing::consume_entitlement_kib(uint64_t entitlement_id, uint64_t required_kib) {
    entitlement_table entitlements(get_self(), get_self().value);
    auto entitlement = entitlements.find(entitlement_id);
    check(entitlement != entitlements.end(), "enterprise entitlement does not exist");
    check(entitlement->status == entitlement_status_active, "enterprise entitlement is not active");

    const auto now = time_point_sec(current_time_point());
    const bool has_expiry = entitlement->expires_at.sec_since_epoch() > 0;
    if (has_expiry && entitlement->expires_at <= now) {
        entitlements.modify(entitlement, get_self(), [&](auto& row) {
            row.status = entitlement_status_expired;
            row.updated_at = now;
        });
        check(false, "enterprise entitlement has expired");
    }

    check(entitlement->kib_remaining >= required_kib, "enterprise entitlement has insufficient remaining KiB");
    entitlements.modify(entitlement, get_self(), [&](auto& row) {
        row.kib_remaining -= required_kib;
        if (row.kib_remaining == 0) {
            row.status = entitlement_status_exhausted;
        }
        row.updated_at = now;
    });
}

void verification_billing::require_contract_only_submitter(const name& payer, const name& submitter) const {
    check(
        payer == submitter,
        "contract-only enterprise flow requires submitter to match payer"
    );
}
