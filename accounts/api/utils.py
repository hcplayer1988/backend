"""Utility functions for the accounts API: emails, tokens, auth cookies."""
 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
 
User = get_user_model()
 
 
def generate_uid_and_token(user):
    """Generates a uidb64 and a password-reset token for the given user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token
 
 
def send_html_email(subject, template_name, context, recipient):
    """Renders an HTML template and sends it as an email with a plain-text fallback."""
    html_content = render_to_string(template_name, context)
    text_content = "Bitte öffne diese E-Mail in einem HTML-fähigen Client."
    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [recipient])
    email.attach_alternative(html_content, "text/html")
    email.send()
 
 
def send_invite_email(einladung):
    """Sends the invite email containing the registration link with token."""
    register_link = f"{settings.FRONTEND_URL}/auth/register?token={einladung.token}&email={einladung.email}"
    send_html_email(
        subject="Einladung zur VV90-Plattform",
        template_name="emails/invite_email.html",
        context={
            "register_link": register_link,
            "email": einladung.email,
            "site_url": settings.FRONTEND_URL,
        },
        recipient=einladung.email,
    )
 
 
def send_password_reset_email(user, uid, token):
    """Sends the password reset email containing the confirm link."""
    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?uid={uid}&token={token}"
    send_html_email(
        subject="Passwort zurücksetzen – VV90",
        template_name="emails/password_reset_email.html",
        context={
            "reset_link": reset_link,
            "email": user.email,
            "site_url": settings.FRONTEND_URL,
        },
        recipient=user.email,
    )
 
 
def send_email_change_confirm_email(aenderung):
    """Sends the confirmation link to the NEW address - clicking it is what
    actually applies the email change (see EmailChangeConfirmView)."""
    confirm_link = f"{settings.FRONTEND_URL}/email-bestaetigen?token={aenderung.token}"
    send_html_email(
        subject="Bestätige deine neue E-Mail-Adresse – VV90",
        template_name="emails/email_change_confirm.html",
        context={
            "confirm_link": confirm_link,
            "alte_email": aenderung.user.email,
            "neue_email": aenderung.neue_email,
            "site_url": settings.FRONTEND_URL,
        },
        recipient=aenderung.neue_email,
    )
 
 
def send_email_change_notice_email(user, neue_email):
    """Sends a heads-up notice to the OLD address - purely informational,
    no action needed, just a way to notice if this wasn't actually the
    account owner requesting the change."""
    send_html_email(
        subject="Änderung deiner E-Mail-Adresse angefordert – VV90",
        template_name="emails/email_change_notice.html",
        context={
            "neue_email": neue_email,
            "site_url": settings.FRONTEND_URL,
        },
        recipient=user.email,
    )
 
 
def get_user_from_uid(uidb64):
    """Decodes a uidb64 value and returns the matching user, or None."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
 
 
def is_valid_activation_token(user, token):
    """Checks whether a password-reset token is valid for the given user."""
    return default_token_generator.check_token(user, token)
 
 
def set_auth_cookies(response, access, refresh):
    """Sets the JWT access and refresh tokens as httpOnly cookies on the response."""
    cookie_settings = {"httponly": True, "secure": True, "samesite": "Lax"}
    response.set_cookie("access_token", access, **cookie_settings)
    if refresh:
        response.set_cookie("refresh_token", refresh, **cookie_settings)
 
 
def delete_auth_cookies(response):
    """Deletes both auth cookies from the response (used on logout)."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
 
 
def build_user_response(user, request=None):
    """Builds the user data dict returned on successful login - includes
    roles so the frontend knows the correct permissions immediately,
    without needing a follow-up /me/ call or a page reload to see them.
 
    NEU: also includes the avatar (if any), for the same reason - otherwise
    the topbar would show initials right after login until the next /me/
    call or a page reload. 'request' is optional so this still works if
    ever called without one (falls back to a relative URL in that case).
    """
    avatar_url = None
    if user.avatar:
        avatar_url = request.build_absolute_uri(user.avatar.url) if request else user.avatar.url
 
    return {
        "detail": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "avatar": avatar_url,
            "rollen": [{"id": r.id, "name": r.name} for r in user.rollen.all()],
        },
    }
  







