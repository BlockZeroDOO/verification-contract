#include <dfs.hpp>

#include <eosio/dispatcher.hpp>

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
}  // namespace

checksum256 dfs::compute_text_key(const string& value) {
    return sha256(value.data(), value.size());
}

checksum256 dfs::compute_balance_key(
    const name& owner_account,
    const name& token_contract,
    const symbol_code& symbol_code
) {
    const string composite = owner_account.to_string() + "|" + token_contract.to_string() + "|" + symbol_code.to_string();
    return compute_text_key(composite);
}

void dfs::regnode(
    const string& node_id,
    const name& owner_account,
    const name& role,
    const string& region,
    uint32_t weight,
    const string& metadata_endpoint,
    const string& storage_endpoint,
    const string& node_public_key
) {
    require_auth(owner_account);
    check(is_account(owner_account), "owner_account does not exist");
    validate_role(role);
    validate_printable_ascii_text(node_id, 128, "node_id", false);
    validate_printable_ascii_text(region, 64, "region", true);
    validate_endpoint(metadata_endpoint, "metadata_endpoint", role == role_metadata || role == role_both);
    validate_endpoint(storage_endpoint, "storage_endpoint", role == role_storage || role == role_both);
    validate_node_public_key(node_public_key);
    check(weight > 0, "weight must be positive");

    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    check(by_node.find(compute_text_key(node_id)) == by_node.end(), "node_id is already registered");

    uint64_t next_id = nodes.available_primary_key();
    if (next_id == 0) {
        next_id = 1;
    }

    const time_point_sec now = time_point_sec(current_time_point());
    nodes.emplace(owner_account, [&](auto& row) {
        row.row_id = next_id;
        row.node_id = node_id;
        row.owner_account = owner_account;
        row.role = role;
        row.region = region;
        row.weight = weight;
        row.metadata_endpoint = metadata_endpoint;
        row.storage_endpoint = storage_endpoint;
        row.node_public_key = node_public_key;
        row.status = status_active;
        row.registered_at = now;
        row.updated_at = now;
    });
}

void dfs::updatenode(
    const string& node_id,
    const name& role,
    const string& region,
    uint32_t weight,
    const string& metadata_endpoint,
    const string& storage_endpoint,
    const string& node_public_key
) {
    validate_role(role);
    validate_printable_ascii_text(region, 64, "region", true);
    validate_endpoint(metadata_endpoint, "metadata_endpoint", role == role_metadata || role == role_both);
    validate_endpoint(storage_endpoint, "storage_endpoint", role == role_storage || role == role_both);
    validate_node_public_key(node_public_key);
    check(weight > 0, "weight must be positive");

    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    auto node_itr = by_node.find(compute_text_key(node_id));
    check(node_itr != by_node.end(), "node_id is not registered");
    require_auth(node_itr->owner_account);
    check(node_itr->status != status_retired, "retired node cannot be updated");

    by_node.modify(node_itr, node_itr->owner_account, [&](auto& row) {
        row.role = role;
        row.region = region;
        row.weight = weight;
        row.metadata_endpoint = metadata_endpoint;
        row.storage_endpoint = storage_endpoint;
        row.node_public_key = node_public_key;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void dfs::suspendnode(const string& node_id) {
    require_auth(get_self());

    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    auto node_itr = by_node.find(compute_text_key(node_id));
    check(node_itr != by_node.end(), "node_id is not registered");

    by_node.modify(node_itr, node_itr->owner_account, [&](auto& row) {
        row.status = status_suspended;
        row.updated_at = time_point_sec(current_time_point());
    });

    stake_table stakes(get_self(), get_self().value);
    auto by_stake_node = stakes.get_index<"bynodeid"_n>();
    auto stake_itr = by_stake_node.find(compute_text_key(node_id));
    if (stake_itr != by_stake_node.end()) {
        by_stake_node.modify(stake_itr, stake_itr->owner_account, [&](auto& row) {
            row.status = status_suspended;
            row.updated_at = time_point_sec(current_time_point());
        });
    }
}

void dfs::retirenode(const string& node_id) {
    require_auth(get_self());

    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    auto node_itr = by_node.find(compute_text_key(node_id));
    check(node_itr != by_node.end(), "node_id is not registered");

    by_node.modify(node_itr, node_itr->owner_account, [&](auto& row) {
        row.status = status_retired;
        row.updated_at = time_point_sec(current_time_point());
    });
}

void dfs::requestunstk(const string& node_id) {
    pricing_policy policy = get_policy();

    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    auto node_itr = by_node.find(compute_text_key(node_id));
    check(node_itr != by_node.end(), "node_id is not registered");
    require_auth(node_itr->owner_account);

    stake_table stakes(get_self(), get_self().value);
    auto by_stake_node = stakes.get_index<"bynodeid"_n>();
    auto stake_itr = by_stake_node.find(compute_text_key(node_id));
    check(stake_itr != by_stake_node.end(), "stake does not exist for node");
    check(stake_itr->status == status_active, "stake is not active");
    check(stake_itr->quantity.amount > 0, "stake quantity must be positive");

    const time_point_sec now = time_point_sec(current_time_point());
    by_stake_node.modify(stake_itr, stake_itr->owner_account, [&](auto& row) {
        row.status = stake_pending_unstake;
        row.cooldown_ends_at = time_point_sec(now.sec_since_epoch() + policy.unstake_cooldown_sec);
        row.updated_at = now;
    });
}

void dfs::withdrawstk(const string& node_id) {
    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    auto node_itr = by_node.find(compute_text_key(node_id));
    check(node_itr != by_node.end(), "node_id is not registered");
    require_auth(node_itr->owner_account);

    stake_table stakes(get_self(), get_self().value);
    auto by_stake_node = stakes.get_index<"bynodeid"_n>();
    auto stake_itr = by_stake_node.find(compute_text_key(node_id));
    check(stake_itr != by_stake_node.end(), "stake does not exist for node");
    check(stake_itr->status == stake_pending_unstake, "stake is not pending unstake");

    const time_point_sec now = time_point_sec(current_time_point());
    check(stake_itr->cooldown_ends_at <= now, "unstake cooldown is still active");

    const asset quantity = stake_itr->quantity;
    check(quantity.amount > 0, "stake quantity must be positive");

    action(
        permission_level{get_self(), "active"_n},
        stake_itr->token_contract,
        "transfer"_n,
        std::make_tuple(get_self(), node_itr->owner_account, quantity, string("dfs withdraw stake"))
    ).send();

    by_stake_node.modify(stake_itr, stake_itr->owner_account, [&](auto& row) {
        row.quantity.amount = 0;
        row.status = stake_withdrawn;
        row.cooldown_ends_at = time_point_sec();
        row.updated_at = now;
    });
}

void dfs::setprice(
    const string& node_id,
    const name& token_contract,
    const asset& unit_price,
    const string& pricing_unit
) {
    validate_nonnegative_asset(unit_price, "unit_price");
    check(unit_price.amount > 0, "unit_price must be positive");
    validate_printable_ascii_text(pricing_unit, 32, "pricing_unit", false);
    require_enabled_token(token_contract, unit_price.symbol);

    node_table nodes(get_self(), get_self().value);
    auto by_node = nodes.get_index<"bynodeid"_n>();
    auto node_itr = by_node.find(compute_text_key(node_id));
    check(node_itr != by_node.end(), "node_id is not registered");
    require_auth(node_itr->owner_account);
    check(node_itr->status == status_active, "node must be active to publish price");
    check(
        node_itr->role == role_storage || node_itr->role == role_both,
        "only storage-capable nodes may publish price offers"
    );

    price_offer_table offers(get_self(), get_self().value);
    auto by_offer_node = offers.get_index<"bynodeid"_n>();
    auto offer_itr = by_offer_node.find(compute_text_key(node_id));
    const time_point_sec now = time_point_sec(current_time_point());

    if (offer_itr == by_offer_node.end()) {
        offers.emplace(node_itr->owner_account, [&](auto& row) {
            row.row_id = offers.available_primary_key();
            if (row.row_id == 0) {
                row.row_id = 1;
            }
            row.node_id = node_id;
            row.owner_account = node_itr->owner_account;
            row.token_contract = token_contract;
            row.unit_price = unit_price;
            row.pricing_unit = pricing_unit;
            row.effective_from = now;
            row.updated_at = now;
        });
        return;
    }

    by_offer_node.modify(offer_itr, node_itr->owner_account, [&](auto& row) {
        row.owner_account = node_itr->owner_account;
        row.token_contract = token_contract;
        row.unit_price = unit_price;
        row.pricing_unit = pricing_unit;
        row.effective_from = now;
        row.updated_at = now;
    });
}

void dfs::settoken(
    const name& token_contract,
    const symbol& token_symbol,
    bool enabled
) {
    require_auth(get_self());
    check(is_account(token_contract), "token_contract does not exist");
    check(token_symbol.is_valid(), "token_symbol is invalid");
    validate_token_contract_stat(token_contract, token_symbol);

    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const uint128_t key = (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.code().raw();
    auto token_itr = by_token.find(key);
    const time_point_sec now = time_point_sec(current_time_point());

    if (token_itr == by_token.end()) {
        tokens.emplace(get_self(), [&](auto& row) {
            row.config_id = tokens.available_primary_key();
            if (row.config_id == 0) {
                row.config_id = 1;
            }
            row.token_contract = token_contract;
            row.token_symbol = token_symbol;
            row.enabled = enabled;
            row.updated_at = now;
        });
        return;
    }

    by_token.modify(token_itr, get_self(), [&](auto& row) {
        row.enabled = enabled;
        row.updated_at = now;
    });
}

void dfs::rmtoken(
    const name& token_contract,
    const symbol& token_symbol
) {
    require_auth(get_self());
    check(token_symbol.is_valid(), "token_symbol is invalid");

    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const uint128_t key = (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.code().raw();
    auto token_itr = by_token.find(key);
    check(token_itr != by_token.end(), "accepted token is not configured");

    balance_table balances(get_self(), get_self().value);
    for (auto itr = balances.begin(); itr != balances.end(); ++itr) {
        if (
            itr->token_contract == token_contract &&
            itr->available_quantity.symbol == token_symbol &&
            itr->available_quantity.amount > 0
        ) {
            check(false, "cannot remove token with live claimable balances");
        }
    }

    price_offer_table offers(get_self(), get_self().value);
    for (auto itr = offers.begin(); itr != offers.end(); ++itr) {
        if (itr->token_contract == token_contract && itr->unit_price.symbol == token_symbol) {
            check(false, "cannot remove token with live price offers");
        }
    }

    receipt_table receipts(get_self(), get_self().value);
    for (auto itr = receipts.begin(); itr != receipts.end(); ++itr) {
        if (
            itr->token_contract == token_contract &&
            itr->quantity.symbol == token_symbol &&
            itr->status == receipt_received
        ) {
            check(false, "cannot remove token with unsettled custody receipts");
        }
    }

    by_token.erase(token_itr);
}

void dfs::setpolicy(
    const name& stake_token_contract,
    const asset& stake_minimum,
    const name& consensus_algorithm,
    const name& settlement_authority,
    uint32_t max_price_age_sec,
    uint16_t min_eligible_price_nodes,
    uint16_t protocol_fee_bps,
    uint32_t unstake_cooldown_sec
) {
    require_auth(get_self());
    check(is_account(stake_token_contract), "stake_token_contract does not exist");
    check(is_account(settlement_authority), "settlement_authority does not exist");
    validate_nonnegative_asset(stake_minimum, "stake_minimum");
    check(stake_minimum.amount > 0, "stake_minimum must be positive");
    check(consensus_algorithm.value != 0, "consensus_algorithm is required");
    check(max_price_age_sec > 0, "max_price_age_sec must be positive");
    check(min_eligible_price_nodes > 0, "min_eligible_price_nodes must be positive");
    check(protocol_fee_bps <= 10'000, "protocol_fee_bps cannot exceed 10000");
    check(unstake_cooldown_sec > 0, "unstake_cooldown_sec must be positive");
    validate_token_contract_stat(stake_token_contract, stake_minimum.symbol);

    pricing_policy_singleton policy_store(get_self(), get_self().value);
    if (policy_store.exists()) {
        const pricing_policy current_policy = policy_store.get();
        stake_table stakes(get_self(), get_self().value);
        bool has_live_stakes = false;
        for (auto itr = stakes.begin(); itr != stakes.end(); ++itr) {
            if (
                itr->quantity.amount > 0 &&
                (itr->status == status_active || itr->status == stake_pending_unstake || itr->status == status_suspended)
            ) {
                has_live_stakes = true;
                break;
            }
        }

        if (has_live_stakes) {
            check(
                current_policy.stake_token_contract == stake_token_contract,
                "cannot change stake_token_contract while live stakes exist"
            );
            check(
                current_policy.stake_minimum.symbol == stake_minimum.symbol,
                "cannot change stake token symbol while live stakes exist"
            );
            check(
                current_policy.stake_minimum == stake_minimum,
                "cannot change stake_minimum while live stakes exist"
            );
        }
    }

    pricing_policy policy;
    policy.stake_token_contract = stake_token_contract;
    policy.stake_minimum = stake_minimum;
    policy.consensus_algorithm = consensus_algorithm;
    policy.settlement_authority = settlement_authority;
    policy.max_price_age_sec = max_price_age_sec;
    policy.min_eligible_price_nodes = min_eligible_price_nodes;
    policy.protocol_fee_bps = protocol_fee_bps;
    policy.unstake_cooldown_sec = unstake_cooldown_sec;
    policy.updated_at = time_point_sec(current_time_point());
    policy_store.set(policy, get_self());
}

void dfs::claimrevenue(
    const name& owner_account,
    const name& token_contract,
    const asset& quantity
) {
    require_auth(owner_account);
    check(is_account(owner_account), "owner_account does not exist");
    check(is_account(token_contract), "token_contract does not exist");
    validate_nonnegative_asset(quantity, "quantity");
    check(quantity.amount > 0, "quantity must be positive");

    balance_table balances(get_self(), get_self().value);
    auto balance_itr = find_balance(balances, owner_account, token_contract, quantity.symbol.code());
    check(balance_itr != balances.end(), "revenue balance does not exist");
    check(balance_itr->available_quantity.symbol == quantity.symbol, "quantity symbol does not match revenue balance");
    check(balance_itr->available_quantity.amount >= quantity.amount, "insufficient claimable revenue");

    const asset remaining = asset(balance_itr->available_quantity.amount - quantity.amount, quantity.symbol);
    balances.modify(balance_itr, get_self(), [&](auto& row) {
        row.available_quantity = remaining;
        row.updated_at = time_point_sec(current_time_point());
    });

    action(
        permission_level{get_self(), "active"_n},
        token_contract,
        "transfer"_n,
        std::make_tuple(get_self(), owner_account, quantity, string("dfs revenue claim"))
    ).send();
}

void dfs::settle(
    const string& settlement_id,
    const string& file_id,
    const string& payment_reference,
    const string& payment_txid,
    const string& manifest_hash,
    const name& token_contract,
    const asset& gross_quantity,
    const asset& protocol_fee_quantity,
    const vector<payout_row>& payouts
) {
    const pricing_policy policy = get_policy();
    require_auth(policy.settlement_authority);
    check(is_account(token_contract), "token_contract does not exist");
    validate_printable_ascii_text(settlement_id, 128, "settlement_id", false);
    validate_printable_ascii_text(file_id, 128, "file_id", false);
    validate_printable_ascii_text(payment_reference, 128, "payment_reference", false);
    validate_printable_ascii_text(payment_txid, 128, "payment_txid", false);
    validate_printable_ascii_text(manifest_hash, 128, "manifest_hash", false);
    validate_nonnegative_asset(gross_quantity, "gross_quantity");
    validate_nonnegative_asset(protocol_fee_quantity, "protocol_fee_quantity");
    check(gross_quantity.amount > 0, "gross_quantity must be positive");
    check(protocol_fee_quantity.symbol == gross_quantity.symbol, "protocol_fee_quantity symbol mismatch");
    check(protocol_fee_quantity.amount <= gross_quantity.amount, "protocol_fee_quantity exceeds gross_quantity");

    settlement_table settlements(get_self(), get_self().value);
    auto by_settlement_id = settlements.get_index<"bysettleid"_n>();
    check(by_settlement_id.find(compute_text_key(settlement_id)) == by_settlement_id.end(), "settlement_id already exists");
    auto by_payment_txid = settlements.get_index<"bypaytxid"_n>();
    check(by_payment_txid.find(compute_text_key(payment_txid)) == by_payment_txid.end(), "payment_txid is already settled");

    receipt_table receipts(get_self(), get_self().value);
    auto receipt_itr = find_receipt(receipts, payment_reference);
    check(receipt_itr != receipts.end(), "storage payment receipt does not exist");
    check(receipt_itr->receipt_kind == receipt_storage, "receipt is not a storage payment");
    check(receipt_itr->status == receipt_received, "storage payment receipt is not available for settlement");
    check(receipt_itr->manifest_hash == manifest_hash, "manifest_hash does not match storage payment receipt");
    check(receipt_itr->token_contract == token_contract, "token_contract does not match storage payment receipt");
    check(receipt_itr->quantity == gross_quantity, "gross_quantity does not match storage payment receipt");
    check(receipt_itr->distributed_quantity.amount == 0, "storage payment receipt already has distributed quantity");

    asset distributed_quantity = asset(0, gross_quantity.symbol);
    for (const auto& payout : payouts) {
        check(is_account(payout.owner_account), "payout owner_account does not exist");
        validate_nonnegative_asset(payout.quantity, "payout quantity");
        check(payout.quantity.amount > 0, "payout quantity must be positive");
        check(payout.quantity.symbol == gross_quantity.symbol, "payout quantity symbol mismatch");
        distributed_quantity += payout.quantity;
    }

    check(
        distributed_quantity.amount + protocol_fee_quantity.amount <= gross_quantity.amount,
        "distributed quantity plus protocol fee exceeds gross quantity"
    );
    check(
        distributed_quantity.amount + protocol_fee_quantity.amount == gross_quantity.amount,
        "distributed quantity plus protocol fee must exactly match gross quantity"
    );

    balance_table balances(get_self(), get_self().value);
    const time_point_sec now = time_point_sec(current_time_point());
    for (const auto& payout : payouts) {
        auto balance_itr = find_balance(balances, payout.owner_account, token_contract, payout.quantity.symbol.code());
        if (balance_itr == balances.end()) {
            balances.emplace(get_self(), [&](auto& row) {
                row.row_id = balances.available_primary_key();
                if (row.row_id == 0) {
                    row.row_id = 1;
                }
                row.owner_account = payout.owner_account;
                row.token_contract = token_contract;
                row.available_quantity = payout.quantity;
                row.updated_at = now;
            });
            continue;
        }

        balances.modify(balance_itr, get_self(), [&](auto& row) {
            row.available_quantity += payout.quantity;
            row.updated_at = now;
        });
    }

    settlements.emplace(get_self(), [&](auto& row) {
        row.row_id = settlements.available_primary_key();
        if (row.row_id == 0) {
            row.row_id = 1;
        }
        row.settlement_id = settlement_id;
        row.file_id = file_id;
        row.payment_reference = payment_reference;
        row.payment_txid = payment_txid;
        row.manifest_hash = manifest_hash;
        row.token_contract = token_contract;
        row.gross_quantity = gross_quantity;
        row.protocol_fee_quantity = protocol_fee_quantity;
        row.distributed_quantity = distributed_quantity;
        row.status = settlement_complete;
        row.settled_at = now;
    });

    receipts.modify(receipt_itr, get_self(), [&](auto& row) {
        row.distributed_quantity = distributed_quantity;
        row.status = receipt_settled;
        row.updated_at = now;
    });
}

void dfs::ontransfer(
    const name& from,
    const name& to,
    const asset& quantity,
    const string& memo
) {
    if (to != get_self() || from == get_self()) {
        return;
    }

    check(quantity.amount > 0, "transfer quantity must be positive");

    auto [is_stake_deposit, node_id] = parse_stake_memo(memo);
    if (is_stake_deposit) {
        pricing_policy policy = get_policy();
        check(get_first_receiver() == policy.stake_token_contract, "stake deposit token contract does not match policy");
        check(quantity.symbol == policy.stake_minimum.symbol, "stake deposit symbol does not match policy");

        node_table nodes(get_self(), get_self().value);
        auto by_node = nodes.get_index<"bynodeid"_n>();
        auto node_itr = by_node.find(compute_text_key(node_id));
        check(node_itr != by_node.end(), "stake target node is not registered");
        check(node_itr->owner_account == from, "only the registered node owner may fund stake");
        check(node_itr->status != status_retired, "retired node cannot receive new stake");

        upsert_stake_after_deposit(
            node_id,
            node_itr->owner_account,
            get_first_receiver(),
            quantity,
            node_itr->status == status_suspended
        );
        return;
    }

    const auto storage_memo = parse_storage_memo(memo);
    const bool is_storage_payment = std::get<0>(storage_memo);
    const string payment_reference = std::get<1>(storage_memo);
    const string manifest_hash = std::get<2>(storage_memo);
    check(is_storage_payment, "unknown transfer memo type");
    require_enabled_token(get_first_receiver(), quantity.symbol);

    receipt_table receipts(get_self(), get_self().value);
    auto existing_receipt = find_receipt(receipts, payment_reference);
    check(existing_receipt == receipts.end(), "payment_reference already exists");
    const time_point_sec now = time_point_sec(current_time_point());

    receipts.emplace(get_self(), [&](auto& row) {
        row.row_id = receipts.available_primary_key();
        if (row.row_id == 0) {
            row.row_id = 1;
        }
        row.receipt_kind = receipt_storage;
        row.payment_reference = payment_reference;
        row.manifest_hash = manifest_hash;
        row.node_id = string();
        row.source_account = from;
        row.token_contract = get_first_receiver();
        row.quantity = quantity;
        row.distributed_quantity = asset(0, quantity.symbol);
        row.status = receipt_received;
        row.created_at = now;
        row.updated_at = now;
    });
}

dfs::pricing_policy dfs::get_policy() const {
    pricing_policy_singleton policy_store(get_self(), get_self().value);
    check(policy_store.exists(), "pricing policy is not configured");
    return policy_store.get();
}

dfs::accepted_token_row dfs::require_enabled_token(const name& token_contract, const symbol& token_symbol) const {
    accepted_token_table tokens(get_self(), get_self().value);
    auto by_token = tokens.get_index<"bytokensym"_n>();
    const uint128_t key = (static_cast<uint128_t>(token_contract.value) << 64) | token_symbol.code().raw();
    auto token_itr = by_token.find(key);
    check(token_itr != by_token.end(), "accepted token is not configured");
    check(token_itr->token_symbol == token_symbol, "token precision does not match accepted token configuration");
    check(token_itr->enabled, "accepted token is disabled");
    return *token_itr;
}

dfs::balance_table::const_iterator dfs::find_balance(
    balance_table& balances,
    const name& owner_account,
    const name& token_contract,
    const symbol_code& symbol_code
) {
    auto by_balance_key = balances.get_index<"bybalancekey"_n>();
    auto itr = by_balance_key.find(compute_balance_key(owner_account, token_contract, symbol_code));
    if (itr == by_balance_key.end()) {
        return balances.end();
    }
    return balances.iterator_to(*itr);
}

dfs::receipt_table::const_iterator dfs::find_receipt(receipt_table& receipts, const string& payment_reference) {
    auto by_payref = receipts.get_index<"bypayref"_n>();
    auto receipt_itr = by_payref.find(compute_text_key(payment_reference));
    if (receipt_itr == by_payref.end()) {
        return receipts.end();
    }
    return receipts.iterator_to(*receipt_itr);
}

tuple<bool, string> dfs::parse_stake_memo(const string& memo) const {
    static constexpr const char* prefix = "stake|";
    static constexpr size_t prefix_length = 6;
    if (memo.size() <= prefix_length || memo.compare(0, prefix_length, prefix) != 0) {
        return std::make_tuple(false, string());
    }

    const string node_id = memo.substr(prefix_length);
    validate_printable_ascii_text(node_id, 128, "stake memo node_id", false);
    return std::make_tuple(true, node_id);
}

tuple<bool, string, string> dfs::parse_storage_memo(const string& memo) const {
    static constexpr const char* prefix = "storage|";
    static constexpr size_t prefix_length = 8;
    if (memo.size() <= prefix_length || memo.compare(0, prefix_length, prefix) != 0) {
        return std::make_tuple(false, string(), string());
    }

    const string payload = memo.substr(prefix_length);
    const size_t separator = payload.find('|');
    check(separator != string::npos, "storage memo must contain payment_reference and manifest_hash");

    const string payment_reference = payload.substr(0, separator);
    const string manifest_hash = payload.substr(separator + 1);
    validate_printable_ascii_text(payment_reference, 128, "storage memo payment_reference", false);
    validate_printable_ascii_text(manifest_hash, 128, "storage memo manifest_hash", false);
    return std::make_tuple(true, payment_reference, manifest_hash);
}

void dfs::validate_role(const name& role) const {
    check(
        role == role_metadata || role == role_storage || role == role_both,
        "role must be metadata, storage, or both"
    );
}

void dfs::validate_node_status(const name& status) const {
    check(
        status == status_active || status == status_suspended || status == status_retired,
        "invalid node status"
    );
}

void dfs::validate_endpoint(const string& value, const char* field_name, bool required) const {
    validate_printable_ascii_text(value, 256, field_name, !required);
    if (value.empty()) {
        return;
    }

    check(
        value.rfind("http://", 0) == 0 || value.rfind("https://", 0) == 0,
        string(field_name) + " must start with http:// or https://"
    );
}

void dfs::validate_node_public_key(const string& node_public_key) const {
    validate_text(node_public_key, 2048, "node_public_key", false);

    const bool is_antelope_public_key =
        node_public_key.rfind("PUB_K1_", 0) == 0 ||
        node_public_key.rfind("PUB_R1_", 0) == 0 ||
        node_public_key.rfind("EOS", 0) == 0;

    if (is_antelope_public_key) {
        validate_printable_ascii_text(node_public_key, 256, "node_public_key", false);
        check(node_public_key.size() >= 10, "node_public_key is too short");
        return;
    }

    const bool has_pem_header = node_public_key.find("-----BEGIN PUBLIC KEY-----") != string::npos;
    const bool has_pem_footer = node_public_key.find("-----END PUBLIC KEY-----") != string::npos;
    check(
        has_pem_header && has_pem_footer,
        "node_public_key must be an Antelope public key or PEM BEGIN/END PUBLIC KEY block"
    );

    for (char ch : node_public_key) {
        const unsigned char code = static_cast<unsigned char>(ch);
        const bool is_pem_whitespace = code == '\n' || code == '\r';
        const bool is_printable_ascii = code >= 32 && code <= 126;
        check(
            is_pem_whitespace || is_printable_ascii,
            "node_public_key PEM must use printable ASCII characters"
        );
    }

    check(node_public_key.size() >= 64, "node_public_key PEM is too short");
}

void dfs::validate_text(
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

void dfs::validate_printable_ascii_text(
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

void dfs::validate_nonnegative_asset(const asset& quantity, const char* field_name) const {
    check(quantity.is_valid(), string(field_name) + " is invalid");
    check(quantity.amount >= 0, string(field_name) + " cannot be negative");
}

void dfs::upsert_stake_after_deposit(
    const string& node_id,
    const name& owner_account,
    const name& token_contract,
    const asset& quantity,
    bool node_is_suspended
) {
    stake_table stakes(get_self(), get_self().value);
    auto by_node = stakes.get_index<"bynodeid"_n>();
    auto stake_itr = by_node.find(compute_text_key(node_id));
    const time_point_sec now = time_point_sec(current_time_point());

    if (stake_itr == by_node.end()) {
        stakes.emplace(owner_account, [&](auto& row) {
            row.row_id = stakes.available_primary_key();
            if (row.row_id == 0) {
                row.row_id = 1;
            }
            row.node_id = node_id;
            row.owner_account = owner_account;
            row.token_contract = token_contract;
            row.quantity = quantity;
            row.status = node_is_suspended ? status_suspended : status_active;
            row.cooldown_ends_at = time_point_sec();
            row.updated_at = now;
        });
        return;
    }

    check(stake_itr->token_contract == token_contract, "stake token contract cannot change for an existing node stake");
    check(stake_itr->quantity.symbol == quantity.symbol, "stake symbol cannot change for an existing node stake");
    check(stake_itr->status != stake_pending_unstake, "cannot top up stake while unstake is pending");

    by_node.modify(stake_itr, owner_account, [&](auto& row) {
        row.quantity += quantity;
        row.status = node_is_suspended ? status_suspended : status_active;
        row.cooldown_ends_at = time_point_sec();
        row.updated_at = now;
    });
}

EOSIO_DISPATCH(
    dfs,
    (regnode)
    (updatenode)
    (suspendnode)
    (retirenode)
    (requestunstk)
    (withdrawstk)
    (setprice)
    (settoken)
    (rmtoken)
    (setpolicy)
    (claimrevenue)
    (settle)
)
