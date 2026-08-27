"""Custom permissions for the forum API."""
 
from rest_framework.permissions import SAFE_METHODS, BasePermission
 
 
class IsAuthorOrModerator(BasePermission):
    """Any authenticated member can read and create.
 
    Editing or deleting a post/comment is only allowed for its own author,
    or for Vorstand/Admin/the platform owner (moderation).
    """
 
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
 
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        is_author = obj.autor_id == user.id
        is_moderator = user.is_superuser or user.has_role('vorstand') or user.has_role('admin')
        return is_author or is_moderator
 
 
 