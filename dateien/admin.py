from django.contrib import admin
 
from .models import Datei
 
 
@admin.register(Datei)
class DateiAdmin(admin.ModelAdmin):
    list_display = ['dateiname', 'besitzer', 'groesse', 'content_type', 'hochgeladen_am']
    list_filter = ['content_type']
    search_fields = ['dateiname', 'besitzer__email']
 

