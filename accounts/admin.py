"""Admin configuration for the accounts app."""
 
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
 
from .models import Einladung, Rolle
 
User = get_user_model()
 
 
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for club members (custom User model)."""
 
    list_display = ['email', 'voller_name', 'is_active', 'is_superuser', 'rollen_liste', 'date_joined']
    list_filter = ['is_active', 'is_superuser', 'rollen']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    filter_horizontal = ('groups', 'user_permissions', 'rollen')
 
    fieldsets = UserAdmin.fieldsets + (
        ('Vereinsdaten', {
            'fields': ('strasse', 'hausnummer', 'plz', 'ort', 'geburtstag', 'rollen'),
        }),
    )
 
    def rollen_liste(self, obj):
        """Displays the member's roles as a comma-separated string in the list view."""
        return ", ".join(r.get_name_display() for r in obj.rollen.all())
    rollen_liste.short_description = 'Rollen'
 
 
@admin.register(Rolle)
class RolleAdmin(admin.ModelAdmin):
    """Admin configuration for roles."""
 
    list_display = ['name']
 
 
@admin.register(Einladung)
class EinladungAdmin(admin.ModelAdmin):
    """Admin configuration for invites, including the invite link for manual resending."""
 
    list_display = ['email', 'rolle', 'erstellt_von', 'erstellt_am', 'verwendet', 'gueltig']
    list_filter = ['verwendet', 'rolle']
    search_fields = ['email']
    readonly_fields = ['token', 'erstellt_von', 'erstellt_am']
 
    def gueltig(self, obj):
        """Shows at a glance in the list view whether the invite can still be used."""
        return obj.ist_gueltig()
    gueltig.boolean = True
    gueltig.short_description = 'Noch gültig'
 