"""Serializers for the accounts API (invites, registration, login, profile)."""
 
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
 
from ..models import Einladung, Rolle
 
User = get_user_model()
 
 
class RolleSerializer(serializers.ModelSerializer):
    """Serializer for a single role."""
 
    class Meta:
        model = Rolle
        fields = ['id', 'name']
 
 
class UserSerializer(serializers.ModelSerializer):
    """Serializer for a member's profile data, including roles."""
 
    rollen = RolleSerializer(many=True, read_only=True)
    full_name = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
 
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'strasse', 'hausnummer', 'plz', 'ort', 'geburtstag',
            'full_name', 'full_address', 'rollen',
        ]
        read_only_fields = ['id', 'email', 'username', 'rollen']
 
 
class InviteCreateSerializer(serializers.Serializer):
    """Serializer for a board member/admin inviting a new member by email."""
 
    email = serializers.EmailField()
    rolle = serializers.ChoiceField(choices=Rolle.ROLLEN_CHOICES, required=False, default=Rolle.MITGLIED)
 
    def validate_email(self, value):
        """Rejects invites for emails that already belong to a registered member."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value
 
 
class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for registering an account via a valid invite token.
 
    The invite (Einladung) proves the person was authorized to join, so the
    account becomes active immediately - no separate email verification step.
    """
 
    confirmed_password = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
 
    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirmed_password', 'token',
            'first_name', 'last_name',
            'strasse', 'hausnummer', 'plz', 'ort', 'geburtstag',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'strasse': {'required': False},
            'hausnummer': {'required': False},
            'plz': {'required': False},
            'ort': {'required': False},
            'geburtstag': {'required': False},
        }
 
    def validate(self, attrs):
        """Checks password confirmation and resolves the invite for this email/token."""
        if attrs.get('password') != attrs.get('confirmed_password'):
            raise serializers.ValidationError('Passwords do not match.')
        try:
            einladung = Einladung.objects.get(token=attrs['token'], email=attrs['email'])
        except Einladung.DoesNotExist:
            raise serializers.ValidationError('Invalid invite token for this email.')
        if not einladung.is_valid():
            raise serializers.ValidationError('This invite is expired or already used.')
        attrs['_einladung'] = einladung
        return attrs
 
    def validate_email(self, value):
        """Rejects registration for an email that already has an account."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value
 
    def save(self):
        """Creates the active user, assigns the invite's role, and marks the invite used."""
        validated = self.validated_data
        einladung = validated.pop('_einladung')
 
        account = User(
            email=validated['email'],
            username=validated['email'],
            first_name=validated.get('first_name', ''),
            last_name=validated.get('last_name', ''),
            strasse=validated.get('strasse', ''),
            hausnummer=validated.get('hausnummer', ''),
            plz=validated.get('plz', ''),
            ort=validated.get('ort', ''),
            geburtstag=validated.get('geburtstag'),
            is_active=True,
        )
        account.set_password(validated['password'])
        account.save()
 
        rolle = einladung.rolle or Rolle.objects.get_or_create(name=Rolle.MITGLIED)[0]
        account.rollen.add(rolle)
 
        einladung.verwendet = True
        einladung.save()
        return account
 
 
class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that authenticates via email instead of username."""
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        self.fields['email'] = serializers.EmailField()
 
    def validate(self, attrs):
        email = attrs.get('email')
        try:
            user = User.objects.get(email=email)
            attrs['username'] = user.username
        except User.DoesNotExist:
            raise serializers.ValidationError('Wrong user or password!')
        try:
            return super().validate(attrs)
        except Exception:
            raise serializers.ValidationError('Wrong user or password!')
 
 
class PasswordConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset."""
 
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
 
    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError('Passwords do not match.')
        return attrs
 
 
class MitgliederManageSerializer(serializers.ModelSerializer):
    """Serializer for admins/Vorstand managing member accounts.
 
    Unlike UserSerializer (used for /me/), 'rollen' is writable here since
    only Admin-restricted views ever use this serializer for updates.
    """
 
    rollen = serializers.PrimaryKeyRelatedField(many=True, queryset=Rolle.objects.all(), required=False)
    full_name = serializers.ReadOnlyField()
 
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'strasse', 'hausnummer', 'plz', 'ort', 'geburtstag',
            'full_name', 'rollen', 'is_active',
        ]
        read_only_fields = ['id', 'email', 'username', 'is_active']
 
 
class ChangeCredentialsSerializer(serializers.Serializer):
    """Serializer for a logged-in user changing their own email and/or
    password. Requires the current password as a confirmation gate for
    either change - deliberately separate from UserSerializer (used for
    /me/), where email stays read-only and there's no password handling.
    """
 
    current_password = serializers.CharField(write_only=True)
    new_email = serializers.EmailField(required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    confirm_new_password = serializers.CharField(write_only=True, required=False)
 
    def validate_current_password(self, value):
        """Confirms the request comes from someone who actually knows the
        current password, not just someone with an active session."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Aktuelles Passwort ist falsch.')
        return value
 
    def validate_new_email(self, value):
        """Rejects an email already used by a different account."""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Diese E-Mail-Adresse wird bereits verwendet.')
        return value
 
    def validate_new_password(self, value):
        """Runs the new password through Django's configured password
        validators (AUTH_PASSWORD_VALIDATORS in settings.py) - same rules
        that already apply everywhere else, e.g. during registration."""
        validate_password(value)
        return value
 
    def validate(self, attrs):
        """Requires at least one actual change, and that password confirmation matches."""
        if not attrs.get('new_email') and not attrs.get('new_password'):
            raise serializers.ValidationError(
                'Gib eine neue E-Mail-Adresse oder ein neues Passwort an.'
            )
        if attrs.get('new_password') and attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError('Die neuen Passwörter stimmen nicht überein.')
        return attrs
 
    def save(self):
        """Applies whichever change(s) were provided. Username is kept in
        sync with email, matching the email=username convention used
        throughout accounts (see RegistrationSerializer)."""
        user = self.context['request'].user
        new_email = self.validated_data.get('new_email')
        new_password = self.validated_data.get('new_password')
 
        if new_email:
            user.email = new_email
            user.username = new_email
        if new_password:
            user.set_password(new_password)
 
        user.save()
        return user
 
 
 