"""Views for the termine API."""
 
from rest_framework import viewsets
 
from accounts.api.permissions import IsVorstand
from rest_framework.permissions import IsAuthenticated
 
from .serializers import TerminSerializer
from ..models import Termin
 
 
class TerminViewSet(viewsets.ModelViewSet):
    """Club events: all logged-in members can view, only Vorstand/Admin/Owner can manage.
 
    - list/retrieve: any authenticated member
    - create/update/partial_update/destroy: Vorstand, Admin, or the platform owner
    """
 
    queryset = Termin.objects.all()
    serializer_class = TerminSerializer
 
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsVorstand()]
 
    def perform_create(self, serializer):
        """Sets the creator automatically to the currently logged-in user."""
        serializer.save(erstellt_von=self.request.user)
 