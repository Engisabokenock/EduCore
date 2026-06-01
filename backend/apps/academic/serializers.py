"""
Academic API serializers.

Hierarchy: Grade → Subject → Topic → Resource
Each level serializes its children inline (list view) or nested (detail view).
"""
from rest_framework import serializers
from .models import Grade, Subject, Topic, Enrollment


# ── Grade serializers ─────────────────────────────────────────────────────────

class GradeListSerializer(serializers.ModelSerializer):
    subject_count = serializers.IntegerField(source="subjects.count", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id", "name", "slug", "code", "order",
            "curriculum", "is_active", "subject_count",
        ]


class GradeDetailSerializer(serializers.ModelSerializer):
    subject_count = serializers.IntegerField(source="subjects.count", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id", "name", "slug", "code", "order",
            "curriculum", "is_active", "subject_count", "created_at",
        ]


class GradeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["name", "code", "order", "curriculum", "is_active"]


# ── Subject serializers ───────────────────────────────────────────────────────

class SubjectListSerializer(serializers.ModelSerializer):
    grade = GradeListSerializer(read_only=True)
    grade_id = serializers.UUIDField(write_only=True, source="grade")
    topic_count = serializers.IntegerField(source="topics.count", read_only=True)
    resource_count = serializers.IntegerField(source="resources.count", read_only=True)

    class Meta:
        model = Subject
        fields = [
            "id", "name", "slug", "description", "icon", "color",
            "order", "is_active", "grade", "grade_id",
            "topic_count", "resource_count",
        ]


class SubjectDetailSerializer(SubjectListSerializer):
    class Meta(SubjectListSerializer.Meta):
        fields = SubjectListSerializer.Meta.fields + ["created_at"]


class SubjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["name", "description", "icon", "color", "order", "is_active", "grade"]

    def validate(self, attrs):
        grade = attrs.get("grade") or (self.instance.grade if self.instance else None)
        if not grade:
            raise serializers.ValidationError({"grade": "Grade is required."})
        return attrs


# ── Topic serializers ─────────────────────────────────────────────────────────

class TopicListSerializer(serializers.ModelSerializer):
    subject = SubjectListSerializer(read_only=True)
    subject_id = serializers.UUIDField(write_only=True, source="subject")
    resource_count = serializers.IntegerField(source="resources.count", read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id", "name", "slug", "description", "order",
            "is_active", "subject", "subject_id", "resource_count",
        ]


class TopicDetailSerializer(TopicListSerializer):
    class Meta(TopicListSerializer.Meta):
        fields = TopicListSerializer.Meta.fields + ["created_at"]


class TopicWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["name", "description", "order", "is_active", "subject"]

    def validate(self, attrs):
        subject = attrs.get("subject") or (self.instance.subject if self.instance else None)
        if not subject:
            raise serializers.ValidationError({"subject": "Subject is required."})
        return attrs


# ── Enrollment serializers ────────────────────────────────────────────────────

class EnrollmentSerializer(serializers.ModelSerializer):
    grade = GradeListSerializer(read_only=True)
    grade_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id", "grade", "grade_id", "status",
            "enrolled_at", "completed_at", "created_at",
        ]
        read_only_fields = ["id", "status", "enrolled_at", "completed_at", "created_at"]

    def validate_grade_id(self, value):
        if not Grade.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Grade not found or inactive.")
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        grade_id = validated_data.pop("grade_id")
        validated_data["grade_id"] = grade_id
        return super().create(validated_data)
