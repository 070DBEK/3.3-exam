from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'makes', views.MakeViewSet)
router.register(r'models', views.ModelViewSet)
router.register(r'body-types', views.BodyTypeViewSet)
router.register(r'features', views.FeatureViewSet)
router.register(r'cars', views.CarViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
