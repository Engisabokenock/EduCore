"""End-to-end API flows against a real PostgreSQL database (see tests/conftest.py)."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from tests.conftest import requires_db

pytestmark = [requires_db, pytest.mark.asyncio]

API = "/api/v1"


# ── helpers ──────────────────────────────────────────────────────────────────

async def register(client, email="learner@example.com", role="student", password="Str0ngPass!"):
    res = await client.post(f"{API}/auth/register/", json={
        "email": email, "first_name": "Amani", "last_name": "Otieno",
        "password": password, "password_confirm": password, "role": role,
    })
    assert res.status_code == 201, res.text
    return res.json()


def auth(tokens):
    return {"Authorization": f"Bearer {tokens['access']}"}


async def set_role(engine, email, role):
    async with engine.begin() as conn:
        await conn.execute(text(
            "UPDATE users SET role_id = (SELECT id FROM roles WHERE name = :role) WHERE email = :email"
        ), {"role": role, "email": email})


async def seed_catalogue(engine):
    """Two grades sharing subject/topic slugs, a free and a premium resource, one plan."""
    ids = {k: uuid.uuid4() for k in ("g1", "g2", "s1", "s2", "t1", "t2", "free", "prem", "plan", "author")}
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO cbc_grades (id, name, code, slug, curriculum, is_active, "order") VALUES
            (:g1, 'Grade 10', 'G10', 'grade-10', 'CBC', true, 10),
            (:g2, 'Grade 2', 'G2', 'grade-2', 'CBC', true, 2)
        """), ids)
        await conn.execute(text("""
            INSERT INTO cbc_subjects (id, grade_id, name, code, slug, is_active, "order") VALUES
            (:s1, :g1, 'Mathematics', 'G10-MATH', 'mathematics', true, 1),
            (:s2, :g2, 'Mathematics', 'G2-MATH', 'mathematics', true, 1)
        """), ids)
        await conn.execute(text("""
            INSERT INTO cbc_topics (id, subject_id, name, ordering, slug, is_active) VALUES
            (:t1, :s1, 'General', 1, 'general', true),
            (:t2, :s2, 'General', 1, 'general', true)
        """), ids)
        await conn.execute(text("""
            INSERT INTO users (id, email, hashed_password, role_id, is_active, created_at, is_verified)
            VALUES (:author, 'author@example.com', 'x', (SELECT id FROM roles WHERE name='teacher'), true, now(), true)
        """), ids)
        await conn.execute(text("""
            INSERT INTO academic_resources (id, title, slug, grade_id, subject_id, topic_id, term, year, pdf_url,
                type_variant, is_premium, is_published, is_archived, views_count, downloads_count,
                created_by_id, created_at, updated_at, published_at)
            VALUES
            (:free, 'Free Fractions Worksheet', 'free-fractions', :g2, :s2, :t2, '1', 2026,
             'https://files.example.com/free.pdf', 'worksheet', false, true, false, 0, 0, :author, now(), now(), now()),
            (:prem, 'Premium Mock Exam', 'premium-mock', :g2, :s2, :t2, '2', 2026,
             'https://files.example.com/SECRET-premium.pdf', 'mock_exam', true, true, false, 0, 0, :author, now(), now(), now())
        """), ids)
        await conn.execute(text("""
            INSERT INTO subscription_plans (id, name, tier, price, duration_days, is_available, is_featured, sort_order)
            VALUES (:plan, 'Monthly Pass', 'monthly', 350.00, 30, true, true, 1)
        """), ids)
    return ids


# ── authentication ───────────────────────────────────────────────────────────

async def test_register_login_me_and_refresh_rotation(client):
    data = await register(client, email="Mixed.Case@Example.com")
    assert data["user"]["email"] == "mixed.case@example.com"
    assert data["user"]["role"] == "student"
    assert data["user"]["is_verified"] is False

    login = await client.post(f"{API}/auth/login/", json={"email": "MIXED.case@example.com", "password": "Str0ngPass!"})
    assert login.status_code == 200, login.text
    tokens = login.json()["tokens"]

    me = await client.get(f"{API}/auth/me/", headers=auth(tokens))
    assert me.status_code == 200 and me.json()["first_name"] == "Amani"

    rotated = await client.post(f"{API}/auth/token/refresh/", json={"refresh": tokens["refresh"]})
    assert rotated.status_code == 200
    new_tokens = rotated.json()

    # Replaying the old refresh token is rejected and revokes the whole session family.
    replay = await client.post(f"{API}/auth/token/refresh/", json={"refresh": tokens["refresh"]})
    assert replay.status_code == 401
    after = await client.post(f"{API}/auth/token/refresh/", json={"refresh": new_tokens["refresh"]})
    assert after.status_code == 401


async def test_duplicate_email_and_privileged_self_registration_rejected(client):
    await register(client)
    dup = await client.post(f"{API}/auth/register/", json={
        "email": "LEARNER@example.com", "first_name": "A", "last_name": "B", "password": "Str0ngPass!",
    })
    assert dup.status_code == 409
    assert dup.json()["success"] is False and "already exists" in dup.json()["error"]

    escalate = await client.post(f"{API}/auth/register/", json={
        "email": "evil@example.com", "first_name": "E", "last_name": "V", "password": "Str0ngPass!",
        "role": "super_admin",
    })
    assert escalate.status_code == 403


async def test_wrong_password_and_validation_errors_are_readable(client):
    await register(client)
    bad = await client.post(f"{API}/auth/login/", json={"email": "learner@example.com", "password": "nope"})
    assert bad.status_code == 401 and bad.json()["error"] == "Incorrect e-mail or password."

    invalid = await client.post(f"{API}/auth/register/", json={"email": "not-an-email"})
    assert invalid.status_code == 422
    assert isinstance(invalid.json()["error"], str) and invalid.json()["detail"]


async def test_change_password_accepts_frontend_field_names(client):
    tokens = (await register(client))["tokens"]
    res = await client.post(f"{API}/users/me/change-password/", headers=auth(tokens), json={
        "old_password": "Str0ngPass!", "new_password": "N3wPassword!", "new_password_confirm": "N3wPassword!",
    })
    assert res.status_code == 204, res.text
    login = await client.post(f"{API}/auth/login/", json={"email": "learner@example.com", "password": "N3wPassword!"})
    assert login.status_code == 200


async def test_logout_accepts_json_body(client):
    tokens = (await register(client))["tokens"]
    res = await client.post(f"{API}/auth/logout/", json={"refresh": tokens["refresh"]})
    assert res.status_code == 204
    again = await client.post(f"{API}/auth/token/refresh/", json={"refresh": tokens["refresh"]})
    assert again.status_code == 401


# ── curriculum ───────────────────────────────────────────────────────────────

async def test_grades_ordered_and_shared_subject_slugs_resolve(client, db_engine):
    await seed_catalogue(db_engine)
    grades = (await client.get(f"{API}/academic/grades/")).json()
    assert [g["slug"] for g in grades] == ["grade-2", "grade-10"]  # curriculum order, not alphabetical
    assert grades[0]["subject_count"] == 1

    grade = (await client.get(f"{API}/academic/grades/grade-10/")).json()
    assert [s["slug"] for s in grade["subjects"]] == ["mathematics"]

    # "mathematics" exists in two grades: previously a 500 (MultipleResultsFound).
    scoped = await client.get(f"{API}/academic/subjects/mathematics/", params={"grade": "grade-10"})
    assert scoped.status_code == 200 and scoped.json()["grade"]["slug"] == "grade-10"
    unscoped = await client.get(f"{API}/academic/subjects/mathematics/")
    assert unscoped.status_code == 200 and unscoped.json()["grade"]["slug"] == "grade-2"

    topics = (await client.get(f"{API}/academic/subjects/mathematics/topics/", params={"grade": "grade-2"})).json()
    assert topics[0]["slug"] == "general" and topics[0]["resource_count"] == 2


# ── catalogue, search and downloads ──────────────────────────────────────────

async def test_public_listing_never_exposes_file_urls(client, db_engine):
    await seed_catalogue(db_engine)
    listing = await client.get(f"{API}/resources/", params={"ordering": "-downloads_count", "page_size": 6})
    assert listing.status_code == 200
    body = listing.text
    assert "SECRET-premium" not in body and "pdf_url" not in body
    item = listing.json()["results"][0]
    assert {"resource_type", "thumbnail", "file_type", "tags"} <= item.keys()

    detail = await client.get(f"{API}/resources/premium-mock/")
    assert detail.status_code == 200 and "SECRET-premium" not in detail.text


async def test_public_search_works(client, db_engine):
    await seed_catalogue(db_engine)
    res = await client.get(f"{API}/search/", params={"q": "fractions"})
    assert res.status_code == 200, res.text
    assert [r["slug"] for r in res.json()["resources"]] == ["free-fractions"]
    wildcard = await client.get(f"{API}/search/", params={"q": "%"})
    assert wildcard.status_code == 200 and wildcard.json()["resources"] == []


async def test_downloads_respect_entitlements_and_quota(client, db_engine):
    await seed_catalogue(db_engine)

    anon_free = await client.post(f"{API}/resources/free-fractions/download/")
    assert anon_free.status_code == 200 and anon_free.json()["url"].endswith("free.pdf")

    anon_premium = await client.post(f"{API}/resources/premium-mock/download/")
    assert anon_premium.status_code == 401

    tokens = (await register(client))["tokens"]
    student_premium = await client.post(f"{API}/resources/premium-mock/download/", headers=auth(tokens))
    assert student_premium.status_code == 403
    access = (await client.get(f"{API}/resources/premium-mock/access/", headers=auth(tokens))).json()
    assert access == {"can_access": False, "is_premium": True, "requires_login": False, "requires_subscription": True}

    for _ in range(5):
        assert (await client.post(f"{API}/resources/free-fractions/download/", headers=auth(tokens))).status_code == 200
    capped = await client.post(f"{API}/resources/free-fractions/download/", headers=auth(tokens))
    assert capped.status_code == 429  # 5 free downloads per day, counted per account

    async with db_engine.connect() as conn:
        count = (await conn.execute(text("SELECT downloads_count FROM academic_resources WHERE slug='free-fractions'"))).scalar()
    assert count == 6


# ── payments and subscriptions ───────────────────────────────────────────────

class FakeMpesa:
    counter = 0

    async def send_stk_push(self, phone_number, amount, account_reference, description="EduCore"):
        FakeMpesa.counter += 1
        FakeMpesa.last_amount = amount
        return {"ResponseCode": "0", "MerchantRequestID": f"m-{FakeMpesa.counter}",
                "CheckoutRequestID": f"ws_CO_{FakeMpesa.counter}"}


def callback(checkout_id, result_code=0, amount=350, receipt="RKT123ABC"):
    body = {"MerchantRequestID": "m", "CheckoutRequestID": checkout_id, "ResultCode": result_code,
            "ResultDesc": "ok" if result_code == 0 else "Request cancelled by user"}
    if result_code == 0:
        body["CallbackMetadata"] = {"Item": [
            {"Name": "Amount", "Value": amount}, {"Name": "MpesaReceiptNumber", "Value": receipt},
            {"Name": "PhoneNumber", "Value": 254712345678},
        ]}
    return {"Body": {"stkCallback": body}}


async def test_renew_no_longer_grants_free_premium(client, db_engine, monkeypatch):
    ids = await seed_catalogue(db_engine)
    monkeypatch.setattr("app.services.payment_service.MpesaClient", FakeMpesa)
    tokens = (await register(client))["tokens"]
    res = await client.post(f"{API}/subscriptions/renew/", headers=auth(tokens),
                            json={"plan_id": str(ids["plan"]), "phone_number": "0712345678"})
    assert res.status_code == 202 and res.json()["amount"] == 350
    sub = await client.get(f"{API}/subscriptions/me/", headers=auth(tokens))
    assert sub.status_code == 200 and sub.json() is None  # nothing granted before payment


async def test_full_payment_flow_is_secure_and_idempotent(client, db_engine, monkeypatch):
    ids = await seed_catalogue(db_engine)
    monkeypatch.setattr("app.services.payment_service.MpesaClient", FakeMpesa)
    tokens = (await register(client))["tokens"]

    checkout = await client.post(f"{API}/payments/buy-premium/", headers=auth(tokens),
                                 json={"plan_id": str(ids["plan"]), "phone_number": "0712345678", "amount": 1})
    assert checkout.status_code == 202, checkout.text
    assert FakeMpesa.last_amount == 350  # client-supplied amount is ignored
    checkout_id = checkout.json()["checkout_request_id"]

    spam = await client.post(f"{API}/payments/checkout/", headers=auth(tokens),
                             json={"plan_id": str(ids["plan"]), "phone_number": "254712345678"})
    assert spam.status_code == 429  # cooldown while a prompt is still pending

    forged = await client.post(f"{API}/payments/mpesa/callback", json=callback(checkout_id))
    assert forged.status_code == 403  # no shared secret

    under = await client.post(f"{API}/payments/mpesa/callback?token=cb-secret-test",
                              json=callback(checkout_id, amount=1))
    assert under.status_code == 200
    status = (await client.get(f"{API}/payments/status/{checkout_id}/", headers=auth(tokens))).json()
    assert status["status"] == "failed" and "Amount mismatch" in status["failure_reason"]

    checkout2 = await client.post(f"{API}/payments/checkout/", headers=auth(tokens),
                                  json={"plan_id": str(ids["plan"]), "phone_number": "254712345678"})
    checkout_id2 = checkout2.json()["checkout_request_id"]

    ok = await client.post(f"{API}/payments/mpesa/callback?token=cb-secret-test", json=callback(checkout_id2))
    assert ok.status_code == 200 and ok.json()["ResultCode"] == 0
    replay = await client.post(f"{API}/payments/mpesa/callback?token=cb-secret-test", json=callback(checkout_id2))
    assert replay.status_code == 200

    sub = (await client.get(f"{API}/subscriptions/me/", headers=auth(tokens))).json()
    assert sub["status"] == "active" and sub["has_access"] is True
    period = datetime.fromisoformat(sub["current_period_end"]) - datetime.now(timezone.utc)
    assert 29 <= period.days <= 30  # replayed callback did not extend twice

    premium = await client.post(f"{API}/resources/premium-mock/download/", headers=auth(tokens))
    assert premium.status_code == 200 and "SECRET-premium" in premium.json()["url"]

    notes = await client.get(f"{API}/notifications/", headers=auth(tokens))
    assert notes.status_code == 200 and notes.json()[0]["notification_type"] == "payment_success"


# ── administration ───────────────────────────────────────────────────────────

async def test_admin_stats_and_super_admin_protection(client, db_engine):
    await seed_catalogue(db_engine)
    student = (await register(client, "student@example.com"))["tokens"]
    assert (await client.get(f"{API}/admin-control-plane/dashboard/stats/", headers=auth(student))).status_code == 403

    await register(client, "admin@example.com")
    await set_role(db_engine, "admin@example.com", "admin")
    admin = (await client.post(f"{API}/auth/login/", json={"email": "admin@example.com", "password": "Str0ngPass!"})).json()["tokens"]
    stats = await client.get(f"{API}/admin-control-plane/dashboard/stats/", headers=auth(admin))
    assert stats.status_code == 200 and stats.json()["total_resources"] == 2

    users = await client.post(f"{API}/admin-control-plane/users/search/", headers=auth(admin), json={"page": 1})
    assert users.status_code == 200 and {"first_name", "role", "date_joined"} <= users.json()[0].keys()

    owner = await register(client, "owner@example.com")
    await set_role(db_engine, "owner@example.com", "super_admin")
    takeover = await client.patch(f"{API}/admin-control-plane/users/{owner['user']['id']}/", headers=auth(admin),
                                  json={"email": "attacker@example.com"})
    assert takeover.status_code == 403

    # Super Admin passes ADMIN-only routes (it used to be locked out).
    owner_tokens = (await client.post(f"{API}/auth/login/", json={"email": "owner@example.com", "password": "Str0ngPass!"})).json()["tokens"]
    assert (await client.get(f"{API}/admin-control-plane/dashboard/stats/", headers=auth(owner_tokens))).status_code == 200
    audit = await client.get(f"{API}/security-control-plane/system/audit-trail/", headers=auth(owner_tokens))
    assert audit.status_code == 200


async def test_health_reports_dependencies(client):
    res = await client.get(f"{API}/health")
    assert res.status_code == 200 and res.json()["checks"]["database"] == "ok"
    assert res.headers.get("x-request-id")
