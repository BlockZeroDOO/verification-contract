#include <verification_enterprise.hpp>

#include <eosio/dispatcher.hpp>

extern "C" {
    [[eosio::wasm_entry]]
    void apply(uint64_t receiver, uint64_t code, uint64_t action) {
        if (code == receiver) {
            switch (action) {
                EOSIO_DISPATCH_HELPER(
                    verification_enterprise,
                    (addschema)(updateschema)(deprecate)
                    (setpolicy)(setauthsrcs)
                    (submit)(billsubmit)(retailsub)
                    (submitroot)(billbatch)(retailbatch)
                    (withdraw)
                )
            }
            return;
        }
    }
}
