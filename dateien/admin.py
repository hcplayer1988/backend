from django.contrib import admin
 
from .models import Datei, Ordner
 
 
@admin.register(Ordner)
class OrdnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'besitzer', 'parent', 'erstellt_am')
    list_filter = ('besitzer',)
    search_fields = ('name', 'besitzer__email', 'besitzer__username')
 
 
@admin.register(Datei)
class DateiAdmin(admin.ModelAdmin):
    list_display = ('dateiname', 'besitzer', 'ordner', 'groesse', 'content_type', 'hochgeladen_am')
    list_filter = ('besitzer',)
    search_fields = ('dateiname', 'besitzer__email', 'besitzer__username')
  

