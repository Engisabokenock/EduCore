from rest_framework import serializers
from django.db.models import Avg
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_name", "resource", "rating", "comment", "is_approved", "created_at"]
        read_only_fields = ["id", "user_name", "is_approved", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ResourceRatingSerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    review_count = serializers.IntegerField()
