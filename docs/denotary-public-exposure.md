# Public Exposure Guidance

This note captures the recommended public deployment stance for the deNotary off-chain services.

## Exposure model

Recommended:

- keep `Finality Watcher` private
- expose `Receipt Service` only through a reverse proxy
- expose `Audit API` only through a reverse proxy
- expose `Ingress API` publicly only if you explicitly want third-party preparation over HTTP

## Privacy modes

`Receipt Service` and `Audit API` support:

- `full`
- `public`

Use:

- `full` for trusted internal deployments
- `public` for internet-facing deployments

Environment variables:

- `RECEIPT_PRIVACY_MODE=public`
- `AUDIT_PRIVACY_MODE=public`

## Reverse proxy templates

Reference templates:

- [deploy/nginx/denotary-public.conf](/c:/projects/verification-contract/deploy/nginx/denotary-public.conf:1)
- [deploy/caddy/Caddyfile.public](/c:/projects/verification-contract/deploy/caddy/Caddyfile.public:1)

These templates illustrate:

- TLS termination
- rate limiting
- request logging
- explicit non-exposure of `Finality Watcher`

## Operational notes

- keep service binds on `127.0.0.1` whenever possible
- do not route `/v1/watch/*` through a public proxy
- rotate `WATCHER_AUTH_TOKEN`
- review whether public `Ingress API` aligns with your abuse and privacy model
