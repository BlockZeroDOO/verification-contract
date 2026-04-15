#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/eosio.hpp>

#include <verification_tables.hpp>
#include <verification_validators.hpp>

#include <cstdint>
#include <string>

namespace verification_core {

static constexpr uint8_t commitment_status_active = 0;
static constexpr uint8_t commitment_status_superseded = 1;
static constexpr uint8_t commitment_status_revoked = 2;
static constexpr uint8_t commitment_status_expired = 3;

static constexpr uint8_t batch_status_open = 0;
static constexpr uint8_t batch_status_closed = 1;

verification_tables::kyc_row require_kyc_record(const eosio::name& self, const eosio::name& account);
verification_tables::schema_row require_schema(const eosio::name& self, uint64_t id);
verification_tables::policy_row require_policy(const eosio::name& self, uint64_t id);

uint64_t next_batch_id(const eosio::name& self);
uint64_t next_commitment_id(const eosio::name& self);

void validate_batch_request_unique(
    const eosio::name& self,
    const eosio::name& submitter,
    const eosio::checksum256& external_ref
);

void validate_batch_is_open(const verification_tables::batch_row& batch);

void validate_commitment_request_unique(
    const eosio::name& self,
    const eosio::name& submitter,
    const eosio::checksum256& external_ref
);

void validate_commitment_can_be_successor(
    const verification_tables::commitment_row& current,
    const verification_tables::commitment_row& successor
);

void validate_commitment_is_active(const verification_tables::commitment_row& commitment);

}  // namespace verification_core
