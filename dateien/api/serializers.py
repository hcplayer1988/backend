from django.db.models import Sum
from rest_framework import serializers
 
from ..models import Datei, Ordner
 
MAX_DATEI_GROESSE_MB = 10
MAX_SPEICHER_PRO_MITGLIED_MB = 50
MAX_DATEI_GROESSE_BYTES = MAX_DATEI_GROESSE_MB * 1024 * 1024
MAX_SPEICHER_PRO_MITGLIED_BYTES = MAX_SPEICHER_PRO_MITGLIED_MB * 1024 * 1024
 
ALLOWED_EXTENSIONS = {
    '.pdf',
    '.jpg', '.jpeg', '.png', '.webp',
    '.doc', '.docx', '.odt', '.txt',
    '.xls', '.xlsx', '.ods',
}
 
 
class OrdnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordner
        fields = ['id', 'name', 'parent', 'erstellt_am']
        read_only_fields = ['id', 'erstellt_am']
 
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Der Ordnername darf nicht leer sein.')
        return value
 
    def validate_parent(self, value):
        if value is None:
            return value
        request = self.context['request']
        if value.besitzer_id != request.user.id:
            raise serializers.ValidationError('Dieser Ordner gehört dir nicht.')
        # Zirkelbezug verhindern: ein Ordner darf beim Umbenennen/Verschieben
        # nicht in sich selbst oder einen seiner eigenen Unterordner gehängt
        # werden - sonst entsteht eine Endlosschleife in der Baumstruktur.
        if self.instance is not None:
            current = value
            while current is not None:
                if current.pk == self.instance.pk:
                    raise serializers.ValidationError(
                        'Ein Ordner kann nicht in sich selbst oder einen eigenen Unterordner verschoben werden.'
                    )
                current = current.parent
        return value
 
    def validate(self, attrs):
        request = self.context['request']
        name = attrs.get('name', getattr(self.instance, 'name', None))
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        queryset = Ordner.objects.filter(besitzer=request.user, parent=parent, name__iexact=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {'name': 'In diesem Ordner gibt es bereits einen Ordner mit diesem Namen.'}
            )
        return attrs
 
    def create(self, validated_data):
        validated_data['besitzer'] = self.context['request'].user
        return super().create(validated_data)
 
 
class DateiSerializer(serializers.ModelSerializer):
    datei = serializers.FileField(write_only=True)
    url = serializers.SerializerMethodField()
    groesse_mb = serializers.SerializerMethodField()
 
    class Meta:
        model = Datei
        fields = ['id', 'datei', 'url', 'ordner', 'dateiname', 'groesse_mb', 'content_type', 'hochgeladen_am']
        read_only_fields = ['id', 'dateiname', 'content_type', 'hochgeladen_am']
 
    def get_url(self, obj):
        request = self.context.get('request')
        if not obj.datei:
            return None
        return request.build_absolute_uri(obj.datei.url) if request else obj.datei.url
 
    def get_groesse_mb(self, obj):
        return round(obj.groesse / (1024 * 1024), 3)
 
    def validate_datei(self, value):
        extension = '.' + value.name.rsplit('.', 1)[-1].lower() if '.' in value.name else ''
        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                'Dieser Dateityp ist nicht erlaubt. Erlaubt sind PDF, Bilder (JPEG/PNG/WebP) sowie '
                'gängige Office-Dateien (Word, OpenDocument, TXT, Excel).'
            )
        if value.size > MAX_DATEI_GROESSE_BYTES:
            raise serializers.ValidationError(f'Die Datei darf maximal {MAX_DATEI_GROESSE_MB}MB groß sein.')
        return value
 
    def validate_ordner(self, value):
        if value is None:
            return value
        request = self.context['request']
        if value.besitzer_id != request.user.id:
            raise serializers.ValidationError('Dieser Ordner gehört dir nicht.')
        return value
 
    def validate(self, attrs):
        # Die Speicher-Quota wird nur beim Hochladen einer neuen Datei
        # geprüft (dann steckt 'datei' in attrs) - beim reinen Verschieben
        # über die verschieben()-Action läuft dieser Serializer gar nicht
        # erst mit, daher ist hier keine Sonderbehandlung nötig.
        if 'datei' in attrs:
            request = self.context['request']
            genutzt = Datei.objects.filter(besitzer=request.user).aggregate(summe=Sum('groesse'))['summe'] or 0
            if genutzt + attrs['datei'].size > MAX_SPEICHER_PRO_MITGLIED_BYTES:
                raise serializers.ValidationError(
                    f'Dein Speicherplatz reicht nicht aus (max. {MAX_SPEICHER_PRO_MITGLIED_MB}MB pro Mitglied).'
                )
        return attrs
 
    def create(self, validated_data):
        upload = validated_data.pop('datei')
        validated_data['besitzer'] = self.context['request'].user
        validated_data['dateiname'] = upload.name
        validated_data['groesse'] = upload.size
        validated_data['content_type'] = upload.content_type or ''
        validated_data['datei'] = upload
        return super().create(validated_data)
 



