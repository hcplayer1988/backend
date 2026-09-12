from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
 
 
def upload_pfad(instance, filename):
    return f"mitglieder_dateien/{instance.besitzer_id}/{filename}"
 
 
class Ordner(models.Model):
    """Ein Ordner im privaten Dateispeicher eines Mitglieds. Ordner können
    beliebig tief verschachtelt werden (parent = übergeordneter Ordner,
    None = Ordner liegt im Hauptverzeichnis). Wird ein Ordner gelöscht,
    werden alle enthaltenen Unterordner und Dateien automatisch mitgelöscht
    (CASCADE) - das Frontend weist vorher per Popup ausdrücklich darauf hin,
    dass das unwiderruflich ist."""
 
    besitzer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ordner'
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='unterordner'
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['name']
 
    def __str__(self):
        return self.name
 
 
class Datei(models.Model):
    besitzer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dateien'
    )
    # CASCADE (vorher SET_NULL): löscht man einen Ordner, sollen alle darin
    # enthaltenen Dateien automatisch mitgelöscht werden, nicht ins
    # Hauptverzeichnis "durchrutschen".
    ordner = models.ForeignKey(
        Ordner, on_delete=models.CASCADE, null=True, blank=True, related_name='dateien'
    )
    datei = models.FileField(upload_to=upload_pfad)
    dateiname = models.CharField(max_length=255)
    groesse = models.PositiveIntegerField(help_text='Dateigröße in Bytes')
    content_type = models.CharField(max_length=100, blank=True)
    hochgeladen_am = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.dateiname
 
 
@receiver(post_delete, sender=Datei)
def datei_von_platte_loeschen(sender, instance, **kwargs):
    """Räumt die physische Datei von der Festplatte auf. Greift sowohl beim
    direkten Löschen einer einzelnen Datei als auch beim kaskadierenden
    Löschen über einen übergeordneten Ordner (dort läuft keine View, nur
    Djangos CASCADE auf DB-Ebene - ohne dieses Signal blieben die Dateien
    dann als Datenleichen auf der Festplatte liegen)."""
    if instance.datei:
        instance.datei.delete(save=False)
 
 
 