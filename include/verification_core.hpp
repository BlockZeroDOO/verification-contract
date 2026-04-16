#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>

#include <verification_tables.hpp>
#include <verification_validators.hpp>

#include <cstdint>
#include <string>

namespace verification_core {

verification_tables::schema_row require_schema(const eosio::name& self, uint64_t id);
verification_tables::policy_row require_policy(const eosio::name& self, uint64_t id);

uint64_t next_batch_id(const eosio::name& self);
uint64_t next_commitment_id(const eosio::name& self);

void validate_batch_request_unique(
    const eosio::name& self,
    const eosio::name& submitter,
    const eosio::checksum256& external_ref
);

void validate_commitment_request_unique(
    const eosio::name& self,
    const eosio::name& submitter,
    const eosio::checksum256& external_ref
);

}  // namespace verification_core
