"""Views for the accounts API (invites, registration, login, profile)."""
 
from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
 
from ..models import Einladung, EmailAenderung, Rolle
from .permissions import IsAdminRolle, IsSuperUser, IsVorstand
from .serializers import (
    ChangeCredentialsSerializer, EmailTokenObtainPairSerializer, InviteCreateSerializer,
    MitgliederManageSerializer, PasswordConfirmSerializer, RegistrationSerializer,
    RolleSerializer, UserSerializer,
)
from .utils import (
    build_user_response, delete_auth_cookies, generate_uid_and_token,
    get_user_from_uid, is_valid_activation_token, send_email_change_confirm_email,
    send_email_change_notice_email, send_invite_email, send_password_reset_email,
    set_auth_cookies,
)
 
User = get_user_model()
 
 
class InviteCreateView(APIView):
    """Allows board members/admins to invite a new member by email."""
 
    permission_classes = [IsVorstand]
 
    def post(self, request):
        """Creates an invite for the given email/role and sends the invite email."""
        serializer = InviteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rolle, _ = Rolle.objects.get_or_create(name=serializer.validated_data['rolle'])
        einladung = Einladung.objects.create(
            email=serializer.validated_data['email'],
            rolle=rolle,
            erstellt_von=request.user,
        )
        send_invite_email(einladung)
        return Response({"detail": "Invite sent."}, status=status.HTTP_201_CREATED)
 
 
class RegisterView(APIView):
    """Registers a new account using a valid invite token. Account is active immediately."""
 
    permission_classes = [AllowAny]
 
    def post(self, request):
        """Validates the invite/token and creates the member account."""
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(
            {"user": {"id": user.id, "email": user.email}},
            status=status.HTTP_201_CREATED,
        )
 
 
class LoginView(TokenObtainPairView):
    """Handles member login via email and sets JWT tokens as httpOnly cookies."""
 
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer
 
    def post(self, request, *args, **kwargs):
        """Authenticates the member and sets access/refresh tokens as cookies."""
        response = super().post(request, *args, **kwargs)
        if response.status_code != 200:
            return response
        user = User.objects.get(email=request.data.get("email"))
        set_auth_cookies(response, response.data.get("access"), response.data.get("refresh"))
        response.data = build_user_response(user)
        return response
 
 
class LogoutView(APIView):
    """Handles member logout and invalidates the refresh token."""
 
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        """Blacklists the refresh token and deletes both auth cookies."""
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Refresh token not found!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"detail": "Token is invalid or already blacklisted!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        delete_auth_cookies(response)
        return response
 
 
class PasswordResetView(APIView):
    """Handles password reset requests."""
 
    permission_classes = [AllowAny]
 
    def post(self, request):
        """Sends a password reset email if the address belongs to a member (no existence leak)."""
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            uid, token = generate_uid_and_token(user)
            send_password_reset_email(user, uid, token)
        except User.DoesNotExist:
            pass
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )
 
 
class PasswordConfirmView(APIView):
    """Handles password reset confirmation."""
 
    permission_classes = [AllowAny]
 
    def post(self, request, uidb64, token):
        """Validates the reset token and sets the new password."""
        user = get_user_from_uid(uidb64)
        if user is None or not is_valid_activation_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PasswordConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            {"detail": "Your password has been successfully reset."},
            status=status.HTTP_200_OK,
        )
 
 
class CookieTokenRefreshView(TokenRefreshView):
    """Issues a new access token using the refresh token stored in cookies."""
 
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Refresh token not found!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"detail": "Refresh token invalid!"}, status=status.HTTP_401_UNAUTHORIZED)
        access_token = serializer.validated_data.get("access")
        response = Response({"detail": "Token refreshed"}, status=status.HTTP_200_OK)
        set_auth_cookies(response, access_token, serializer.validated_data.get("refresh"))
        return response
 
 
class MeView(APIView):
    """Returns or updates the currently authenticated member's own profile."""
 
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        """Returns the logged-in member's profile, including roles."""
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
 
    def patch(self, request):
        """Lets a member update their own contact data (not their roles)."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
 
 
class ChangeCredentialsView(APIView):
    """Lets a logged-in member change their own email and/or password.
 
    Password changes apply immediately. Email changes instead trigger a
    confirmation email to the NEW address (see EmailChangeConfirmView) plus
    a heads-up notice to the OLD address - the actual email only changes
    once the confirmation link is clicked.
    """
 
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        serializer = ChangeCredentialsSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        old_email = request.user.email
        user = serializer.save()
 
        if serializer.pending_email_change:
            send_email_change_confirm_email(serializer.pending_email_change)
            send_email_change_notice_email(user, serializer.pending_email_change.neue_email)
            return Response(
                {
                    "detail": (
                        f"Bestätigungslink an {serializer.pending_email_change.neue_email} "
                        f"verschickt. Die E-Mail-Adresse ändert sich erst nach Bestätigung - "
                        f"bis dahin bleibt {old_email} gültig."
                    )
                },
                status=status.HTTP_200_OK,
            )
 
        return Response({"detail": "Änderungen gespeichert."}, status=status.HTTP_200_OK)
 
 
class EmailChangeConfirmView(APIView):
    """Confirms a pending email change via the link sent to the new address.
    This is the only point where the user's actual email is updated."""
 
    permission_classes = [AllowAny]
 
    def get(self, request, token):
        try:
            aenderung = EmailAenderung.objects.get(token=token)
        except EmailAenderung.DoesNotExist:
            return Response({"detail": "Invalid or expired confirmation link."}, status=status.HTTP_400_BAD_REQUEST)
 
        if not aenderung.is_valid():
            aenderung.delete()
            return Response({"detail": "Invalid or expired confirmation link."}, status=status.HTTP_400_BAD_REQUEST)
 
        user = aenderung.user
        user.email = aenderung.neue_email
        user.username = aenderung.neue_email
        user.save()
 
        # Clean up: this request is consumed, and any other still-pending
        # requests for this user are now moot.
        EmailAenderung.objects.filter(user=user).delete()
 
        return Response(
            {"detail": "E-Mail-Adresse erfolgreich bestätigt und geändert."},
            status=status.HTTP_200_OK,
        )
 
 
class RolleListView(generics.ListAPIView):
    """Lists all existing roles with their IDs and names - needed so the
    frontend can turn a role ID (which is all the mitglieder-endpoint
    returns) back into a human-readable name, and so the Verwaltung UI can
    offer real checkboxes for role assignment instead of raw numbers."""
 
    queryset = Rolle.objects.all().order_by('name')
    serializer_class = RolleSerializer
    permission_classes = [IsVorstand]
 
 
class MitgliederViewSet(viewsets.ModelViewSet):
    """Admin/Vorstand-facing management of member accounts.
 
    - list/retrieve: Vorstand and Admin (read-only for Vorstand, enforced
      by only exposing PATCH/DELETE to Admin below)
    - update/partial_update/destroy: Admin only
    - destroy: soft-deactivates unless performed by the platform owner
      (is_superuser), who hard-deletes instead
    - reaktivieren: owner-only, restores a deactivated account
    """
 
    queryset = User.objects.all().order_by('last_name', 'first_name')
    serializer_class = MitgliederManageSerializer
 
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsVorstand()]
        if self.action == 'reaktivieren':
            return [IsSuperUser()]
        return [IsAdminRolle()]
 
    def destroy(self, request, *args, **kwargs):
        """Hard-deletes if the owner performs it, otherwise deactivates the account."""
        instance = self.get_object()
        if request.user.is_superuser:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        instance.is_active = False
        instance.save()
        return Response({"detail": "Mitglied wurde deaktiviert."}, status=status.HTTP_200_OK)
 
    @action(detail=True, methods=['post'])
    def reaktivieren(self, request, pk=None):
        """Reactivates a previously deactivated member account. Owner only."""
        instance = self.get_object()
        instance.is_active = True
        instance.save()
        return Response({"detail": "Mitglied wurde reaktiviert."}, status=status.HTTP_200_OK)
 
 
 
 
 
 
 
 