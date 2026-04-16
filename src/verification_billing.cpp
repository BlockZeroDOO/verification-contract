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
    uint64_t single_quota,
    uint64_t batch_quota
) {
    eosio::check(plan_code.value > 0, "plan_code is invalid");
    verification_validators::validate_payment_price(price, "price");
    eosio::check(duration_sec > 0, "duration_sec must be greater than zero");
    eosio::check(single_quota > 0 || batch_quota > 0, "plan must provide at least one quota");
}

void validate_pack_config(
    const eosio::name& pack_code,
    const eosio::asset& price,
    uint64_t single_units,
    uint64_t batch_units
) {
    eosio::check(pack_code.value > 0, "pack_code is invalid");
    verification_validators::validate_payment_price(price, "price");
    eosio::check(single_units > 0 || batch_units > 0, "pack must provide at least one usage unit");
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
    uint64_t single_quota,
    uint64_t batch_quota,
    bool active
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_plan_config(plan_code, price, duration_sec, single_quota, batch_quota);
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
            row.single_quota = single_quota;
            row.batch_quota = batch_quota;
            row.active = active;
            row.updated_at = now;
        });
        return;
    }

    by_code.modify(existing, get_self(), [&](auto& row) {
        row.token_contract = token_contract;
        row.price = price;
        row.duration_sec = duration_sec;
        row.single_quota = single_quota;
        row.batch_quota = batch_quota;
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
    uint64_t single_units,
    uint64_t batch_units,
    bool active
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    validate_pack_config(pack_code, price, single_units, batch_units);
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
            row.single_units = single_units;
            row.batch_units = batch_units;
            row.active = active;
            row.updated_at = now;
        });
        return;
    }

    by_code.modify(existing, get_self(), [&](auto& row) {
        row.token_contract = token_contract;
        row.price = price;
        row.single_units = single_units;
        row.batch_units = batch_units;
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

void verification_billing::grantdelegate(const name& payer, const name& submitter) {
    check(is_account(payer), "payer account does not exist");
    check(is_account(submitter), "submitter account does not exist");
    check(has_auth(payer) || has_auth(get_self()), "missing required authority of payer or contract");

    delegate_table delegates(get_self(), get_self().value);
    auto by_pair = delegates.get_index<"bypair"_n>();
    const auto pair_key = (static_cast<uint128_t>(payer.value) << 64) | submitter.value;
    auto existing = by_pair.find(pair_key);
    const auto now = time_point_sec(current_time_point());

    if (existing == by_pair.end()) {
        delegates.emplace(get_self(), [&](auto& row) {
            row.delegate_id = next_delegate_id();
            row.payer = payer;
            row.submitter = submitter;
            row.enabled = true;
            row.created_at = now;
            row.updated_at = now;
        });
        return;
    }

    by_pair.modify(existing, get_self(), [&](auto& row) {
        row.enabled = true;
        row.updated_at = now;
    });
}

void verification_billing::revokedeleg(const name& payer, const name& submitter) {
    check(has_auth(payer) || has_auth(get_self()), "missing required authority of payer or contract");

    delegate_table delegates(get_self(), get_self().value);
    auto by_pair = delegates.get_index<"bypair"_n>();
    const auto pair_key = (static_cast<uint128_t>(payer.value) << 64) | submitter.value;
    auto existing = by_pair.find(pair_key);
    check(existing != by_pair.end(), "delegate mapping does not exist");

    by_pair.modify(existing, get_self(), [&](auto& row) {
        row.enabled = false;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void verification_billing::use(const name& payer, const name& submitter, uint8_t mode, const checksum256& external_ref) {
    check(is_account(payer), "payer account does not exist");
    check(is_account(submitter), "submitter account does not exist");
    check(mode == enterprise_mode_single || mode == enterprise_mode_batch, "unsupported enterprise usage mode");
    verification_validators::validate_nonzero_checksum(external_ref, "external_ref");
    check(
        has_auth(submitter) || has_auth(payer),
        "missing required authority of submitter or payer"
    );

    if (submitter != payer) {
        check(has_delegate_permission(payer, submitter), "submitter is not delegated by payer");
    }

    const auto request_key = verification_common::compute_request_key(submitter, external_ref);
    usage_auth_table usage_auths(get_self(), get_self().value);
    auto by_request = usage_auths.get_index<"byrequest"_n>();
    check(by_request.find(request_key) == by_request.end(), "enterprise usage authorization already exists for request");

    const auto allocated = allocate_usage(payer, mode);
    const auto now = time_point_sec(current_time_point());
    usage_auths.emplace(get_self(), [&](auto& row) {
        row.auth_id = next_usageauth_id();
        row.payer = payer;
        row.submitter = submitter;
        row.mode = mode;
        row.request_key = request_key;
        row.entitlement_id = allocated.entitlement_id;
        row.consumed = false;
        row.created_at = now;
        row.consumed_at = time_point_sec{};
        row.expires_at = time_point_sec(now.sec_since_epoch() + usage_auth_ttl_sec);
    });
}

void verification_billing::consume(uint64_t auth_id) {
    check(
        has_auth(get_self()) || has_auth("verif"_n),
        "missing required authority of billing contract or verif"
    );
    verification_validators::validate_registry_id(auth_id, "auth_id");

    usage_auth_table usage_auths(get_self(), get_self().value);
    auto existing = usage_auths.find(auth_id);
    check(existing != usage_auths.end(), "enterprise usage authorization does not exist");
    check(!existing->consumed, "enterprise usage authorization is already consumed");

    usage_auths.modify(existing, get_self(), [&](auto& row) {
        row.consumed = true;
        row.consumed_at = time_point_sec(current_time_point());
    });
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
            row.single_remaining = existing->single_quota;
            row.batch_remaining = existing->batch_quota;
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
            row.single_remaining = existing->single_units;
            row.batch_remaining = existing->batch_units;
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

bool verification_billing::has_delegate_permission(const name& payer, const name& submitter) const {
    delegate_table delegates(get_self(), get_self().value);
    auto by_pair = delegates.get_index<"bypair"_n>();
    const auto pair_key = (static_cast<uint128_t>(payer.value) << 64) | submitter.value;
    auto existing = by_pair.find(pair_key);
    return existing != by_pair.end() && existing->enabled;
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

uint64_t verification_billing::next_delegate_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    const auto allocated = state.next_delegate_id == 0 ? 1 : state.next_delegate_id;
    state.next_delegate_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
}

uint64_t verification_billing::next_usageauth_id() {
    counter_singleton counters(get_self(), get_self().value);
    auto state = counters.exists() ? counters.get() : counter_state{};
    const auto allocated = state.next_usageauth_id == 0 ? 1 : state.next_usageauth_id;
    state.next_usageauth_id = allocated + 1;
    counters.set(state, get_self());
    return allocated;
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

verification_billing::entitlement_row verification_billing::allocate_usage(const name& payer, uint8_t mode) {
    entitlement_table entitlements(get_self(), get_self().value);
    const auto now = time_point_sec(current_time_point());

    for (auto itr = entitlements.begin(); itr != entitlements.end(); ++itr) {
        if (itr->payer != payer || itr->status != entitlement_status_active) {
            continue;
        }

        const bool has_expiry = itr->expires_at.sec_since_epoch() > 0;
        if (has_expiry && itr->expires_at <= now) {
            entitlements.modify(itr, get_self(), [&](auto& row) {
                row.status = entitlement_status_expired;
                row.updated_at = now;
            });
            continue;
        }

        const bool can_consume = mode == enterprise_mode_single
            ? itr->single_remaining > 0
            : itr->batch_remaining > 0;
        if (!can_consume) {
            if (itr->single_remaining == 0 && itr->batch_remaining == 0) {
                entitlements.modify(itr, get_self(), [&](auto& row) {
                    row.status = entitlement_status_exhausted;
                    row.updated_at = now;
                });
            }
            continue;
        }

        const auto entitlement_id = itr->entitlement_id;
        entitlements.modify(itr, get_self(), [&](auto& row) {
            if (mode == enterprise_mode_single) {
                --row.single_remaining;
            } else {
                --row.batch_remaining;
            }
            if (row.single_remaining == 0 && row.batch_remaining == 0) {
                row.status = entitlement_status_exhausted;
            }
            row.updated_at = now;
        });

        auto updated = entitlements.find(entitlement_id);
        check(updated != entitlements.end(), "allocated entitlement disappeared");
        return *updated;
    }

    check(false, "payer does not have active enterprise entitlement for requested mode");
    return entitlement_row{};
}
