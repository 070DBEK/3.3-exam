from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Review
from .serializers import ReviewSerializer
from core.permissions import IsOwnerOrReadOnly


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reviewed_user', 'listing']
    ordering_fields = ['rating', 'created_at']

    @action(detail=False, methods=['get'], url_path='users/(?P<user_id>[^/.]+)')
    def user_reviews(self, request, user_id=None):
        reviews = Review.objects.filter(reviewed_user_id=user_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='listings/(?P<listing_id>[^/.]+)')
    def listing_reviews(self, request, listing_id=None):
        reviews = Review.objects.filter(listing_id=listing_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
