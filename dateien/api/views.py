"""Views for the dateien API: private per-member file storage."""
 
from django.db.models import Sum
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
 
from ..models import Datei
from .serializers import MAX_SPEICHER_PRO_MITGLIED_BYTES, DateiSerializer
 
 
class DateiViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Private per-member file storage.
 
    - list/create/destroy: only the member's own files - get_queryset()
      filters to the logged-in user, so another member's files are neither
      listed nor reachable by id (a mismatched id just 404s, same as if it
      didn't exist)
    - speicher: returns how much of the 50MB quota is used/free, for the
      frontend's storage indicator
    """
 
    serializer_class = DateiSerializer
    permission_classes = [IsAuthenticated]
 
    def get_queryset(self):
        return Datei.objects.filter(besitzer=self.request.user)
 
    def perform_destroy(self, instance):
        """Deletes the file from disk too, not just the database row -
        otherwise uploads would just pile up unused in the media folder."""
        instance.datei.delete(save=False)
        instance.delete()
 
    @action(detail=False, methods=['get'])
    def speicher(self, request):
        """Returns the logged-in member's current storage usage against
        their 50MB quota, in MB rounded to 3 decimal places (the internal
        model field 'groesse' stays in bytes for precision - this endpoint
        just converts for display)."""
        genutzt_bytes = self.get_queryset().aggregate(summe=Sum('groesse'))['summe'] or 0
        frei_bytes = max(MAX_SPEICHER_PRO_MITGLIED_BYTES - genutzt_bytes, 0)
        return Response(
            {
                'genutzt_mb': round(genutzt_bytes / (1024 * 1024), 3),
                'quota_mb': round(MAX_SPEICHER_PRO_MITGLIED_BYTES / (1024 * 1024), 3),
                'frei_mb': round(frei_bytes / (1024 * 1024), 3),
            },
            status=status.HTTP_200_OK,
        )
 

