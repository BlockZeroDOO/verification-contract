#pragma once

#include <eosio/action.hpp>
#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>
#include <eosio/singleton.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <string>
#include <tuple>
#include <vector>

using namespace eosio;
using std::string;
using std::tuple;
using std::vector;

class [[eosio::contract("dfs")]] dfs : public contract {
public:
    using contract::contract;

    [[eosio::action]]
    void regnode(
        const string& node_id,
        const name& owner_account,
        const name& role,
        const string& region,
        uint32_t weight,
        const string& metadata_endpoint,
        const string& storage_endpoint,
        const string& node_public_key
    );

    [[eosio::action]]
    void updatenode(
        const string& node_id,
        const name& role,
        const string& region,
        uint32_t weight,
        const string& metadata_endpoint,
        const string& storage_endpoint,
        const string& node_public_key
    );

    [[eosio::action]]
    void suspendnode(const string& node_id);

    [[eosio::action]]
    void retirenode(const string& node_id);

    [[eosio::action]]
    void requestunstk(const string& node_id);

    [[eosio::action]]
    void withdrawstk(const string& node_id);

    [[eosio::action]]
    void setprice(
        const string& node_id,
        const name& token_contract,
        const asset& unit_price,
        const string& pricing_unit
    );

    [[eosio::action]]
    void settoken(
        const name& token_contract,
        const symbol& token_symbol,
        bool enabled
    );

    [[eosio::action]]
    void rmtoken(
        const name& token_contract,
        const symbol& token_symbol
    );

    [[eosio::action]]
    void setpolicy(
        const name& stake_token_contract,
        const asset& stake_minimum,
        const name& consensus_algorithm,
        const name& settlement_authority,
        uint32_t max_price_age_sec,
        uint16_t min_eligible_price_nodes,
        uint16_t protocol_fee_bps,
        uint32_t unstake_cooldown_sec
    );

    [[eosio::action]]
    void claimrevenue(
        const name& owner_account,
        const name& token_contract,
        const asset& quantity
    );

    struct payout_row {
        name owner_account;
        asset quantity;

        EOSLIB_SERIALIZE(payout_row, (owner_account)(quantity))
    };

    [[eosio::action]]
    void settle(
        const string& settlement_id,
        const string& file_id,
        const string& payment_reference,
        const string& payment_txid,
        const string& manifest_hash,
        const name& token_contract,
        const asset& gross_quantity,
        const asset& protocol_fee_quantity,
        const vector<payout_row>& payouts
    );

    [[eosio::on_notify("*::transfer")]]
    void ontransfer(
        const name& from,
        const name& to,
        const asset& quantity,
        const string& memo
    );

private:
    struct [[eosio::table("nodes")]] node_row {
        uint64_t row_id;
        string node_id;
        name owner_account;
        name role;
        string region;
        uint32_t weight;
        string metadata_endpoint;
        string storage_endpoint;
        string node_public_key;
        name status;
        time_point_sec registered_at;
        time_point_sec updated_at;

        uint64_t primary_key() const { return row_id; }
        checksum256 by_nodeid() const { return compute_text_key(node_id); }
        uint64_t by_owner() const { return owner_account.value; }
    };

    struct [[eosio::table("stakes")]] stake_row {
        uint64_t row_id;
        string node_id;
        name owner_account;
        name token_contract;
        asset quantity;
        name status;
        time_point_sec cooldown_ends_at;
        time_point_sec updated_at;

        uint64_t primary_key() const { return row_id; }
        checksum256 by_nodeid() const { return compute_text_key(node_id); }
        uint64_t by_owner() const { return owner_account.value; }
    };

    struct [[eosio::table("priceoffers")]] price_offer_row {
        uint64_t row_id;
        string node_id;
        name owner_account;
        name token_contract;
        asset unit_price;
        string pricing_unit;
        time_point_sec effective_from;
        time_point_sec updated_at;

        uint64_t primary_key() const { return row_id; }
        checksum256 by_nodeid() const { return compute_text_key(node_id); }
        uint64_t by_owner() const { return owner_account.value; }
    };

    struct [[eosio::table("acpttokens")]] accepted_token_row {
        uint64_t config_id;
        name token_contract;
        symbol token_symbol;
        bool enabled;
        time_point_sec updated_at;

        uint64_t primary_key() const { return config_id; }
        uint128_t by_tokensym() const {
            return (static_cast<uint128_t>(token_contract.value) << 64) |
                   token_symbol.code().raw();
        }
    };

    struct [[eosio::table("balances")]] balance_row {
        uint64_t row_id;
        name owner_account;
        name token_contract;
        asset available_quantity;
        time_point_sec updated_at;

        uint64_t primary_key() const { return row_id; }
        uint64_t by_owner() const { return owner_account.value; }
        checksum256 by_balancekey() const {
            return compute_balance_key(owner_account, token_contract, available_quantity.symbol.code());
        }
    };

    struct [[eosio::table("receipts")]] receipt_row {
        uint64_t row_id;
        name receipt_kind;
        string payment_reference;
        string manifest_hash;
        string node_id;
        name source_account;
        name token_contract;
        asset quantity;
        asset distributed_quantity;
        name status;
        time_point_sec created_at;
        time_point_sec updated_at;

        uint64_t primary_key() const { return row_id; }
        checksum256 by_payref() const { return compute_text_key(payment_reference); }
    };

    struct [[eosio::table("settlements")]] settlement_row {
        uint64_t row_id;
        string settlement_id;
        string file_id;
        string payment_reference;
        string payment_txid;
        string manifest_hash;
        name token_contract;
        asset gross_quantity;
        asset protocol_fee_quantity;
        asset distributed_quantity;
        name status;
        time_point_sec settled_at;

        uint64_t primary_key() const { return row_id; }
        checksum256 by_settleid() const { return compute_text_key(settlement_id); }
        checksum256 by_paytxid() const { return compute_text_key(payment_txid); }
    };

    struct [[eosio::table("pricepolicy")]] pricing_policy {
        name stake_token_contract;
        asset stake_minimum;
        name consensus_algorithm;
        name settlement_authority;
        uint32_t max_price_age_sec = 0;
        uint16_t min_eligible_price_nodes = 0;
        uint16_t protocol_fee_bps = 0;
        uint32_t unstake_cooldown_sec = 0;
        time_point_sec updated_at;
    };

    using node_table = multi_index<
        "nodes"_n,
        node_row,
        indexed_by<"bynodeid"_n, const_mem_fun<node_row, checksum256, &node_row::by_nodeid>>,
        indexed_by<"byowner"_n, const_mem_fun<node_row, uint64_t, &node_row::by_owner>>
    >;
    using stake_table = multi_index<
        "stakes"_n,
        stake_row,
        indexed_by<"bynodeid"_n, const_mem_fun<stake_row, checksum256, &stake_row::by_nodeid>>,
        indexed_by<"byowner"_n, const_mem_fun<stake_row, uint64_t, &stake_row::by_owner>>
    >;
    using price_offer_table = multi_index<
        "priceoffers"_n,
        price_offer_row,
        indexed_by<"bynodeid"_n, const_mem_fun<price_offer_row, checksum256, &price_offer_row::by_nodeid>>,
        indexed_by<"byowner"_n, const_mem_fun<price_offer_row, uint64_t, &price_offer_row::by_owner>>
    >;
    using accepted_token_table = multi_index<
        "acpttokens"_n,
        accepted_token_row,
        indexed_by<"bytokensym"_n, const_mem_fun<accepted_token_row, uint128_t, &accepted_token_row::by_tokensym>>
    >;
    using balance_table = multi_index<
        "balances"_n,
        balance_row,
        indexed_by<"byowner"_n, const_mem_fun<balance_row, uint64_t, &balance_row::by_owner>>,
        indexed_by<"bybalancekey"_n, const_mem_fun<balance_row, checksum256, &balance_row::by_balancekey>>
    >;
    using receipt_table = multi_index<
        "receipts"_n,
        receipt_row,
        indexed_by<"bypayref"_n, const_mem_fun<receipt_row, checksum256, &receipt_row::by_payref>>
    >;
    using settlement_table = multi_index<
        "settlements"_n,
        settlement_row,
        indexed_by<"bysettleid"_n, const_mem_fun<settlement_row, checksum256, &settlement_row::by_settleid>>,
        indexed_by<"bypaytxid"_n, const_mem_fun<settlement_row, checksum256, &settlement_row::by_paytxid>>
    >;
    using pricing_policy_singleton = singleton<"pricepolicy"_n, pricing_policy>;

    static constexpr name role_metadata = "metadata"_n;
    static constexpr name role_storage = "storage"_n;
    static constexpr name role_both = "both"_n;
    static constexpr name status_active = "active"_n;
    static constexpr name status_suspended = "suspended"_n;
    static constexpr name status_retired = "retired"_n;
    static constexpr name stake_pending_unstake = "pendingunstk"_n;
    static constexpr name stake_withdrawn = "withdrawn"_n;
    static constexpr name settlement_complete = "settled"_n;
    static constexpr name receipt_stake = "stake"_n;
    static constexpr name receipt_storage = "storage"_n;
    static constexpr name receipt_received = "received"_n;
    static constexpr name receipt_settled = "settled"_n;

    static checksum256 compute_text_key(const string& value);
    static checksum256 compute_balance_key(
        const name& owner_account,
        const name& token_contract,
        const symbol_code& symbol_code
    );

    pricing_policy get_policy() const;
    accepted_token_row require_enabled_token(const name& token_contract, const symbol& token_symbol) const;
    balance_table::iterator find_balance(balance_table& balances, const name& owner_account, const name& token_contract, const symbol_code& symbol_code);
    receipt_table::iterator find_receipt(receipt_table& receipts, const string& payment_reference);
    tuple<bool, string> parse_stake_memo(const string& memo) const;
    tuple<bool, string, string> parse_storage_memo(const string& memo) const;
    void validate_role(const name& role) const;
    void validate_node_status(const name& status) const;
    void validate_endpoint(const string& value, const char* field_name, bool required) const;
    void validate_node_public_key(const string& node_public_key) const;
    void validate_text(const string& value, uint32_t max_length, const char* field_name, bool allow_empty) const;
    void validate_printable_ascii_text(
        const string& value,
        uint32_t max_length,
        const char* field_name,
        bool allow_empty
    ) const;
    void validate_nonnegative_asset(const asset& quantity, const char* field_name) const;
    void upsert_stake_after_deposit(
        const string& node_id,
        const name& owner_account,
        const name& token_contract,
        const asset& quantity,
        bool node_is_suspended
    );
};
