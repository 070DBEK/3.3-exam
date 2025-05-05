from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from listings.models import Listing
from listings.serializers import ListingSerializer


class SearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def get_paginated_response(self, queryset, serializer_class, request):
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = serializer_class(result_page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='listings')
    def search_listings(self, request):
        queryset = Listing.objects.filter(is_active=True)
        make = request.query_params.get('make')
        if make:
            queryset = queryset.filter(car__make_id=make)
        model = request.query_params.get('model')
        if model:
            queryset = queryset.filter(car__model_id=model)
        year_min = request.query_params.get('year_min')
        if year_min:
            queryset = queryset.filter(car__year__gte=year_min)
        year_max = request.query_params.get('year_max')
        if year_max:
            queryset = queryset.filter(car__year__lte=year_max)
        price_min = request.query_params.get('price_min')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        price_max = request.query_params.get('price_max')
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        location = request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        condition = request.query_params.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        fuel_type = request.query_params.get('fuel_type')
        if fuel_type:
            queryset = queryset.filter(car__fuel_type=fuel_type)
        transmission = request.query_params.get('transmission')
        if transmission:
            queryset = queryset.filter(car__transmission=transmission)
        body_type = request.query_params.get('body_type')
        if body_type:
            queryset = queryset.filter(car__body_type_id=body_type)
        sort = request.query_params.get('sort')
        if sort:
            if sort == 'price':
                queryset = queryset.order_by('price')
            elif sort == '-price':
                queryset = queryset.order_by('-price')
            elif sort == 'created_at':
                queryset = queryset.order_by('created_at')
            elif sort == '-created_at':
                queryset = queryset.order_by('-created_at')
        return self.get_paginated_response(queryset, ListingSerializer, request)

    @action(detail=False, methods=['get'], url_path='similar/(?P<listing_id>[^/.]+)')
    def similar_listings(self, request, listing_id=None):
        try:
            listing = Listing.objects.get(pk=listing_id)
        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        similar_listings = Listing.objects.filter(
            is_active=True,
            car__make=listing.car.make,
            car__model=listing.car.model
        ).exclude(id=listing.id)
        year_min = listing.car.year - 2
        year_max = listing.car.year + 2
        similar_listings = similar_listings.filter(
            car__year__gte=year_min,
            car__year__lte=year_max
        )
        price_min = listing.price * 0.8
        price_max = listing.price * 1.2
        similar_listings = similar_listings.filter(
            price__gte=price_min,
            price__lte=price_max
        )
        similar_listings = similar_listings[:5]
        serializer = ListingSerializer(similar_listings, many=True, context={'request': request})
        return Response(serializer.data)
