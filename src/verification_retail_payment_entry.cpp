#include <verification_retail_payment.hpp>

#include <eosio/dispatcher.hpp>

extern "C" {
    [[eosio::wasm_entry]]
    void apply(uint64_t receiver, uint64_t code, uint64_t action) {
        if (code == receiver) {
            switch (action) {
                EOSIO_DISPATCH_HELPER(
                    verification_retail_payment,
                    (settoken)(rmtoken)(setprice)(consume)(withdraw)
                )
            }
            return;
        }

        if (action == "transfer"_n.value) {
            eosio::execute_action(
                eosio::name(receiver),
                eosio::name(code),
                &verification_retail_payment::ontransfer
            );
        }
    }
}
