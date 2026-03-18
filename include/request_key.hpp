#pragma once

#include <eosio/crypto.hpp>
#include <eosio/name.hpp>

#include <string>

namespace verification_common {
inline eosio::checksum256 compute_request_key(const eosio::name& submitter, const std::string& client_reference) {
    std::string payload = submitter.to_string();
    payload.push_back(':');
    payload += client_reference;
    return eosio::sha256(payload.data(), static_cast<uint32_t>(payload.size()));
}
}  // namespace verification_common
