# Ricardian Clauses

## record

Appends a proof row to the immutable `verification` registry.

The action stores:

- the writing contract account in `writer`
- the end-user account in `submitter`
- the submitted `object_hash`
- the submitted `canonicalization_profile`
- the submitted `client_reference`
- the on-chain timestamp in `submitted_at`

Only `managementel` is authorized to call this action. The same `(submitter, client_reference)`
pair cannot be recorded twice.
