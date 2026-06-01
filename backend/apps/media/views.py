from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MediaFile
from .serializers import MediaFileSerializer, MediaUploadSerializer


class MediaUploadView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MediaUploadSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(MediaFileSerializer(instance).data, status=status.HTTP_201_CREATED)


class MediaListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MediaFileSerializer

    def get_queryset(self):
        return MediaFile.objects.filter(user=self.request.user).order_by("-created_at")


class MediaDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MediaFileSerializer

    def get_queryset(self):
        return MediaFile.objects.filter(user=self.request.user)
