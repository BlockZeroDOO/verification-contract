#include <verification.hpp>

#include <eosio/dispatcher.hpp>

void verification::record(
    const name& submitter,
    const checksum256& object_hash,
    const string& canonicalization_profile,
    const string& client_reference
) {
    require_auth(authorized_writer);
    check(is_account(submitter), "submitter account does not exist");
    validate_printable_ascii_text(canonicalization_profile, 32, "canonicalization_profile", false);
    validate_client_reference(client_reference);

    proof_table proofs(get_self(), get_self().value);
    uint64_t next_id = static_cast<uint64_t>(current_time_point().sec_since_epoch());
    while (proofs.find(next_id) != proofs.end()) {
        ++next_id;
    }

    proofs.emplace(get_self(), [&](auto& row) {
        row.proof_id = next_id;
        row.writer = authorized_writer;
        row.submitter = submitter;
        row.object_hash = object_hash;
        row.canonicalization_profile = canonicalization_profile;
        row.client_reference = client_reference;
        row.submitted_at = time_point_sec(current_time_point());
    });
}

void verification::validate_client_reference(const string& client_reference) const {
    validate_printable_ascii_text(client_reference, 128, "client_reference", false);

    for (char ch : client_reference) {
        check(ch != '|', "client_reference cannot contain '|'");
    }
}

void verification::validate_printable_ascii_text(
    const string& value,
    uint32_t max_length,
    const char* field_name,
    bool allow_empty
) const {
    validate_text(value, max_length, field_name, allow_empty);

    for (char ch : value) {
        const unsigned char code = static_cast<unsigned char>(ch);
        check(code >= 32 && code <= 126, string(field_name) + " must use printable ASCII characters");
    }
}

void verification::validate_text(
    const string& value,
    uint32_t max_length,
    const char* field_name,
    bool allow_empty
) const {
    if (!allow_empty) {
        check(!value.empty(), string(field_name) + " cannot be empty");
    }
    check(value.size() <= max_length, string(field_name) + " is too long");
}

EOSIO_DISPATCH(verification, (record))
