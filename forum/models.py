"""Models for the forum app: posts, comments, replies and reactions."""
 
from django.conf import settings
from django.db import models
 
 
class Beitrag(models.Model):
    """A forum post members can discuss under."""
 
    titel = models.CharField(max_length=200)
    text = models.TextField()
    kategorie = models.CharField(max_length=100, blank=True)
 
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='beitraege'
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = 'Beitrag'
        verbose_name_plural = 'Beiträge'
        ordering = ['-erstellt_am']
 
    def __str__(self):
        return self.titel
 
 
class Kommentar(models.Model):
    """A comment on a forum post. May itself be a reply to another comment."""
 
    beitrag = models.ForeignKey(Beitrag, on_delete=models.CASCADE, related_name='kommentare')
    antwort_auf = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='antworten'
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kommentare'
    )
    text = models.TextField()
    erstellt_am = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Kommentar'
        verbose_name_plural = 'Kommentare'
        ordering = ['erstellt_am']
 
    def like_count(self):
        """Number of likes on this comment."""
        return self.bewertungen.filter(typ=KommentarBewertung.LIKE).count()
 
    def dislike_count(self):
        """Number of dislikes on this comment."""
        return self.bewertungen.filter(typ=KommentarBewertung.DISLIKE).count()
 
    def __str__(self):
        return f"Kommentar von {self.autor} zu '{self.beitrag.titel}'"
 
 
class KommentarBewertung(models.Model):
    """One member's like or dislike on a comment.
 
    A member can have at most one reaction per comment (unique_together);
    voting the opposite type replaces it, voting the same type again
    removes it (handled in the view, not here).
    """
 
    LIKE = 'like'
    DISLIKE = 'dislike'
 
    BEWERTUNG_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]
 
    kommentar = models.ForeignKey(Kommentar, on_delete=models.CASCADE, related_name='bewertungen')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kommentar_bewertungen'
    )
    typ = models.CharField(max_length=10, choices=BEWERTUNG_CHOICES)
    erstellt_am = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Kommentar-Bewertung'
        verbose_name_plural = 'Kommentar-Bewertungen'
        unique_together = ('kommentar', 'user')
 
    def __str__(self):
        return f"{self.user} -> {self.typ} auf Kommentar {self.kommentar_id}"
 
 
 