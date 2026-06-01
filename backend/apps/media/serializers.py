from rest_framework import serializers
from .models import MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    url = serializers.CharField(read_only=True)
    size_mb = serializers.FloatField(read_only=True)

    class Meta:
        model = MediaFile
        fields = [
            "id", "file", "original_name", "file_type", "mime_type",
            "size", "size_mb", "width", "height", "duration",
            "is_public", "cdn_url", "url", "created_at",
        ]
        read_only_fields = ["id", "size_mb", "url", "created_at", "cdn_url"]


class MediaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ["file", "is_public"]

    def create(self, validated_data):
        import mimetypes
        file = validated_data["file"]
        mime_type, _ = mimetypes.guess_type(file.name)
        file_type = self._detect_file_type(mime_type or "")
        validated_data.update(
            {
                "original_name": file.name,
                "size": file.size,
                "mime_type": mime_type or "",
                "file_type": file_type,
                "user": self.context["request"].user,
            }
        )
        return super().create(validated_data)

    @staticmethod
    def _detect_file_type(mime_type: str) -> str:
        if mime_type.startswith("image/"):
            return MediaFile.FileType.IMAGE
        if mime_type == "application/pdf":
            return MediaFile.FileType.PDF
        if mime_type.startswith("video/"):
            return MediaFile.FileType.VIDEO
        if mime_type.startswith("audio/"):
            return MediaFile.FileType.AUDIO
        if mime_type in ("application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
            return MediaFile.FileType.DOCUMENT
        return MediaFile.FileType.OTHER
