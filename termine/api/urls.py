"""URL configuration for the termine API."""
 
from django.urls import include, path
from rest_framework.routers import DefaultRouter
 
from .views import TerminViewSet
 
router = DefaultRouter()
router.register('', TerminViewSet, basename='termin')
 
urlpatterns = [
    path('', include(router.urls)),
]
 