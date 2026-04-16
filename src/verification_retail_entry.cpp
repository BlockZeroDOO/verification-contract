#include <verification_retail.hpp>

#include <eosio/dispatcher.hpp>

extern "C" {
    [[eosio::wasm_entry]]
    void apply(uint64_t receiver, uint64_t code, uint64_t action) {
        if (code == receiver) {
            switch (action) {
                EOSIO_DISPATCH_HELPER(
                    verification_retail,
                    (addschema)(updateschema)(deprecate)
                    (setpolicy)
                    (submit)
                    (submitroot)
                    (settoken)(rmtoken)(setprice)(withdraw)
                )
            }
            return;
        }

        if (action == "transfer"_n.value) {
            eosio::execute_action(name(receiver), name(code), &verification_retail::ontransfer);
        }
    }
}
