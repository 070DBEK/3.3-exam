from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'listings', views.ListingViewSet)
router.register(r'saved-listings', views.SavedListingViewSet, basename='saved-listings')
router.register(r'comparison-lists', views.ComparisonListViewSet, basename='comparison-lists')
listings_router = DefaultRouter()
listings_router.register(r'images', views.ImageViewSet, basename='listing-images')


urlpatterns = [
    path('', include(router.urls)),
    path('listings/<int:listing_pk>/', include(listings_router.urls)),
]
