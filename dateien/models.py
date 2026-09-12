"""Models for the dateien app: private per-member file storage."""
 
from django.conf import settings
from django.db import models
 
 
def upload_pfad(instance, filename):
    """Stores each member's uploads under their own subfolder, so filenames
    from different members never collide and everything stays easy to
    find/clean up per member."""
    return f"mitglieder_dateien/{instance.besitzer_id}/{filename}"
 
 
class Datei(models.Model):
    """A file a member uploaded to their own private storage (e.g. a PDF
    protocol from a meeting). Counts against that member's 50MB quota (see
    MAX_SPEICHER_PRO_MITGLIED_BYTES in api/serializers.py) - the avatar is
    intentionally separate and does NOT count against this quota.
 
    Strictly private for now: a member only ever sees their own files here.
    Sharing is a separate, later feature (planned: sending as an attachment
    in the not-yet-built live chat).
    """
 
    besitzer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dateien'
    )
    datei = models.FileField(upload_to=upload_pfad)
    # Der urspruengliche Dateiname wird separat gespeichert, weil Django beim
    # Speichern bei einer Namenskollision automatisch einen Suffix anhaengt -
    # so bleibt der Name, den das Mitglied kennt, in der Anzeige trotzdem erhalten.
    dateiname = models.CharField(max_length=255)
    groesse = models.PositiveIntegerField(help_text='Dateigröße in Bytes')
    content_type = models.CharField(max_length=100, blank=True)
    hochgeladen_am = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Datei'
        verbose_name_plural = 'Dateien'
        ordering = ['-hochgeladen_am']
 
    def __str__(self):
        return f"{self.dateiname} ({self.besitzer.email})"
 