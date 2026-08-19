"""URL configuration for the accounts API."""
 
from django.urls import include, path
from rest_framework.routers import DefaultRouter
 
from .views import (
    CookieTokenRefreshView, InviteCreateView, LoginView, LogoutView, MeView,
    MitgliederViewSet, PasswordConfirmView, PasswordResetView, RegisterView,
)
 
router = DefaultRouter()
router.register('mitglieder', MitgliederViewSet, basename='mitglieder')
 
urlpatterns = [
    path('invite/', InviteCreateView.as_view(), name='invite'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordConfirmView.as_view(), name='password_confirm'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
 
 