"""Application lifespan events."""
import logging
from sqlalchemy import text
from app.core.database import Base, engine, AsyncSession
from app.models import cbc

logger = logging.getLogger("educore.lifespan")

CBC_SEED_DATA = [
    {
        "grade": {"name": "Grade 1", "code": "G1", "slug": "grade-1", "description": "Grade 1 CBC Curriculum", "curriculum": "CBC", "is_active": True, "order": 1},
        "subjects": [
            {"name": "Mathematics", "code": "G1-MATH", "slug": "mathematics", "icon": "🔢", "color": "bg-blue-50 text-blue-700", "order": 1, "topics": [
                {"name": "Numbers", "slug": "numbers", "order": 1, "outcomes": ["Count objects up to 50", "Write numbers 1-50"]},
                {"name": "Addition", "slug": "addition", "order": 2, "outcomes": ["Add single digit numbers", "Solve simple word problems"]},
            ]},
            {"name": "English", "code": "G1-ENG", "slug": "english", "icon": "📖", "color": "bg-purple-50 text-purple-700", "order": 2, "topics": [
                {"name": "Phonics", "slug": "phonics", "order": 1, "outcomes": ["Identify letter sounds", "Blend sounds to read words"]},
                {"name": "Writing", "slug": "writing", "order": 2, "outcomes": ["Write simple sentences", "Use capital letters and full stops"]},
            ]},
        ],
    },
    {
        "grade": {"name": "Grade 2", "code": "G2", "slug": "grade-2", "description": "Grade 2 CBC Curriculum", "curriculum": "CBC", "is_active": True, "order": 2},
        "subjects": [
            {"name": "Kiswahili", "code": "G2-KIS", "slug": "kiswahili", "icon": "🗣️", "color": "bg-green-50 text-green-700", "order": 1, "topics": [
                {"name": "SOMA", "slug": "soma", "order": 1, "outcomes": ["Read simple Swahili texts", "Identify main ideas"]},
            ]},
            {"name": "Science", "code": "G2-SCI", "slug": "science", "icon": "🔬", "color": "bg-cyan-50 text-cyan-700", "order": 2, "topics": [
                {"name": "Living Things", "slug": "living-things", "order": 1, "outcomes": ["Classify plants and animals", "Identify parts of a plant"]},
            ]},
        ],
    },
    {
        "grade": {"name": "Grade 3", "code": "G3", "slug": "grade-3", "description": "Grade 3 CBC Curriculum", "curriculum": "CBC", "is_active": True, "order": 3},
        "subjects": [
            {"name": "Social Studies", "code": "G3-SST", "slug": "social-studies", "icon": "🌍", "color": "bg-amber-50 text-amber-700", "order": 1, "topics": [
                {"name": "Our Environment", "slug": "our-environment", "order": 1, "outcomes": ["Describe local environment", "Identify environmental hazards"]},
            ]},
            {"name": "Creative Arts", "code": "G3-CRE", "slug": "creative-arts", "icon": "🎨", "color": "bg-pink-50 text-pink-700", "order": 2, "topics": [
                {"name": "Drawing", "slug": "drawing", "order": 1, "outcomes": ["Use different drawing materials", "Create a simple composition"]},
            ]},
        ],
    },
    {
        "grade": {"name": "Grade 4", "code": "G4", "slug": "grade-4", "description": "Grade 4 CBC Curriculum", "curriculum": "CBC", "is_active": True, "order": 4},
        "subjects": [
            {"name": "CRE / IRE", "code": "G4-CRE", "slug": "cre-ire", "icon": "🕌", "color": "bg-teal-50 text-teal-700", "order": 1, "topics": [
                {"name": "Creation", "slug": "creation", "order": 1, "outcomes": ["Describe creation story", "Discuss stewardship"]},
            ]},
            {"name": "Design", "code": "G4-DES", "slug": "design", "icon": "✏️", "color": "bg-orange-50 text-orange-700", "order": 2, "topics": [
                {"name": "Design Process", "slug": "design-process", "order": 1, "outcomes": ["Identify design needs", "Sketch design ideas"]},
            ]},
        ],
    },
]


async def _seed_cbc_if_empty():
    from sqlalchemy.future import select
    from app.models.cbc import Grade

    async with AsyncSession(engine) as session:
        result = await session.execute(select(Grade).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        logger.info("Seeding CBC curriculum data...")
        GradeModel = cbc.Grade
        SubjectModel = cbc.Subject
        TopicModel = cbc.Topic
        OutcomeModel = cbc.LearningOutcome

        for entry in CBC_SEED_DATA:
            grade = GradeModel(**entry["grade"])
            session.add(grade)
            await session.flush()

            for subj in entry["subjects"]:
                topic_datas = list(subj.get("topics", []))
                subject_data = {k: v for k, v in subj.items() if k != "topics"}
                subject = SubjectModel(grade_id=grade.id, **subject_data)
                session.add(subject)
                await session.flush()

                for idx, topic in enumerate(topic_datas):
                    outcomes = list(topic.get("outcomes", []))
                    topic_data = {k: v for k, v in topic.items() if k != "outcomes"}
                    t = TopicModel(subject_id=subject.id, ordering=idx + 1, **topic_data)
                    session.add(t)
                    await session.flush()
                    for outcome_text in outcomes:
                        session.add(OutcomeModel(topic_id=t.id, statement=outcome_text))

        await session.commit()
        logger.info("CBC seed complete")


async def _add_missing_columns():
    """Best-effort migration for CBC tables when the DB was created with an older model."""
    statements = [
        text('ALTER TABLE cbc_grades ADD COLUMN IF NOT EXISTS slug VARCHAR(50)'),
        text('ALTER TABLE cbc_grades ADD COLUMN IF NOT EXISTS curriculum VARCHAR(20) DEFAULT \'CBC\' NOT NULL'),
        text('ALTER TABLE cbc_grades ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL'),
        text('ALTER TABLE cbc_grades ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0 NOT NULL'),
        text('ALTER TABLE cbc_subjects ADD COLUMN IF NOT EXISTS icon VARCHAR(10)'),
        text('ALTER TABLE cbc_subjects ADD COLUMN IF NOT EXISTS color VARCHAR(50)'),
        text('ALTER TABLE cbc_subjects ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL'),
        text('ALTER TABLE cbc_subjects ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0 NOT NULL'),
        text('ALTER TABLE cbc_topics ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL'),
    ]
    async with engine.begin() as conn:
        for stmt in statements:
            try:
                await conn.execute(stmt)
            except Exception as exc:
                logger.warning(f"Column migration skipped for statement: {stmt} ({exc})")


async def startup_create_tables():
    """
    Ensure all ORM tables exist in the database on startup.
    """
    from app.models import (
        base,
        analytics,
        cbc,
        download,
        grade,
        notification,
        payment,
        resource,
        review,
        school,
        subject,
        subscription,
        topic,
        tracking,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured via startup_create_tables")

    await _add_missing_columns()
    await _seed_cbc_if_empty()
