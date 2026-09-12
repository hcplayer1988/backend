"""Serializers for the dateien API: private per-member file storage."""
 
import os
 
from django.db.models import Sum
from rest_framework import serializers
 
from ..models import Datei
 
MAX_DATEI_GROESSE_MB = 10
MAX_SPEICHER_PRO_MITGLIED_MB = 50
 
MAX_DATEI_GROESSE_BYTES = MAX_DATEI_GROESSE_MB * 1024 * 1024
MAX_SPEICHER_PRO_MITGLIED_BYTES = MAX_SPEICHER_PRO_MITGLIED_MB * 1024 * 1024
 
# Validiert wird ueber die Dateiendung, nicht ueber den vom Browser gemeldeten
# Content-Type - der ist gerade bei Office-Dateien (.odt/.ods) je nach Browser
# unzuverlaessig oder generisch (z.B. "application/octet-stream"). Fuer eine
# haertere serverseitige Pruefung des tatsaechlichen Dateiinhalts waere
# zusaetzlich eine Bibliothek wie python-magic noetig - fuer den Start reicht
# die Endungspruefung.
ALLOWED_EXTENSIONS = {
    '.pdf',
    '.jpg', '.jpeg', '.png', '.webp',
    '.doc', '.docx', '.odt', '.txt',
    '.xls', '.xlsx', '.ods',
}
 
 
class DateiSerializer(serializers.ModelSerializer):
    """Serializer for a member's own uploaded file. 'datei' is write-only
    (the raw upload) - reading back returns 'url' instead, so the frontend
    never needs to reconstruct the storage path itself."""
 
    datei = serializers.FileField(write_only=True)
    url = serializers.SerializerMethodField()
    # NEU: nach aussen wird die Groesse in MB ausgegeben statt in Bytes -
    # das Model-Feld 'groesse' selbst bleibt in Bytes (fuer die exakte
    # Quota-Berechnung in validate() unten), nur die Serializer-Ausgabe rundet.
    groesse_mb = serializers.SerializerMethodField()
 
    class Meta:
        model = Datei
        fields = ['id', 'datei', 'url', 'dateiname', 'groesse_mb', 'content_type', 'hochgeladen_am']
        read_only_fields = ['id', 'dateiname', 'groesse_mb', 'content_type', 'hochgeladen_am']
 
    def get_url(self, obj):
        request = self.context.get('request')
        if not obj.datei:
            return None
        return request.build_absolute_uri(obj.datei.url) if request else obj.datei.url
 
    def get_groesse_mb(self, obj):
        return round(obj.groesse / (1024 * 1024), 3)
 
    def validate_datei(self, value):
        """Rejects files with a disallowed extension or that are too large."""
        extension = os.path.splitext(value.name)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                'Dieser Dateityp ist nicht erlaubt. Erlaubt sind PDF, Bilder '
                '(JPEG/PNG/WebP) sowie Text- und Tabellendateien (Word, OpenDocument, TXT, Excel).'
            )
        if value.size > MAX_DATEI_GROESSE_BYTES:
            raise serializers.ValidationError(
                f'Die Datei darf maximal {MAX_DATEI_GROESSE_MB}MB groß sein.'
            )
        return value
 
    def validate(self, attrs):
        """Rejects the upload if it would push the member over their 50MB
        total quota. Runs after validate_datei, so 'datei' here is already
        confirmed to be an allowed type within the per-file size limit."""
        user = self.context['request'].user
        neue_groesse = attrs['datei'].size
        bereits_belegt = Datei.objects.filter(besitzer=user).aggregate(
            summe=Sum('groesse')
        )['summe'] or 0
 
        if bereits_belegt + neue_groesse > MAX_SPEICHER_PRO_MITGLIED_BYTES:
            frei_mb = max(MAX_SPEICHER_PRO_MITGLIED_BYTES - bereits_belegt, 0) / (1024 * 1024)
            raise serializers.ValidationError(
                f'Nicht genug Speicherplatz. Noch verfügbar: {frei_mb:.1f}MB.'
            )
        return attrs
 
    def create(self, validated_data):
        upload = validated_data.pop('datei')
        return Datei.objects.create(
            besitzer=self.context['request'].user,
            datei=upload,
            dateiname=upload.name,
            groesse=upload.size,
            content_type=getattr(upload, 'content_type', '') or '',
        )
 



