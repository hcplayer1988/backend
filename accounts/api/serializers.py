"""Serializers for the accounts API (invites, registration, login, profile)."""
 
from django.contrib.auth import get_user_model
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
    voller_name = serializers.ReadOnlyField()
    vollstaendige_adresse = serializers.ReadOnlyField()
 
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'strasse', 'hausnummer', 'plz', 'ort', 'geburtstag',
            'voller_name', 'vollstaendige_adresse', 'rollen',
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
        if not einladung.ist_gueltig():
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
 