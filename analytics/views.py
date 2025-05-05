from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from listings.models import Listing
from cars.models import Make, Model, Car


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    @action(detail=False, methods=['get'], url_path='price')
    def price_analytics(self, request):
        listings = Listing.objects.filter(is_active=True)
        avg_price = listings.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        min_price = listings.order_by('price').first().price if listings.exists() else 0
        max_price = listings.order_by('-price').first().price if listings.exists() else 0
        price_ranges = [
            {'min': 0, 'max': 10000, 'label': '0-10000'},
            {'min': 10000, 'max': 20000, 'label': '10000-20000'},
            {'min': 20000, 'max': 30000, 'label': '20000-30000'},
            {'min': 30000, 'max': 50000, 'label': '30000-50000'},
            {'min': 50000, 'max': 100000, 'label': '50000-100000'},
            {'min': 100000, 'max': float('inf'), 'label': '100000+'}
        ]
        price_distribution = []
        total_count = listings.count()
        for price_range in price_ranges:
            count = listings.filter(
                price__gte=price_range['min'],
                price__lt=price_range['max']
            ).count()
            percentage = (count / total_count * 100) if total_count > 0 else 0
            price_distribution.append({
                'range': price_range['label'],
                'count': count,
                'percentage': round(percentage, 2)
            })
        popular_makes = Make.objects.annotate(
            listings_count=Count('cars__listings', filter=Q(cars__listings__is_active=True))
        ).filter(listings_count__gt=0).order_by('-listings_count')[:5]
        popular_makes_data = []
        for make in popular_makes:
            make_listings = listings.filter(car__make=make)
            avg_make_price = make_listings.aggregate(avg_price=Avg('price'))['avg_price'] or 0

            popular_makes_data.append({
                'make': make.name,
                'count': make_listings.count(),
                'average_price': avg_make_price
            })
        return Response({
            'average_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_distribution': price_distribution,
            'popular_makes': popular_makes_data,
            'total_listings': total_count
        })

    @action(detail=False, methods=['get'], url_path='price/makes/(?P<make_id>[^/.]+)')
    def make_price_analytics(self, request, make_id=None):
        try:
            make = Make.objects.get(pk=make_id)
        except Make.DoesNotExist:
            return Response(
                {"detail": "Make not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        listings = Listing.objects.filter(is_active=True, car__make=make)
        if not listings.exists():
            return Response(
                {"detail": "No active listings found for this make."},
                status=status.HTTP_404_NOT_FOUND
            )
        avg_price = listings.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        min_price = listings.order_by('price').first().price
        max_price = listings.order_by('-price').first().price
        price_ranges = [
            {'min': 0, 'max': 10000, 'label': '0-10000'},
            {'min': 10000, 'max': 20000, 'label': '10000-20000'},
            {'min': 20000, 'max': 30000, 'label': '20000-30000'},
            {'min': 30000, 'max': 50000, 'label': '30000-50000'},
            {'min': 50000, 'max': 100000, 'label': '50000-100000'},
            {'min': 100000, 'max': float('inf'), 'label': '100000+'}
        ]
        price_distribution = []
        total_count = listings.count()
        for price_range in price_ranges:
            count = listings.filter(
                price__gte=price_range['min'],
                price__lt=price_range['max']
            ).count()
            percentage = (count / total_count * 100) if total_count > 0 else 0
            price_distribution.append({
                'range': price_range['label'],
                'count': count,
                'percentage': round(percentage, 2)
            })
        popular_models = Model.objects.filter(make=make).annotate(
            listings_count=Count('cars__listings', filter=Q(cars__listings__is_active=True))
        ).filter(listings_count__gt=0).order_by('-listings_count')[:5]
        popular_models_data = []
        for model in popular_models:
            model_listings = listings.filter(car__model=model)
            avg_model_price = model_listings.aggregate(avg_price=Avg('price'))['avg_price'] or 0
            popular_models_data.append({
                'model': model.name,
                'count': model_listings.count(),
                'average_price': avg_model_price
            })
        return Response({
            'make': {
                'id': make.id,
                'name': make.name,
                'country': make.country
            },
            'average_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_distribution': price_distribution,
            'popular_models': popular_models_data,
            'total_listings': total_count
        })

    @action(detail=False, methods=['post'], url_path='price/estimate')
    def estimate_price(self, request):
        # Get car details from request
        make_id = request.data.get('make')
        model_id = request.data.get('model')
        year = request.data.get('year')
        mileage = request.data.get('mileage')
        condition = request.data.get('condition')
        if not all([make_id, model_id, year, mileage, condition]):
            return Response(
                {"detail": "Missing required parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )
        similar_listings = Listing.objects.filter(
            is_active=True,
            car__make_id=make_id,
            car__model_id=model_id,
            condition=condition
        )
        if not similar_listings.exists():
            return Response(
                {"detail": "Not enough data to estimate price."},
                status=status.HTTP_404_NOT_FOUND
            )
        base_price = similar_listings.aggregate(avg_price=Avg('price'))['avg_price']
        year_factor = 0
        year_listings = similar_listings.filter(car__year=year)
        if year_listings.exists():
            year_avg = year_listings.aggregate(avg_price=Avg('price'))['avg_price']
            year_factor = year_avg - base_price
        mileage_factor = 0
        avg_mileage = similar_listings.aggregate(avg_mileage=Avg('car__mileage'))['avg_mileage']
        if avg_mileage:
            mileage_diff = mileage - avg_mileage
            mileage_factor = -0.1 * (mileage_diff / 10000)
        estimated_price = base_price + year_factor + (base_price * mileage_factor)
        estimated_price = max(estimated_price, 0)
        price_range = {
            'min': estimated_price * 0.95,
            'max': estimated_price * 1.05
        }
        most_similar = similar_listings.order_by('car__year')[:2]
        similar_data = []
        for listing in most_similar:
            similarity_score = 1.0
            year_diff = abs(listing.car.year - int(year))
            if year_diff > 0:
                similarity_score -= 0.05 * year_diff
            mileage_diff = abs(listing.car.mileage - int(mileage))
            if mileage_diff > 0:
                similarity_score -= 0.1 * (mileage_diff / 10000)
            similarity_score = max(0.5, similarity_score) 
            similar_data.append({
                'id': listing.id,
                'title': listing.title,
                'price': listing.price,
                'currency': listing.currency,
                'mileage': listing.car.mileage,
                'similarity_score': round(similarity_score, 2)
            })
        factors = []
        if year_factor != 0:
            factors.append({
                'factor': 'year',
                'impact': f"{'+' if year_factor >= 0 else ''}{year_factor:.2f}",
                'description': f"{year} yil modellari o'rtacha {abs(year_factor):.2f} USD {'qimmatroq' if year_factor >= 0 else 'arzonroq'}"
            })
        if mileage_factor != 0:
            mileage_impact = base_price * mileage_factor
            factors.append({
                'factor': 'mileage',
                'impact': f"{'+' if mileage_impact >= 0 else ''}{mileage_impact:.2f}",
                'description': f"{mileage} km yurgan avtomobillar o'rtacha {abs(mileage_impact):.2f} USD {'qimmatroq' if mileage_impact >= 0 else 'arzonroq'}"
            })
        return Response({
            'estimated_price': round(estimated_price, 2),
            'price_range': {
                'min': round(price_range['min'], 2),
                'max': round(price_range['max'], 2)
            },
            'confidence_score': 0.85,
            'similar_listings': similar_data,
            'factors': factors
        })

    @action(detail=False, methods=['get'], url_path='trends')
    def market_trends(self, request):
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)
        three_months_ago = now - timedelta(days=90)
        six_months_ago = now - timedelta(days=180)
        one_year_ago = now - timedelta(days=365)
        current_avg = Listing.objects.filter(
            created_at__gte=one_month_ago
        ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
        three_month_avg = Listing.objects.filter(
            created_at__gte=three_months_ago,
            created_at__lt=one_month_ago
        ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
        six_month_avg = Listing.objects.filter(
            created_at__gte=six_months_ago,
            created_at__lt=three_months_ago
        ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
        one_year_avg = Listing.objects.filter(
            created_at__gte=one_year_ago,
            created_at__lt=six_months_ago
        ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
        one_month_change = ((current_avg - three_month_avg) / three_month_avg * 100) if three_month_avg > 0 else 0
        three_month_change = ((three_month_avg - six_month_avg) / six_month_avg * 100) if six_month_avg > 0 else 0
        six_month_change = ((six_month_avg - one_year_avg) / one_year_avg * 100) if one_year_avg > 0 else 0
        one_year_change = ((current_avg - one_year_avg) / one_year_avg * 100) if one_year_avg > 0 else 0
        price_trends = {
            'last_month': f"{'+' if one_month_change >= 0 else ''}{one_month_change:.1f}%",
            'last_3_months': f"{'+' if three_month_change >= 0 else ''}{three_month_change:.1f}%",
            'last_6_months': f"{'+' if six_month_change >= 0 else ''}{six_month_change:.1f}%",
            'last_year': f"{'+' if one_year_change >= 0 else ''}{one_year_change:.1f}%"
        }
        popular_makes = Make.objects.annotate(
            listings_count=Count('cars__listings', filter=Q(cars__listings__is_active=True))
        ).filter(listings_count__gt=0).order_by('-listings_count')[:5]
        popular_makes_data = []
        total_listings = Listing.objects.filter(is_active=True).count()
        for make in popular_makes:
            make_listings = Listing.objects.filter(car__make=make, is_active=True)
            make_count = make_listings.count()
            percentage = (make_count / total_listings * 100) if total_listings > 0 else 0
            current_make_count = Listing.objects.filter(
                car__make=make, created_at__gte=one_month_ago
            ).count()
            previous_make_count = Listing.objects.filter(
                car__make=make, created_at__gte=three_months_ago, created_at__lt=one_month_ago
            ).count()
            make_trend = ((
                                      current_make_count - previous_make_count) / previous_make_count * 100) if previous_make_count > 0 else 0
            popular_makes_data.append({
                'make': make.name,
                'percentage': round(percentage, 2),
                'trend': f"{'+' if make_trend >= 0 else ''}{make_trend:.1f}%"
            })
        from cars.models import BodyType
        popular_body_types = BodyType.objects.annotate(
            listings_count=Count('cars__listings', filter=Q(cars__listings__is_active=True))
        ).filter(listings_count__gt=0).order_by('-listings_count')[:5]
        body_types_data = []
        for body_type in popular_body_types:
            body_type_listings = Listing.objects.filter(car__body_type=body_type, is_active=True)
            body_type_count = body_type_listings.count()
            percentage = (body_type_count / total_listings * 100) if total_listings > 0 else 0
            current_body_type_count = Listing.objects.filter(
                car__body_type=body_type, created_at__gte=one_month_ago
            ).count()
            previous_body_type_count = Listing.objects.filter(
                car__body_type=body_type, created_at__gte=three_months_ago, created_at__lt=one_month_ago
            ).count()
            body_type_trend = ((
                                           current_body_type_count - previous_body_type_count) / previous_body_type_count * 100) if previous_body_type_count > 0 else 0
            body_types_data.append({
                'body_type': body_type.name,
                'percentage': round(percentage, 2),
                'trend': f"{'+' if body_type_trend >= 0 else ''}{body_type_trend:.1f}%"
            })
        fuel_types = Listing.objects.filter(is_active=True).values('car__fuel_type').annotate(
            count=Count('id')
        ).order_by('-count')
        fuel_types_data = []
        for fuel_type in fuel_types:
            fuel_type_name = fuel_type['car__fuel_type']
            fuel_type_count = fuel_type['count']
            percentage = (fuel_type_count / total_listings * 100) if total_listings > 0 else 0
            current_fuel_type_count = Listing.objects.filter(
                car__fuel_type=fuel_type_name, created_at__gte=one_month_ago
            ).count()
            previous_fuel_type_count = Listing.objects.filter(
                car__fuel_type=fuel_type_name, created_at__gte=three_months_ago, created_at__lt=one_month_ago
            ).count()
            fuel_type_trend = ((
                                           current_fuel_type_count - previous_fuel_type_count) / previous_fuel_type_count * 100) if previous_fuel_type_count > 0 else 0
            fuel_types_data.append({
                'fuel_type': fuel_type_name.capitalize(),
                'percentage': round(percentage, 2),
                'trend': f"{'+' if fuel_type_trend >= 0 else ''}{fuel_type_trend:.1f}%"
            })
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        monthly_listings = []
        current_year = now.year
        for i in range(7):
            month_number = (now.month - i) % 12
            if month_number == 0:
                month_number = 12
            year = current_year if now.month - i > 0 else current_year - 1
            month_start = timezone.datetime(year, month_number, 1, tzinfo=timezone.utc)
            if month_number == 12:
                month_end = timezone.datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                month_end = timezone.datetime(year, month_number + 1, 1, tzinfo=timezone.utc)
            count = Listing.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            monthly_listings.insert(0, {
                'month': months[month_number - 1],
                'count': count
            })

        return Response({
            'price_trends': price_trends,
            'popular_makes': popular_makes_data,
            'popular_body_types': body_types_data,
            'fuel_type_distribution': fuel_types_data,
            'monthly_listings': monthly_listings
        })
