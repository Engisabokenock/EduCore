# EduCore Project Dispositions

Date: 2026-06-01  
Author Architecture: Kilo

## Active Disposition Tracker

### Payment / Commerce
- `backend/apps/commerce/models.py` — Added `plan` FK on Payment for callback lookup without subscription join
- `backend/apps/commerce/services.py` — callback uses `payment.plan` first (no None bug); `create_pending_payment` saves plan
- `backend/apps/commerce/views.py` — admin can see all payments via role check; user sees own only
- `backend/apps/commerce/serializers.py` — user PaymentSerializer strips phone/reference/transaction_id; PaymentAdminSerializer adds them back for admin-only use
- `backend/apps/commerce/models.py` — `PaymentStatusViewSet` uses `get_object_or_404` for reference lookup

### Security
- `backend/config/middleware.py` — Ip-whitelist for admin; maintenance mode; CSP/HSTS in production
- `backend/core/security.py` — input validators (phone, email, UUID, file), `RateLimitMiddleware`
- `backend/core/middleware.py` — signed URL helpers; `_build_signed_url` built, `_validate_signed_url` defined
- `backend/core/permissions.py` — refreshed: IsAdmin, IsTeacher, IsStudent, IsParent, IsOwnerOrAdmin, IsPremium, IsOwnerAndActive
- `backend/apps/accounts/permissions.py` — role/owner-based permissions
- `backend/apps/accounts/serializers.py` — RegisterSerializer removed `role` field; no admin self-registration
- `backend/apps/content/views.py` — `permission_classes=[IsAuthenticated]` on download; no anonymous path
- `backend/apps/content/services.py` — `get_signed_file_url` returns None for non-premium/anonymous
- `backend/apps/content/serializers.py` — `_user_has_subscription` treats admin as premium
- `backend/config/exceptions.py` — generic else branch returns `errors=None` (prevents info leak)
- `backend/config/urls.py` — `readiness_check` returns no DB error string

### Performance
- `backend/core/cache.py` — cache_key, cache_page decorator, cache_queryset, invalidate_cache helpers
- `backend/core/performance.py` — `optimize_content_queryset`, `optimize_grade_queryset`, `gzip_response`

### Durability of the Work
- All secrets are env-var driven: MPESA_CONSUMER_KEY/SECRET/PASSKEY/SHORTCODE/CALLBACK_URL/ENVIRONMENT
- JWT auth via `rest_framework_simplejwt`; access 15 min, refresh 7 day, rotate + blacklist
- `MEDIA_SIGNING_SECRET` env var gates signed file URLs
- `MPESA_BASE_URL` env var overrides default sandbox/prod host

## TODO next — payment/domain engineering discipline

### Failure-mode / URL hardening
1. Replace `verify_email(...) and error_response(...)` chains in views with early-return guards in `services.verify_email(...)`.
2. Add `states[-1]` fallback check in domain spin/wait loops so a single failed domain launch aborts instead of hanging.
3. Make M-Pesa `callback_url` derived from `request.build_absolute_uri(...)`? if handled behind a TLS-terminating proxy, ensure headers map correctly.
4. In `services.py`, wrap each M-Pesa domain pull in a per-call try/except that updates a local failure counter — if 2/3 attempts fail, raise `PaymentError` and mark payment failed.
5. Verify the hard-coded `sandbox.safaricom.co.ke` and `api.safaricom.co.ke` strings in `services.py` are replaced by `settings.MPESA_BASE_URL`.

### Frontend durability
1. Render login/register with a `useHydration` guard to avoid SSR mismatch under `page.tsx` weirdness.
2. Add a `<LoadingScreen />` for navigation transitions.
3. Move sensitive `console.log` outputs to a `LOGGER` module that's a no-op in production.
4. Expose an `apiFetch` wrapper that fails closed on DNS issues (abort + UI retry).
