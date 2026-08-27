"""URL configuration for the forum API."""
 
from django.urls import include, path
from rest_framework.routers import DefaultRouter
 
from .views import BeitragViewSet, KommentarViewSet
 
router = DefaultRouter()
router.register('beitraege', BeitragViewSet, basename='beitrag')
router.register('kommentare', KommentarViewSet, basename='kommentar')
 
urlpatterns = [
    path('', include(router.urls)),
]
 




































