"""Views for the forum API."""
 
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
 
from .permissions import IsAuthorOrModerator
from .serializers import BeitragSerializer, KommentarSerializer
from ..models import Beitrag, Kommentar, KommentarBewertung
 
 
class BeitragViewSet(viewsets.ModelViewSet):
    """Forum posts: any authenticated member can read/create; editing or
    deleting is restricted to the author or a moderator (see permissions)."""
 
    queryset = Beitrag.objects.all()
    serializer_class = BeitragSerializer
    permission_classes = [IsAuthorOrModerator]
 
    def perform_create(self, serializer):
        """Sets the author automatically to the currently logged-in user."""
        serializer.save(autor=self.request.user)
 
 
class KommentarViewSet(viewsets.ModelViewSet):
    """Forum comments. Supports filtering by post via ?beitrag=<id>, replying
    to another comment via antwort_auf, and liking/disliking via /bewerten/."""
 
    serializer_class = KommentarSerializer
    permission_classes = [IsAuthorOrModerator]
 
    def get_queryset(self):
        """Optionally filters comments down to a single post."""
        queryset = Kommentar.objects.all()
        beitrag_id = self.request.query_params.get('beitrag')
        if beitrag_id:
            queryset = queryset.filter(beitrag_id=beitrag_id)
        return queryset
 
    def get_serializer_context(self):
        """Passes the request through so the serializer can resolve 'meine_bewertung'."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
 
    def perform_create(self, serializer):
        """Sets the author automatically to the currently logged-in user."""
        serializer.save(autor=self.request.user)
 
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bewerten(self, request, pk=None):
        """Likes or dislikes a comment.
 
        Voting the same type again removes the reaction (toggle off).
        Voting the opposite type replaces the existing one.
        Body: {"typ": "like"} or {"typ": "dislike"}.
        """
        kommentar = self.get_object()
        typ = request.data.get('typ')
        if typ not in dict(KommentarBewertung.BEWERTUNG_CHOICES):
            return Response(
                {"detail": "typ muss 'like' oder 'dislike' sein."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        bestehende = KommentarBewertung.objects.filter(kommentar=kommentar, user=request.user).first()
        if bestehende and bestehende.typ == typ:
            bestehende.delete()
            meine_bewertung = None
        elif bestehende:
            bestehende.typ = typ
            bestehende.save()
            meine_bewertung = typ
        else:
            KommentarBewertung.objects.create(kommentar=kommentar, user=request.user, typ=typ)
            meine_bewertung = typ
 
        return Response(
            {
                "likes": kommentar.like_count(),
                "dislikes": kommentar.dislike_count(),
                "meine_bewertung": meine_bewertung,
            },
            status=status.HTTP_200_OK,
        )
 
 
 