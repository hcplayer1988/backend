"""Serializers for the forum API."""
 
from rest_framework import serializers
 
from ..models import Beitrag, Kommentar, KommentarBewertung
 
 
class KommentarSerializer(serializers.ModelSerializer):
    """Serializer for a single comment, including reply target and like/dislike counts."""
 
    autor = serializers.StringRelatedField(read_only=True)
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    meine_bewertung = serializers.SerializerMethodField()
 
    class Meta:
        model = Kommentar
        fields = [
            'id', 'beitrag', 'antwort_auf', 'autor', 'text',
            'erstellt_am', 'likes', 'dislikes', 'meine_bewertung',
        ]
        read_only_fields = ['id', 'autor', 'erstellt_am']
 
    def get_likes(self, obj):
        """Number of likes on this comment."""
        return obj.like_count()
 
    def get_dislikes(self, obj):
        """Number of dislikes on this comment."""
        return obj.dislike_count()
 
    def get_meine_bewertung(self, obj):
        """The current user's own reaction on this comment ('like', 'dislike' or None)."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        bewertung = obj.bewertungen.filter(user=request.user).first()
        return bewertung.typ if bewertung else None
 
    def validate_antwort_auf(self, value):
        """Ensures a reply targets a comment on the same post it's being created under."""
        if value is None:
            return value
        beitrag_id = self.initial_data.get('beitrag')
        if beitrag_id and str(value.beitrag_id) != str(beitrag_id):
            raise serializers.ValidationError('Der referenzierte Kommentar gehört zu einem anderen Beitrag.')
        return value
 
 
class BeitragSerializer(serializers.ModelSerializer):
    """Serializer for a forum post, including a comment count for list views."""
 
    autor = serializers.StringRelatedField(read_only=True)
    anzahl_kommentare = serializers.IntegerField(source='kommentare.count', read_only=True)
 
    class Meta:
        model = Beitrag
        fields = [
            'id', 'titel', 'text', 'kategorie', 'autor',
            'erstellt_am', 'aktualisiert_am', 'anzahl_kommentare',
        ]
        read_only_fields = ['id', 'autor', 'erstellt_am', 'aktualisiert_am', 'anzahl_kommentare']
 
 
 