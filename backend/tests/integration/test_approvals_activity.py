"""Account approvals (teachers by admins, admins by the Super Admin) and activity monitoring."""
import pytest
from sqlalchemy import text

from tests.conftest import requires_db
from tests.integration.test_api_flows import API, auth, register, set_role

pytestmark = [requires_db, pytest.mark.asyncio]

PASSWORD = "Str0ngPass!"


async def login(client, email, password=PASSWORD):
    return await client.post(f"{API}/auth/login/", json={"email": email, "password": password})


async def staff_tokens(client, engine, email, role):
    """Register a student, promote it directly in the database and sign in."""
    await register(client, email)
    await set_role(engine, email, role)
    res = await login(client, email)
    assert res.status_code == 200, res.text
    return res.json()["tokens"]


async def test_teacher_signup_waits_for_admin_approval(client, db_engine):
    admin = await staff_tokens(client, db_engine, "admin@example.com", "admin")

    signup = await register(client, "teacher@example.com", role="teacher")
    assert signup["tokens"] is None and signup["requires_approval"] is True
    assert signup["user"]["approval_status"] == "pending"
    assert "administrator" in signup["message"]

    blocked = await login(client, "teacher@example.com")
    assert blocked.status_code == 403 and "waiting for approval" in blocked.json()["error"]

    # The admin was notified and sees the application.
    notes = (await client.get(f"{API}/notifications/", headers=auth(admin))).json()
    assert any(n["notification_type"] == "account_review" for n in notes)
    summary = await client.get(f"{API}/admin-control-plane/approvals/summary/", headers=auth(admin))
    assert summary.json() == {"total": 1, "by_role": {"teacher": 1}}
    queue = await client.get(f"{API}/admin-control-plane/approvals/", headers=auth(admin))
    assert queue.status_code == 200 and queue.json()["items"][0]["email"] == "teacher@example.com"
    teacher_id = queue.json()["items"][0]["id"]

    approved = await client.post(f"{API}/admin-control-plane/approvals/{teacher_id}/approve/",
                                 headers=auth(admin), json={"note": "Welcome aboard"})
    assert approved.status_code == 200 and approved.json()["approval_status"] == "approved"

    again = await client.post(f"{API}/admin-control-plane/approvals/{teacher_id}/approve/", headers=auth(admin))
    assert again.status_code == 409

    teacher = await login(client, "teacher@example.com")
    assert teacher.status_code == 200 and teacher.json()["user"]["role"] == "teacher"


async def test_only_super_admin_approves_admins(client, db_engine):
    admin = await staff_tokens(client, db_engine, "admin@example.com", "admin")
    owner = await staff_tokens(client, db_engine, "owner@example.com", "super_admin")

    signup = await register(client, "new.admin@example.com", role="admin")
    assert signup["tokens"] is None and "Super Admin" in signup["message"]
    applicant_id = signup["user"]["id"]

    # A regular admin can neither list nor decide administrator applications.
    listing = await client.get(f"{API}/admin-control-plane/approvals/?role=admin", headers=auth(admin))
    assert listing.status_code == 403
    assert (await client.get(f"{API}/admin-control-plane/approvals/", headers=auth(admin))).json()["total"] == 0
    hijack = await client.post(f"{API}/admin-control-plane/approvals/{applicant_id}/approve/", headers=auth(admin))
    assert hijack.status_code == 403

    # Nor can they promote someone to admin by editing roles directly.
    student = await register(client, "student@example.com")
    promote = await client.patch(f"{API}/security-control-plane/users/{student['user']['id']}/override/",
                                 headers=auth(admin), json={"role": "admin"})
    assert promote.status_code == 403

    queue = await client.get(f"{API}/admin-control-plane/approvals/?role=admin", headers=auth(owner))
    assert queue.json()["total"] == 1
    ok = await client.post(f"{API}/admin-control-plane/approvals/{applicant_id}/approve/", headers=auth(owner))
    assert ok.status_code == 200

    new_admin = (await login(client, "new.admin@example.com")).json()
    assert new_admin["user"]["role"] == "admin"

    # Admins cannot edit fellow administrators; the Super Admin can.
    edit = await client.patch(f"{API}/admin-control-plane/users/{applicant_id}/", headers=auth(admin),
                              json={"is_active": False})
    assert edit.status_code == 403
    edit = await client.patch(f"{API}/admin-control-plane/users/{applicant_id}/", headers=auth(owner),
                              json={"full_name": "Renamed Admin"})
    assert edit.status_code == 200


async def test_rejected_application_cannot_sign_in(client, db_engine):
    admin = await staff_tokens(client, db_engine, "admin@example.com", "admin")
    signup = await register(client, "teacher@example.com", role="teacher")
    res = await client.post(f"{API}/admin-control-plane/approvals/{signup['user']['id']}/reject/",
                            headers=auth(admin), json={"note": "Could not verify TSC number"})
    assert res.status_code == 200 and res.json()["approval_status"] == "rejected"

    blocked = await login(client, "teacher@example.com")
    assert blocked.status_code == 403 and "Could not verify TSC number" in blocked.json()["error"]

    history = await client.get(f"{API}/admin-control-plane/approvals/?status=rejected", headers=auth(admin))
    assert history.json()["items"][0]["review_note"] == "Could not verify TSC number"


async def test_super_admin_monitors_all_activity(client, db_engine):
    admin = await staff_tokens(client, db_engine, "admin@example.com", "admin")
    owner = await staff_tokens(client, db_engine, "owner@example.com", "super_admin")

    assert (await login(client, "admin@example.com", "wrong-password")).status_code == 401
    signup = await register(client, "teacher@example.com", role="teacher")
    await client.post(f"{API}/admin-control-plane/approvals/{signup['user']['id']}/approve/", headers=auth(admin))
    # A state-changing call without a dedicated event is still captured.
    await client.post(f"{API}/notifications/mark-all-read/", headers=auth(admin))

    # Only the Super Admin can read the activity log.
    assert (await client.get(f"{API}/security-control-plane/activity/", headers=auth(admin))).status_code == 403

    log = await client.get(f"{API}/security-control-plane/activity/?page_size=200", headers=auth(owner))
    assert log.status_code == 200, log.text
    actions = [e["action"] for e in log.json()["items"]]
    for expected in ("auth.login", "auth.login_failed", "approval.requested", "approval.approved", "account.registered"):
        assert expected in actions, (expected, actions)

    generic = next(e for e in log.json()["items"] if e["action"] == "request.post")
    assert generic["path"] == "/api/v1/notifications/mark-all-read" and generic["status_code"] == 204
    assert generic["actor_email"] == "admin@example.com"

    failed = next(e for e in log.json()["items"] if e["action"] == "auth.login_failed")
    assert failed["actor_email"] == "admin@example.com" and failed["ip_address"]
    approval = next(e for e in log.json()["items"] if e["action"] == "approval.approved")
    assert approval["actor_email"] == "admin@example.com" and approval["request_id"]

    filtered = await client.get(f"{API}/security-control-plane/activity/?category=approval", headers=auth(owner))
    assert {e["category"] for e in filtered.json()["items"]} == {"approval"}
    search = await client.get(f"{API}/security-control-plane/activity/?search=teacher@example", headers=auth(owner))
    assert search.json()["total"] >= 2

    summary = await client.get(f"{API}/security-control-plane/activity/summary/", headers=auth(owner))
    assert summary.status_code == 200 and summary.json()["failed_logins"] == 1

    # Nothing sensitive is ever stored.
    async with db_engine.connect() as conn:
        dump = (await conn.execute(text("SELECT string_agg(details::text || summary, ' ') FROM activity_logs"))).scalar()
    assert PASSWORD not in dump and "wrong-password" not in dump


async def test_only_the_platform_owner_is_super_admin(client, db_engine):
    owner = await staff_tokens(client, db_engine, "owner@example.com", "super_admin")

    # A super_admin role row on any other account grants nothing.
    rogue = await staff_tokens(client, db_engine, "rogue@example.com", "super_admin")
    me = await client.get(f"{API}/auth/me/", headers=auth(rogue))
    assert me.json()["role"] == "student"
    assert (await client.get(f"{API}/admin-control-plane/dashboard/stats/", headers=auth(rogue))).status_code == 403
    assert (await client.get(f"{API}/security-control-plane/activity/", headers=auth(rogue))).status_code == 403

    # Nobody, not even the owner, can hand out the role through the API.
    student = await register(client, "student@example.com")
    grant = await client.patch(f"{API}/security-control-plane/users/{student['user']['id']}/override/",
                               headers=auth(owner), json={"role": "super_admin"})
    assert grant.status_code == 403

    # The owner's e-mail anchors the role, so it cannot be changed from the admin panel.
    owner_id = (await client.get(f"{API}/auth/me/", headers=auth(owner))).json()["id"]
    rename = await client.patch(f"{API}/admin-control-plane/users/{owner_id}/", headers=auth(owner),
                                json={"email": "someone-else@example.com"})
    assert rename.status_code == 403
    assert (await client.delete(f"{API}/users/me/", headers=auth(owner))).status_code == 403
