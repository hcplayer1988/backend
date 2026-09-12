"""URL configuration for the dateien API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DateiViewSet, OrdnerViewSet

router = DefaultRouter()

router.register("ordner", OrdnerViewSet, basename="ordner")
router.register("", DateiViewSet, basename="datei")

urlpatterns = [
    path("", include(router.urls)),
]
