"""
Seed database with CBC Kenya curriculum structure.

Run with:
    cd backend
    python manage.py shell < ../scripts/seed_database.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.utils.text import slugify
from apps.academic.models import Grade, Subject, Topic
from apps.commerce.models import Plan
from decimal import Decimal

print("=== Seeding CBC Kenya Curriculum ===\n")

# ── Grades ─────────────────────────────────────────────────────────────────────
GRADES = [
    ("PP1",      "pp1",      1),
    ("PP2",      "pp2",      2),
    ("Grade 1",  "grade-1",  3),
    ("Grade 2",  "grade-2",  4),
    ("Grade 3",  "grade-3",  5),
    ("Grade 4",  "grade-4",  6),
    ("Grade 5",  "grade-5",  7),
    ("Grade 6",  "grade-6",  8),
    ("Grade 7",  "grade-7",  9),
    ("Grade 8",  "grade-8",  10),
    ("Grade 9",  "grade-9",  11),
    ("Grade 10", "grade-10", 12),
    ("Grade 11", "grade-11", 13),
    ("Grade 12", "grade-12", 14),
]

created_grades = 0
for name, code, order in GRADES:
    _, created = Grade.objects.get_or_create(
        code=code,
        defaults={"name": name, "order": order, "curriculum": "CBC", "is_active": True},
    )
    if created:
        created_grades += 1
print(f"Grades: {created_grades} created | {Grade.objects.count()} total")

# ── Subjects ───────────────────────────────────────────────────────────────────
SUBJECTS = {
    "grade-1": [
        ("Mathematics", "📐", "#3B82F6"),
        ("English", "📖", "#10B981"),
        ("Kiswahili", "🗣️", "#F59E0B"),
        ("Environmental Activities", "🌿", "#22C55E"),
        ("Hygiene & Nutrition", "🧼", "#EC4899"),
        ("Religious Education", "✝️", "#8B5CF6"),
        ("Creative Arts", "🎨", "#F97316"),
    ],
    "grade-4": [
        ("Mathematics", "📐", "#3B82F6"),
        ("English", "📖", "#10B981"),
        ("Kiswahili", "🗣️", "#F59E0B"),
        ("Science & Technology", "🔬", "#06B6D4"),
        ("Social Studies", "🌍", "#84CC16"),
        ("Religious Education", "✝️", "#8B5CF6"),
        ("Creative Arts & Sports", "🎨", "#F97316"),
        ("Agriculture", "🌱", "#22C55E"),
        ("Home Science", "🏠", "#EC4899"),
    ],
    "grade-5": [
        ("Mathematics", "📐", "#3B82F6"),
        ("English", "📖", "#10B981"),
        ("Kiswahili", "🗣️", "#F59E0B"),
        ("Science & Technology", "🔬", "#06B6D4"),
        ("Social Studies", "🌍", "#84CC16"),
        ("Religious Education", "✝️", "#8B5CF6"),
        ("Creative Arts & Sports", "🎨", "#F97316"),
        ("Agriculture", "🌱", "#22C55E"),
        ("Home Science", "🏠", "#EC4899"),
    ],
    "grade-7": [
        ("Mathematics", "📐", "#3B82F6"),
        ("English", "📖", "#10B981"),
        ("Kiswahili", "🗣️", "#F59E0B"),
        ("Integrated Science", "🔬", "#06B6D4"),
        ("Social Studies", "🌍", "#84CC16"),
        ("Agriculture & Nutrition", "🌱", "#22C55E"),
        ("Pre-Technical Studies", "⚙️", "#6B7280"),
        ("Creative Arts", "🎨", "#F97316"),
        ("Business Studies", "💼", "#64748B"),
        ("Religious Education", "✝️", "#8B5CF6"),
    ],
}

created_subjects = 0
for grade_code, subjects in SUBJECTS.items():
    try:
        grade = Grade.objects.get(code=grade_code)
    except Grade.DoesNotExist:
        continue
    for i, (name, icon, color) in enumerate(subjects):
        _, created = Subject.objects.get_or_create(
            grade=grade, slug=slugify(name),
            defaults={"name": name, "icon": icon, "color": color, "order": i + 1, "is_active": True},
        )
        if created:
            created_subjects += 1
print(f"Subjects: {created_subjects} created | {Subject.objects.count()} total")

# ── Topics for Grade 5 Mathematics ────────────────────────────────────────────
GRADE5_MATH_TOPICS = [
    "Numbers up to 100,000",
    "Place Value",
    "Fractions",
    "Decimals",
    "Percentages",
    "Ratio and Proportion",
    "Measurement — Length",
    "Measurement — Area",
    "Measurement — Volume and Capacity",
    "Time",
    "Money",
    "Geometry — 2D Shapes",
    "Geometry — 3D Shapes",
    "Data Handling",
    "Algebra Basics",
]

created_topics = 0
try:
    math5 = Subject.objects.get(grade__code="grade-5", slug="mathematics")
    for i, name in enumerate(GRADE5_MATH_TOPICS):
        _, created = Topic.objects.get_or_create(
            subject=math5, slug=slugify(name),
            defaults={"name": name, "order": i + 1, "is_active": True},
        )
        if created:
            created_topics += 1
except Subject.DoesNotExist:
    pass
print(f"Topics: {created_topics} created | {Topic.objects.count()} total")

# ── Subscription Plans ─────────────────────────────────────────────────────────
PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "description": "Access free materials and browse all content.",
        "price": Decimal("0.00"),
        "billing_cycle": "monthly",
        "features": [
            "Access to all free notes and worksheets",
            "Browse all grades, subjects, and topics",
            "Search and discover content",
            "Up to 5 free downloads per month",
        ],
        "sort_order": 1,
        "is_featured": False,
    },
    {
        "slug": "monthly",
        "name": "Monthly Premium",
        "description": "Unlimited access to all premium content.",
        "price": Decimal("299.00"),
        "billing_cycle": "monthly",
        "features": [
            "Unlimited downloads — all content types",
            "Past papers with full answer sheets",
            "All worksheets and revision guides",
            "Video and audio lessons",
            "Priority email support",
        ],
        "sort_order": 2,
        "is_featured": True,
    },
    {
        "slug": "annual",
        "name": "Annual Premium",
        "description": "Best value — equivalent to 10 months.",
        "price": Decimal("2490.00"),
        "billing_cycle": "annual",
        "features": [
            "Everything in Monthly Premium",
            "2 months free (save KES 1,098)",
            "Early access to new materials",
            "Offline download capability",
            "Family sharing (up to 3 students)",
        ],
        "sort_order": 3,
        "is_featured": False,
    },
]

created_plans = 0
for plan_data in PLANS:
    _, created = Plan.objects.get_or_create(slug=plan_data["slug"], defaults=plan_data)
    if created:
        created_plans += 1
print(f"Plans: {created_plans} created | {Plan.objects.count()} total")

print("\n=== Seed complete! ===")
