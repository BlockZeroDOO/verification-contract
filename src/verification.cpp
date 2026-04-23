#include <verification_enterprise.hpp>

#include <eosio/dispatcher.hpp>

extern "C" {
    [[eosio::wasm_entry]]
    void apply(uint64_t receiver, uint64_t code, uint64_t action) {
        if (code == receiver) {
            switch (action) {
                EOSIO_DISPATCH_HELPER(
                    verification_enterprise,
                    (billsubmit)(retailsub)
                    (billbatch)(retailbatch)
                )
            }
            return;
        }
    }
}
