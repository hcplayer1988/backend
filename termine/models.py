"""Models for the termine app: club events, trainings and their recurrence."""
 
from django.conf import settings
from django.db import models
 
 
class Termin(models.Model):
    """A single club event - match schedule entry, meeting, tournament or training.
 
    Recurring events (typically trainings) store their own recurrence rule
    (unit + interval) rather than generating individual future rows, so the
    rule stays editable in one place.
    """
 
    SPIELPLAN = 'spielplan'
    MITGLIEDERVERSAMMLUNG = 'mitgliederversammlung'
    TURNIER = 'turnier'
    TRAINING = 'training'
    SONSTIGES = 'sonstiges'
 
    TYP_CHOICES = [
        (SPIELPLAN, 'Spielplan'),
        (MITGLIEDERVERSAMMLUNG, 'Mitgliederversammlung'),
        (TURNIER, 'Turnier'),
        (TRAINING, 'Training'),
        (SONSTIGES, 'Sonstiges'),
    ]
 
    TAGE = 'tage'
    WOCHEN = 'wochen'
    MONATE = 'monate'
 
    WIEDERHOLUNG_EINHEIT_CHOICES = [
        (TAGE, 'Tage'),
        (WOCHEN, 'Wochen'),
        (MONATE, 'Monate'),
    ]
 
    titel = models.CharField(max_length=200)
    beschreibung = models.TextField(blank=True)
    typ = models.CharField(max_length=30, choices=TYP_CHOICES, default=SONSTIGES)
    ort = models.CharField(max_length=200, blank=True)
 
    start = models.DateTimeField()
    ende = models.DateTimeField(null=True, blank=True)
 
    ist_wiederkehrend = models.BooleanField(default=False)
    wiederholung_einheit = models.CharField(
        max_length=10, choices=WIEDERHOLUNG_EINHEIT_CHOICES, blank=True
    )
    wiederholung_abstand = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Zahl in Kombination mit der Einheit, z.B. Abstand=2 + Einheit=Wochen = alle 2 Wochen.'
    )
    wiederholung_bis = models.DateField(
        null=True, blank=True, help_text='Optional: Datum, ab dem die Wiederholung endet.'
    )
 
    erstellt_von = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='erstellte_termine'
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Termin'
        verbose_name_plural = 'Termine'
        ordering = ['start']
 
    def recurrence_label(self):
        """Returns a short human-readable description of the recurrence rule, if any."""
        if not self.ist_wiederkehrend or not self.wiederholung_abstand or not self.wiederholung_einheit:
            return ''
        einheit_label = dict(self.WIEDERHOLUNG_EINHEIT_CHOICES).get(self.wiederholung_einheit, '')
        return f"alle {self.wiederholung_abstand} {einheit_label}"
 
    def __str__(self):
        return f"{self.titel} ({self.start:%d.%m.%Y %H:%M})"
 