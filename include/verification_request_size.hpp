#pragma once

#include <eosio/crypto.hpp>
#include <eosio/name.hpp>
#include <eosio/serialize.hpp>

#include <cstdint>

namespace verification_request_size {

using eosio::checksum256;
using eosio::name;

struct single_registry_request {
    name submitter;
    uint64_t schema_id;
    uint64_t policy_id;
    checksum256 object_hash;
    checksum256 external_ref;

    EOSLIB_SERIALIZE(single_registry_request, (submitter)(schema_id)(policy_id)(object_hash)(external_ref))
};

struct batch_registry_request {
    name submitter;
    uint64_t schema_id;
    uint64_t policy_id;
    checksum256 root_hash;
    uint32_t leaf_count;
    checksum256 manifest_hash;
    checksum256 external_ref;

    EOSLIB_SERIALIZE(
        batch_registry_request,
        (submitter)(schema_id)(policy_id)(root_hash)(leaf_count)(manifest_hash)(external_ref)
    )
};

inline uint64_t compute_single_registry_bytes(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& object_hash,
    const checksum256& external_ref
) {
    const auto packed = eosio::pack(single_registry_request{
        submitter,
        schema_id,
        policy_id,
        object_hash,
        external_ref
    });
    return static_cast<uint64_t>(packed.size());
}

inline uint64_t compute_batch_registry_bytes(
    const name& submitter,
    uint64_t schema_id,
    uint64_t policy_id,
    const checksum256& root_hash,
    uint32_t leaf_count,
    const checksum256& manifest_hash,
    const checksum256& external_ref
) {
    const auto packed = eosio::pack(batch_registry_request{
        submitter,
        schema_id,
        policy_id,
        root_hash,
        leaf_count,
        manifest_hash,
        external_ref
    });
    return static_cast<uint64_t>(packed.size());
}

}  // namespace verification_request_size
