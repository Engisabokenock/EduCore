"""Academic business logic."""
from django.db import transaction
from .models import Grade, Subject, Topic, Enrollment


def get_curriculum_tree(curriculum: str = "CBC") -> list:
    grades = Grade.objects.filter(is_active=True, curriculum=curriculum).prefetch_related(
        "subjects__topics"
    )
    from .serializers import GradeSerializer
    return GradeSerializer(grades, many=True).data


def enroll_student(user, grade_id: str) -> Enrollment:
    grade = Grade.objects.get(id=grade_id, is_active=True)
    enrollment, created = Enrollment.objects.get_or_create(
        user=user, grade=grade,
        defaults={"status": Enrollment.Status.ACTIVE},
    )
    if not created and enrollment.status == Enrollment.Status.SUSPENDED:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])
    return enrollment


def get_student_grades(user) -> list:
    return Enrollment.objects.filter(
        user=user, status=Enrollment.Status.ACTIVE
    ).select_related("grade").values_list("grade", flat=True)
