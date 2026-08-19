"""Models for the accounts app: custom user, roles and invites."""
 
import secrets
from datetime import timedelta
 
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
 
 
class Rolle(models.Model):
    """Represents a role a user can have within the club."""
 
    ADMIN = 'admin'
    VORSTAND = 'vorstand'
    MITGLIED = 'mitglied'
 
    ROLLEN_CHOICES = [
        (ADMIN, 'Admin'),
        (VORSTAND, 'Vorstandsmitglied'),
        (MITGLIED, 'Mitglied'),
    ]
 
    name = models.CharField(max_length=50, choices=ROLLEN_CHOICES, unique=True)
 
    class Meta:
        verbose_name = 'Rolle'
        verbose_name_plural = 'Rollen'
 
    def __str__(self):
        return self.get_name_display()
 
 
class User(AbstractUser):
    """Custom user model representing a club member.
 
    Holds contact and address data in addition to Django's default auth
    fields, plus the roles that drive permissions (Vorstand, Admin, etc.).
    """
 
    email = models.EmailField(unique=True)
 
    # Adresse
    strasse = models.CharField(max_length=100, blank=True)
    hausnummer = models.CharField(max_length=10, blank=True)
    plz = models.CharField(max_length=10, blank=True)
    ort = models.CharField(max_length=100, blank=True)
 
    # Geburtstag — Basis für die spätere automatische Erinnerungs-Mail
    # an alle Mitglieder außer dem Geburtstagskind selbst.
    geburtstag = models.DateField(null=True, blank=True)
 
    rollen = models.ManyToManyField(Rolle, blank=True, related_name='users')
 
    def has_rolle(self, rolle_name):
        """Checks whether the user has the given role."""
        return self.rollen.filter(name=rolle_name).exists()
 
    @property
    def voller_name(self):
        """Returns the member's full name, falling back to the email."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email
 
    @property
    def vollstaendige_adresse(self):
        """Returns a formatted one-line address, or an empty string if incomplete."""
        if not (self.strasse and self.plz and self.ort):
            return ''
        hausnummer = f" {self.hausnummer}" if self.hausnummer else ''
        return f"{self.strasse}{hausnummer}, {self.plz} {self.ort}"
 
    def __str__(self):
        return self.email
 
 
class Einladung(models.Model):
    """An invite that allows one person to register with a specific role."""
 
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    rolle = models.ForeignKey(Rolle, on_delete=models.SET_NULL, null=True, blank=True)
    erstellt_von = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='versendete_einladungen'
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)
    verwendet = models.BooleanField(default=False)
 
    class Meta:
        verbose_name = 'Einladung'
        verbose_name_plural = 'Einladungen'
        ordering = ['-erstellt_am']
 
    def ist_gueltig(self):
        """Checks whether the invite is still usable (not used, not older than 7 days)."""
        return not self.verwendet and self.erstellt_am >= timezone.now() - timedelta(days=7)
 
    def __str__(self):
        return f"{self.email} ({'verwendet' if self.verwendet else 'offen'})"
    
