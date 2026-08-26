"""Admin configuration for the termine app."""
 
from django.contrib import admin
 
from .models import Termin
 
 
@admin.register(Termin)
class TerminAdmin(admin.ModelAdmin):
    """Admin configuration for club events."""
 
    list_display = ['titel', 'typ', 'start', 'ort', 'ist_wiederkehrend', 'erstellt_von']
    list_filter = ['typ', 'ist_wiederkehrend']
    search_fields = ['titel', 'ort', 'beschreibung']
    date_hierarchy = 'start'
    readonly_fields = ['erstellt_von', 'erstellt_am']
 
    def save_model(self, request, obj, form, change):
        """Sets erstellt_von automatically to the current user when created via the admin."""
        if not change:
            obj.erstellt_von = request.user
        super().save_model(request, obj, form, change)
 