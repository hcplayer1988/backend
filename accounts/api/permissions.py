"""Custom authentication and permission classes for the accounts API."""
 
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
 
 
class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication that reads the access token from an httpOnly cookie
    instead of the Authorization header."""
 
    def authenticate(self, request):
        """Validates the 'access_token' cookie and returns (user, token) or None."""
        access_token = request.COOKIES.get('access_token')
        if access_token is None:
            return None
        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError):
            return None
 
 
class IsVorstand(BasePermission):
    """Grants access only to authenticated users with the Vorstand or Admin role."""
 
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and (user.has_rolle('vorstand') or user.has_rolle('admin'))
        )
 
 
class IsAdminRolle(BasePermission):
    """Grants access only to authenticated users with the Admin role."""
 
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.has_rolle('admin'))
 
 
class IsSuperUser(BasePermission):
    """Grants access only to the platform owner (Django's is_superuser flag).
 
    Used for actions reserved for the owner alone, e.g. hard-deleting or
    reactivating a member account.
    """
 
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
 
 
 
 