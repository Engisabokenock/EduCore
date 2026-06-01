"""
Resource serializers.

Three serializer tiers:
  ResourceListSerializer   — lightweight, for list endpoints
  ResourceDetailSerializer — full detail including file URLs and access flag
  ResourceWriteSerializer  — for create/update by teachers/admins
"""
from rest_framework import serializers
from apps.academic.models import Grade, Subject, Topic
from .models import Resource, Download


# ── Inline academic serializers (compact for embedding) ──────────────────────

class GradeInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "name", "slug", "code", "curriculum"]


class SubjectInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "icon", "color"]


class TopicInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "slug"]


# ── Resource serializers ─────────────────────────────────────────────────────

class ResourceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no heavy file URLs."""
    grade = GradeInlineSerializer(read_only=True)
    subject = SubjectInlineSerializer(read_only=True)
    topic = TopicInlineSerializer(read_only=True)
    resource_type_display = serializers.CharField(source="get_resource_type_display", read_only=True)
    term_display = serializers.CharField(source="get_term_display", read_only=True)
    has_answer_sheet = serializers.BooleanField(read_only=True)

    class Meta:
        model = Resource
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "resource_type",
            "resource_type_display",
            "grade",
            "subject",
            "topic",
            "term",
            "term_display",
            "year",
            "tags",
            "thumbnail",
            "file_type",
            "file_size",
            "is_premium",
            "has_answer_sheet",
            "view_count",
            "download_count",
            "is_published",
            "published_at",
            "created_at",
        ]


class ResourceDetailSerializer(ResourceListSerializer):
    """Full detail serializer — includes file URLs and per-user access flag."""
    can_access = serializers.SerializerMethodField()
    can_access_answer_sheet = serializers.SerializerMethodField()
    pdf_file_url = serializers.SerializerMethodField()
    answer_sheet_url = serializers.SerializerMethodField()
    external_url = serializers.URLField(read_only=True)

    class Meta(ResourceListSerializer.Meta):
        fields = ResourceListSerializer.Meta.fields + [
            "pdf_file_url",
            "answer_sheet_url",
            "external_url",
            "can_access",
            "can_access_answer_sheet",
        ]

    def _user_has_subscription(self) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if request.user.role == "admin":
            return True
        return request.user.subscriptions.filter(status="active").exists()

    def get_can_access(self, obj: Resource) -> bool:
        if not obj.is_premium:
            return True
        return self._user_has_subscription()

    def get_can_access_answer_sheet(self, obj: Resource) -> bool:
        # Answer sheets are always premium-gated, even if resource is free
        return self._user_has_subscription()

    def get_pdf_file_url(self, obj: Resource) -> str | None:
        if not self.get_can_access(obj):
            return None
        request = self.context.get("request")
        if obj.pdf_file:
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return obj.external_url or None

    def get_answer_sheet_url(self, obj: Resource) -> str | None:
        if not self.get_can_access_answer_sheet(obj):
            return None
        request = self.context.get("request")
        if obj.answer_sheet:
            return request.build_absolute_uri(obj.answer_sheet.url) if request else obj.answer_sheet.url
        return None


class ResourceWriteSerializer(serializers.ModelSerializer):
    """
    For POST/PUT/PATCH by teachers and admins.
    Validates academic hierarchy: subject must belong to grade;
    topic must belong to subject.
    """

    class Meta:
        model = Resource
        fields = [
            "title",
            "description",
            "resource_type",
            "grade",
            "subject",
            "topic",
            "term",
            "year",
            "tags",
            "pdf_file",
            "answer_sheet",
            "thumbnail",
            "external_url",
            "file_size",
            "file_type",
            "is_premium",
            "is_published",
        ]

    def validate(self, attrs):
        grade = attrs.get("grade") or (self.instance.grade if self.instance else None)
        subject = attrs.get("subject") or (self.instance.subject if self.instance else None)
        topic = attrs.get("topic")

        if grade and subject and subject.grade_id != grade.id:
            raise serializers.ValidationError(
                {"subject": f"Subject '{subject.name}' does not belong to Grade '{grade.name}'."}
            )

        if topic and subject and topic.subject_id != subject.id:
            raise serializers.ValidationError(
                {"topic": f"Topic '{topic.name}' does not belong to Subject '{subject.name}'."}
            )

        if not attrs.get("pdf_file") and not attrs.get("external_url"):
            if not self.instance:
                raise serializers.ValidationError(
                    "Either 'pdf_file' or 'external_url' is required."
                )

        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


# ── Download serializer ──────────────────────────────────────────────────────

class DownloadSerializer(serializers.ModelSerializer):
    resource = ResourceListSerializer(read_only=True)
    resource_id = serializers.UUIDField(write_only=True, source="resource")

    class Meta:
        model = Download
        fields = ["id", "resource", "resource_id", "downloaded_at"]
        read_only_fields = ["id", "downloaded_at"]
