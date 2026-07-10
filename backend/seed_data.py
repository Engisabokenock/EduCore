"""
EduCore Operational Master Blueprint — Database Fixture Seed Engine.

Seeds the database with data that matches the frontend exactly:
- Grades 1-7 (matching homepage grade buttons)
- Popular CBC subjects (matching homepage subject cards)
- Subscription pricing plans (matching pricing page)
"""
import asyncio
import json
from decimal import Decimal

from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.cbc import Grade, Subject, Topic, LearningOutcome
from app.models.subscription import SubscriptionPlan, PlanTier


POPULAR_SUBJECTS = [
    {"name": "Mathematics", "slug": "mathematics", "icon": "🔢", "color": "bg-blue-50 text-blue-700 border-blue-100"},
    {"name": "English", "slug": "english", "icon": "📖", "color": "bg-purple-50 text-purple-700 border-purple-100"},
    {"name": "Kiswahili", "slug": "kiswahili", "icon": "🗣️", "color": "bg-green-50 text-green-700 border-green-100"},
    {"name": "Science", "slug": "science", "icon": "🔬", "color": "bg-cyan-50 text-cyan-700 border-cyan-100"},
    {"name": "Social Studies", "slug": "social-studies", "icon": "🌍", "color": "bg-amber-50 text-amber-700 border-amber-100"},
    {"name": "CRE / IRE", "slug": "cre-ire", "icon": "🕌", "color": "bg-teal-50 text-teal-700 border-teal-100"},
    {"name": "Creative Arts", "slug": "creative-arts", "icon": "🎨", "color": "bg-pink-50 text-pink-700 border-pink-100"},
    {"name": "Design", "slug": "design", "icon": "✏️", "color": "bg-orange-50 text-orange-700 border-orange-100"},
]

GRADE_CODES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
GRADE_NAMES = {
    "G1": "Grade 1", "G2": "Grade 2", "G3": "Grade 3",
    "G4": "Grade 4", "G5": "Grade 5", "G6": "Grade 6", "G7": "Grade 7",
}

PLAN_TIERS = [
    {
        "name": "Weekly Pass",
        "tier": PlanTier.WEEKLY,
        "price": Decimal("100.00"),
        "duration_days": 7,
        "description": "Perfect for quick revision before a test.",
        "features": ["Unlimited downloads", "Access to all grades", "Cancel anytime"],
        "is_featured": False,
        "sort_order": 1,
    },
    {
        "name": "Monthly Pass",
        "tier": PlanTier.MONTHLY,
        "price": Decimal("350.00"),
        "duration_days": 30,
        "description": "Most popular plan for regular learners.",
        "features": ["Unlimited downloads", "Access to all grades", "Priority support", "Cancel anytime"],
        "is_featured": True,
        "sort_order": 2,
    },
    {
        "name": "Quarterly Pass",
        "tier": PlanTier.QUARTERLY,
        "price": Decimal("900.00"),
        "duration_days": 90,
        "description": "Save more with a 3-month revision pass.",
        "features": ["Unlimited downloads", "Access to all grades", "Priority support", "Early access to new exams"],
        "is_featured": False,
        "sort_order": 3,
    },
    {
        "name": "Yearly Revision Pass",
        "tier": PlanTier.YEARLY,
        "price": Decimal("2500.00"),
        "duration_days": 365,
        "description": "Best value — full-year access to every resource.",
        "features": ["Unlimited downloads", "Access to all grades", "Priority support", "Early access to new exams", "Exclusive revision sets"],
        "is_featured": False,
        "sort_order": 4,
    },
]


async def seed_grades(session):
    grade_ids = {}
    for code in GRADE_CODES:
        stmt = select(Grade).where(Grade.code == code)
        result = await session.execute(stmt)
        grade = result.scalar_one_or_none()
        if not grade:
            grade = Grade(
                name=GRADE_NAMES[code],
                code=code,
                slug=f"grade-{int(code[1:])}",
                description=f"CBC Curriculum {GRADE_NAMES[code]}",
                curriculum="CBC",
                is_active=True,
                order=len(grade_ids) + 1,
            )
            session.add(grade)
            await session.flush()
        grade_ids[code] = grade.id
    return grade_ids


async def seed_subjects(session, grade_ids):
    for code in GRADE_CODES:
        grade_id = grade_ids[code]
        for idx, subj in enumerate(POPULAR_SUBJECTS):
            stmt = select(Subject).where(
                Subject.grade_id == grade_id,
                Subject.slug == subj["slug"],
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                continue

            subject = Subject(
                grade_id=grade_id,
                name=subj["name"],
                code=f"{code}-{subj['slug'][:3].upper()}",
                slug=subj["slug"],
                description=f"CBC {subj['name']} Resource Book — {GRADE_NAMES[code]}",
                icon=subj["icon"],
                color=subj["color"],
                is_active=True,
                order=idx + 1,
            )
            session.add(subject)
            await session.flush()

            # Add starter topics so subject pages are not empty
            starter_topic = Topic(
                subject_id=subject.id,
                name="General",
                slug="general",
                ordering=1,
                is_active=True,
            )
            session.add(starter_topic)
            await session.flush()
            session.add(LearningOutcome(topic_id=starter_topic.id, statement="Explore all resources for this subject."))


async def seed_plans(session):
    for plan in PLAN_TIERS:
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.tier == plan["tier"])
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            continue

        features_json = json.dumps(plan["features"])
        new_plan = SubscriptionPlan(
            name=plan["name"],
            tier=plan["tier"],
            price=plan["price"],
            duration_days=plan["duration_days"],
            is_available=True,
            description=plan["description"],
            features=features_json,
            is_featured=plan["is_featured"],
            sort_order=plan["sort_order"],
        )
        session.add(new_plan)


async def main():
    print("[SEED] Initializing EduCore Database Fixture Seed Engine...")
    async with AsyncSessionLocal() as session:
        grade_ids = await seed_grades(session)
        print("[OK] Grades 1 to 7 successfully verified and seeded.")

        await seed_subjects(session, grade_ids)
        print("[OK] Popular CBC subjects and starter topics seeded across all grades.")

        await seed_plans(session)
        await session.commit()
        print("[OK] Subscription pricing plans seeded.")
        print("[DONE] EduCore database fixtures are fully aligned with the frontend.")


if __name__ == "__main__":
    asyncio.run(main())
