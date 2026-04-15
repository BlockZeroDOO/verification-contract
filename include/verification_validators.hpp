#pragma once

#include <eosio/asset.hpp>
#include <eosio/crypto.hpp>
#include <eosio/system.hpp>
#include <eosio/time.hpp>

#include <array>
#include <string>
#include <tuple>

namespace verification_validators {

static constexpr uint8_t checksum_hash_size = 32;

using eosio::asset;
using eosio::check;
using eosio::checksum256;
using eosio::current_time_point;
using eosio::symbol;
using eosio::time_point_sec;
using std::array;
using std::string;
using std::tuple;

inline bool is_zero_checksum(const checksum256& value) {
    const auto bytes = value.extract_as_byte_array();
    for (auto byte : bytes) {
        if (byte != 0) {
            return false;
        }
    }
    return true;
}

inline uint8_t from_hex(char c) {
    if (c >= '0' && c <= '9') {
        return static_cast<uint8_t>(c - '0');
    }
    if (c >= 'a' && c <= 'f') {
        return static_cast<uint8_t>(10 + (c - 'a'));
    }
    if (c >= 'A' && c <= 'F') {
        return static_cast<uint8_t>(10 + (c - 'A'));
    }

    check(false, "object hash contains non-hex characters");
    return 0;
}

inline void validate_text(const string& value, uint32_t max_length, const char* field_name, bool allow_empty) {
    if (!allow_empty) {
        check(!value.empty(), string(field_name) + " cannot be empty");
    }
    check(value.size() <= max_length, string(field_name) + " is too long");
}

inline void validate_printable_ascii_text(
    const string& value,
    uint32_t max_length,
    const char* field_name,
    bool allow_empty
) {
    validate_text(value, max_length, field_name, allow_empty);

    for (char ch : value) {
        const unsigned char code = static_cast<unsigned char>(ch);
        check(code >= 32 && code <= 126, string(field_name) + " must use printable ASCII characters");
    }
}

inline void validate_future_time(const time_point_sec& value, const char* field_name) {
    check(value > time_point_sec(current_time_point()), string(field_name) + " must be in the future");
}

inline void validate_registry_id(uint64_t id, const char* field_name) {
    check(id > 0, string(field_name) + " must be greater than zero");
}

inline void validate_policy_settings(
    bool allow_single,
    bool allow_batch,
    bool require_kyc,
    uint8_t min_kyc_level,
    bool allow_zk,
    bool active
) {
    if (!require_kyc) {
        check(min_kyc_level == 0, "min_kyc_level must be zero when require_kyc is false");
    }

    if (active) {
        check(
            allow_single || allow_batch || allow_zk,
            "active policy must enable at least one supported mode"
        );
    }
}

inline void validate_payment_price(const asset& price, const char* field_name) {
    check(price.is_valid(), string(field_name) + " is invalid");
    check(price.amount > 0, string(field_name) + " must be positive");
    check(price.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

inline void validate_nonnegative_asset(const asset& quantity, const char* field_name) {
    check(quantity.is_valid(), string(field_name) + " is invalid");
    check(quantity.amount >= 0, string(field_name) + " cannot be negative");
    check(quantity.symbol.is_valid(), string(field_name) + " has invalid symbol");
}

inline checksum256 parse_hash(const string& hex) {
    check(
        hex.size() == checksum_hash_size * 2,
        "object hash must be 64 hex characters"
    );

    array<uint8_t, checksum_hash_size> bytes{};
    for (size_t i = 0; i < bytes.size(); ++i) {
        const auto high = from_hex(hex[i * 2]);
        const auto low = from_hex(hex[i * 2 + 1]);
        bytes[i] = static_cast<uint8_t>((high << 4) | low);
    }

    return checksum256(bytes);
}

inline void validate_nonzero_checksum(const checksum256& value, const char* field_name) {
    check(!is_zero_checksum(value), string(field_name) + " cannot be zero");
}

inline tuple<string, string, string, string> parse_payment_memo(const string& memo) {
    const auto first = memo.find('|');
    const auto second = memo.find('|', first == string::npos ? first : first + 1);
    const auto third = memo.find('|', second == string::npos ? second : second + 1);

    check(
        first != string::npos &&
        second != string::npos &&
        third != string::npos &&
        memo.find('|', third + 1) == string::npos,
        "memo format must be hash|algorithm|canonicalization|client_reference"
    );

    return std::make_tuple(
        memo.substr(0, first),
        memo.substr(first + 1, second - first - 1),
        memo.substr(second + 1, third - second - 1),
        memo.substr(third + 1)
    );
}

inline void validate_client_reference(const string& client_reference) {
    validate_printable_ascii_text(client_reference, 128, "client_reference", false);

    for (char ch : client_reference) {
        check(ch != '|', "client_reference cannot contain '|'");
    }
}

}  // namespace verification_validators
