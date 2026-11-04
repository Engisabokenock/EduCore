# Changelog

## [1.1.0] — 2026-11-04 — Platform hardening

### Security
- Payments: `/subscriptions/renew` no longer grants paid plans without payment; checkout prices come from the plan, never the client.
- M-Pesa callback requires `MPESA_CALLBACK_SECRET`, is processed once under a row lock, and verifies the paid amount.
- Public resource responses no longer expose `pdf_url`; downloads go through entitlement checks and presigned URLs.
- Public sign-up can no longer create admin or super-admin accounts.
- Admins can no longer edit Super Admin accounts; refresh-token reuse revokes all sessions.
- CORS restricted to configured origins; the API refuses to boot in production with default secrets.
- Reset and verification tokens are stored hashed; password changes and resets revoke sessions.

### Fixed
- Enum columns stored member names instead of the database values, breaking plans, permissions and resources.
- Missing `users` columns broke register and login; the migration never created indexes or unique constraints.
- Shared subject and topic slugs across grades caused 500s on subject and topic pages.
- Server-side rendering always fetched from `http://localhost:80`, so every page showed fallback data.
- `GET /search` crashed on a missing import; notifications and reviews failed to serialize.
- Query-string "sanitizer" middleware corrupted parameters; rate limiting keyed on the proxy IP.
- Free downloads required login; subscribers were always blocked from premium content.
- Missing `/checkout` page, admin stats endpoint, and several request-shape mismatches.

### Added
- Migration `20261104090000_schema_hardening` (repairs existing databases, seeds roles and permissions).
- Services layer (`user`, `subscription`, `payment`, `download`), payment status polling with Daraja reconciliation.
- `scripts/create_superadmin.py`, health check with dependency status, request IDs, test suite, working CI.
