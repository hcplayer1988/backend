"""URL configuration for the accounts API."""
 
from django.urls import include, path
from rest_framework.routers import DefaultRouter
 
from .views import (
    ChangeCredentialsView, CookieTokenRefreshView, EinladungViewSet, EmailChangeConfirmView,
    InviteCreateView, LoginView, LogoutView, MeView, MitgliederViewSet, PasswordConfirmView,
    PasswordResetView, RegisterView, RolleListView,
)
 
router = DefaultRouter()
router.register('mitglieder', MitgliederViewSet, basename='mitglieder')
router.register('einladungen', EinladungViewSet, basename='einladungen')
 
urlpatterns = [
    path('invite/', InviteCreateView.as_view(), name='invite'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordConfirmView.as_view(), name='password_confirm'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('change-credentials/', ChangeCredentialsView.as_view(), name='change_credentials'),
    path('email_change_confirm/<str:token>/', EmailChangeConfirmView.as_view(), name='email_change_confirm'),
    path('rollen/', RolleListView.as_view(), name='rollen_list'),
    path('', include(router.urls)),
]
 
 