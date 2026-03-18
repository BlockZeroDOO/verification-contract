#include <verificationlegacywipe.hpp>

#include <eosio/dispatcher.hpp>

void verificationlegacywipe::wipeall(uint32_t max_rows) {
    require_auth(get_self());
    check(max_rows > 0, "max_rows must be positive");

    uint32_t remaining = max_rows;

    proof_table proofs(get_self(), get_self().value);
    remaining = erase_rows(proofs, remaining);

    payment_token_table paytokens(get_self(), get_self().value);
    remaining = erase_rows(paytokens, remaining);

    wholesale_table wholesale(get_self(), get_self().value);
    remaining = erase_rows(wholesale, remaining);

    nonprofit_table nonprofit(get_self(), get_self().value);
    remaining = erase_rows(nonprofit, remaining);

    free_usage_table free_usage(get_self(), get_self().value);
    remaining = erase_rows(free_usage, remaining);

    if (remaining > 0) {
        free_policy_singleton policy(get_self(), get_self().value);
        if (policy.exists()) {
            policy.remove();
        }
    }

    if (remaining > 0) {
        legacy_config_singleton config(get_self(), get_self().value);
        if (config.exists()) {
            config.remove();
        }
    }
}

template <typename Table>
uint32_t verificationlegacywipe::erase_rows(Table& table, uint32_t remaining) {
    while (remaining > 0) {
        auto itr = table.begin();
        if (itr == table.end()) {
            break;
        }

        itr = table.erase(itr);
        static_cast<void>(itr);
        --remaining;
    }

    return remaining;
}

EOSIO_DISPATCH(verificationlegacywipe, (wipeall))
