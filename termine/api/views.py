"""Views for the termine API."""
 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
 
from accounts.api.permissions import IsVorstand
 
from .serializers import TerminSerializer
from ..models import Termin
 
 
class TerminViewSet(viewsets.ModelViewSet):
    """Club events: anyone can view, only Vorstand/Admin/Owner can manage.
 
    - list/retrieve: public (no authentication required)
    - create/update/partial_update/destroy: Vorstand, Admin, or the platform owner
    """
 
    queryset = Termin.objects.all()
    serializer_class = TerminSerializer
 
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsVorstand()]
 
    def perform_create(self, serializer):
        """Sets the creator automatically to the currently logged-in user."""
        serializer.save(erstellt_von=self.request.user)
 



