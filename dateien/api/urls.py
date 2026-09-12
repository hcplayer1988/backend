"""URL configuration for the dateien API."""
 
from django.urls import include, path
from rest_framework.routers import DefaultRouter
 
from .views import DateiViewSet
 
router = DefaultRouter()
router.register('', DateiViewSet, basename='dateien')
 
urlpatterns = [
    path('', include(router.urls)),
]
 
 
 