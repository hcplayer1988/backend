from django.db.models import Sum
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
 
from ..models import Datei, Ordner
from .serializers import (
    MAX_SPEICHER_PRO_MITGLIED_BYTES,
    DateiSerializer,
    OrdnerSerializer,
)
 
 
class OrdnerViewSet(viewsets.ModelViewSet):
    serializer_class = OrdnerSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
 
    def get_queryset(self):
        qs = Ordner.objects.filter(besitzer=self.request.user)
        # ?alle=1 liefert die komplette, flache Ordnerliste des Mitglieds
        # (fürs Frontend, um Baum/Breadcrumb/Verschieben-Auswahl clientseitig
        # aufzubauen, ohne bei jeder Navigation neu nachzuladen). Ohne diesen
        # Parameter wird beim Auflisten nach dem übergeordneten Ordner
        # gefiltert (?parent=<id>, kein Parameter = Hauptverzeichnis).
        if self.action == 'list' and self.request.query_params.get('alle') != '1':
            parent_param = self.request.query_params.get('parent')
            if parent_param in (None, ''):
                qs = qs.filter(parent__isnull=True)
            else:
                qs = qs.filter(parent_id=parent_param)
        return qs
 
    # Kein perform_destroy-Override mehr: das Löschen eines Ordners
    # kaskadiert jetzt bewusst auf Unterordner und Dateien (siehe
    # models.py, Datei.ordner = CASCADE). Das Frontend warnt vorher per
    # Popup ausdrücklich davor, dass das unwiderruflich ist.
 
 
class DateiViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = DateiSerializer
 
    def get_queryset(self):
        qs = Datei.objects.filter(besitzer=self.request.user)
        if self.action == 'list':
            ordner_param = self.request.query_params.get('ordner')
            if ordner_param in (None, ''):
                qs = qs.filter(ordner__isnull=True)
            else:
                qs = qs.filter(ordner_id=ordner_param)
        return qs
 
    # Kein perform_destroy-Override mehr nötig: die physische Datei wird
    # jetzt per post_delete-Signal (models.py) von der Festplatte entfernt -
    # das greift dann automatisch auch beim kaskadierenden Löschen über
    # einen Ordner, wo gar keine View im Spiel ist.
 
    @action(detail=False, methods=['get'])
    def speicher(self, request):
        # Bewusst nicht über get_queryset() (die filtert bei action='list'
        # nach Ordner) - hier zählt immer die Gesamtsumme über alle Ordner.
        genutzt_bytes = Datei.objects.filter(besitzer=request.user).aggregate(
            summe=Sum('groesse')
        )['summe'] or 0
        frei_bytes = max(MAX_SPEICHER_PRO_MITGLIED_BYTES - genutzt_bytes, 0)
        return Response({
            'genutzt_mb': round(genutzt_bytes / (1024 * 1024), 3),
            'quota_mb': round(MAX_SPEICHER_PRO_MITGLIED_BYTES / (1024 * 1024), 3),
            'frei_mb': round(frei_bytes / (1024 * 1024), 3),
        }, status=status.HTTP_200_OK)
 
    @action(detail=True, methods=['post'], url_path='verschieben')
    def verschieben(self, request, pk=None):
        datei = self.get_object()
        ordner_id = request.data.get('ordner')
        if ordner_id in (None, ''):
            datei.ordner = None
        else:
            try:
                ordner = Ordner.objects.get(pk=ordner_id, besitzer=request.user)
            except Ordner.DoesNotExist:
                return Response({'ordner': 'Ordner nicht gefunden.'}, status=status.HTTP_400_BAD_REQUEST)
            datei.ordner = ordner
        datei.save(update_fields=['ordner'])
        return Response(DateiSerializer(datei, context={'request': request}).data)
 

