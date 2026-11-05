# Changelog

## [1.2.0] - 2026-11-04 - Account approvals and activity monitoring

### Added
- Teachers and administrators can sign up, but their accounts stay pending until reviewed. Admins approve teachers; only the Super Admin approves administrators. Pending and rejected accounts cannot sign in.
- Review queue: `GET/POST /admin-control-plane/approvals` (list, summary, approve, reject with a note shown to the applicant), plus the `/admin/approvals` page.
- Platform activity log (`activity_logs`): sign-ins, failed sign-ins, registrations, approvals, staff edits, role changes, payments, refunds, downloads and every other state-changing API call, with actor, IP, device and request ID. Super Admin only: `GET /security-control-plane/activity` and `/activity/summary`, plus the `/admin/audit` page.
- `scripts/create_staff_account.py` provisions pre-approved Super Admin / Admin accounts from the server (single Super Admin enforced).
- Migration `20261104120000_account_approvals_activity_log`.

### Security
- Only the Super Admin can grant the admin role or edit administrator accounts.
- The Super Admin role is reserved for `PLATFORM_OWNER_EMAIL` (default isabokenock@gmail.com). Any other account holding that role is treated as a student, the role cannot be granted through the API, and the owner account cannot be renamed or deleted. Provisioning the owner moves any other Super Admin to Admin.
- Role changes and deactivation revoke the user's sessions.

### Fixed
- The admin shell rendered twice (route layout and page both wrapped it).
- The old audit-trail endpoints returned notification e-mails instead of activity.

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
