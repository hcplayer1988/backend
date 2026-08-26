"""Serializers for the termine API."""
 
from rest_framework import serializers
 
from ..models import Termin
 
 
class TerminSerializer(serializers.ModelSerializer):
    """Serializer for creating, viewing and editing club events."""
 
    erstellt_von = serializers.StringRelatedField(read_only=True)
    recurrence_label = serializers.ReadOnlyField()
 
    class Meta:
        model = Termin
        fields = [
            'id', 'titel', 'beschreibung', 'typ', 'ort', 'start', 'ende',
            'ist_wiederkehrend', 'wiederholung_einheit', 'wiederholung_abstand',
            'wiederholung_bis', 'recurrence_label', 'erstellt_von', 'erstellt_am',
        ]
        read_only_fields = ['id', 'erstellt_von', 'erstellt_am']
 
    def validate(self, attrs):
        """Requires unit and interval whenever an event is marked as recurring."""
        ist_wiederkehrend = attrs.get(
            'ist_wiederkehrend',
            getattr(self.instance, 'ist_wiederkehrend', False)
        )
        if ist_wiederkehrend:
            einheit = attrs.get('wiederholung_einheit', getattr(self.instance, 'wiederholung_einheit', ''))
            abstand = attrs.get('wiederholung_abstand', getattr(self.instance, 'wiederholung_abstand', None))
            if not einheit or not abstand:
                raise serializers.ValidationError(
                    'Bei wiederkehrenden Terminen sind wiederholung_einheit und wiederholung_abstand erforderlich.'
                )
        return attrs
 