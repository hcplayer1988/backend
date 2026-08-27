"""Admin configuration for the forum app."""
 
from django.contrib import admin
 
from .models import Beitrag, Kommentar, KommentarBewertung
 
 
class KommentarInline(admin.TabularInline):
    """Shows comments directly under their post in the admin."""
 
    model = Kommentar
    fk_name = 'beitrag'
    extra = 0
    readonly_fields = ['autor', 'erstellt_am']
 
 
@admin.register(Beitrag)
class BeitragAdmin(admin.ModelAdmin):
    """Admin configuration for forum posts."""
 
    list_display = ['titel', 'autor', 'kategorie', 'erstellt_am']
    list_filter = ['kategorie']
    search_fields = ['titel', 'text']
    readonly_fields = ['autor', 'erstellt_am', 'aktualisiert_am']
    inlines = [KommentarInline]
 
    def save_model(self, request, obj, form, change):
        """Sets autor automatically to the current user when created via the admin."""
        if not change:
            obj.autor = request.user
        super().save_model(request, obj, form, change)
 
    def save_formset(self, request, form, formset, change):
        """Sets autor automatically on new Kommentar rows added via the inline formset.
 
        save_model() above only covers the Beitrag itself - inline rows go
        through this hook instead, so without it new comments would be
        saved with autor=None and violate the NOT NULL constraint.
        """
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, Kommentar) and obj.pk is None:
                obj.autor = request.user
            obj.save()
        formset.save_m2m()
 
 
@admin.register(Kommentar)
class KommentarAdmin(admin.ModelAdmin):
    """Admin configuration for forum comments."""
 
    list_display = ['beitrag', 'antwort_auf', 'autor', 'erstellt_am', 'like_count', 'dislike_count']
    list_filter = ['beitrag']
    search_fields = ['text']
    readonly_fields = ['autor', 'erstellt_am']
 
    def save_model(self, request, obj, form, change):
        """Sets autor automatically to the current user when created via the admin."""
        if not change:
            obj.autor = request.user
        super().save_model(request, obj, form, change)
 
 
@admin.register(KommentarBewertung)
class KommentarBewertungAdmin(admin.ModelAdmin):
    """Admin configuration for comment reactions (likes/dislikes)."""
 
    list_display = ['kommentar', 'user', 'typ', 'erstellt_am']
    list_filter = ['typ']
 
 
 