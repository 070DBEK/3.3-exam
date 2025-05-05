from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Listing, Image, PriceHistory, SavedListing, ComparisonList
from .serializers import (
    ListingSerializer,
    ImageSerializer,
    PriceHistorySerializer,
    SavedListingSerializer,
    ComparisonListSerializer
)
from core.permissions import IsOwnerOrReadOnly, IsSellerOrReadOnly


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsSellerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['car__make', 'car__model', 'car__year', 'car__body_type', 'car__fuel_type',
                        'car__transmission', 'location', 'condition', 'is_active', 'is_featured']
    search_fields = ['title', 'description', 'car__make__name', 'car__model__name']
    ordering_fields = ['price', 'created_at', 'views_count']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = Listing.objects.filter(is_featured=True, is_active=True)
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my(self, request):
        my_listings = Listing.objects.filter(seller=request.user)
        serializer = self.get_serializer(my_listings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        listing = self.get_object()
        images = Image.objects.filter(listing=listing)
        serializer = ImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def images(self, request, pk=None):
        listing = self.get_object()
        serializer = ImageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(listing=listing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def price_history(self, request, pk=None):
        listing = self.get_object()
        history = PriceHistory.objects.filter(listing=listing)
        serializer = PriceHistorySerializer(history, many=True)
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsSellerOrReadOnly]

    def get_queryset(self):
        listing_id = self.kwargs.get('listing_pk')
        if listing_id:
            return Image.objects.filter(listing_id=listing_id)
        return Image.objects.none()


class SavedListingViewSet(viewsets.ModelViewSet):
    serializer_class = SavedListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedListing.objects.filter(user=self.request.user)


class ComparisonListViewSet(viewsets.ModelViewSet):
    serializer_class = ComparisonListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return ComparisonList.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='add')
    def add_listing(self, request, pk=None):
        comparison_list = self.get_object()
        listing_id = request.data.get('listing_id')

        if not listing_id:
            return Response(
                {"detail": "Listing ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            listing = Listing.objects.get(pk=listing_id)
            comparison_list.listings.add(listing)
            serializer = self.get_serializer(comparison_list)
            return Response(serializer.data)
        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='remove')
    def remove_listing(self, request, pk=None):
        comparison_list = self.get_object()
        listing_id = request.data.get('listing_id')

        if not listing_id:
            return Response(
                {"detail": "Listing ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            listing = Listing.objects.get(pk=listing_id)
            comparison_list.listings.remove(listing)
            serializer = self.get_serializer(comparison_list)
            return Response(serializer.data)
        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )
