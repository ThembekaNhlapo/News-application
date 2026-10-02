"""Custom DRF permission classes enforcing role-based access to the API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Role


class IsJournalist(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.JOURNALIST)


class IsEditor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.EDITOR)


class IsReader(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.READER)


class ArticlePermission(BasePermission):
    """
    - Readers: read-only (SAFE_METHODS).
    - Journalists: read + create; may update/delete only their own articles.
    - Editors: read, update, delete any article (approval included);
      editors do not create articles.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method == 'POST':
            return user.role == Role.JOURNALIST

        # PUT / PATCH / DELETE
        return user.role in (Role.JOURNALIST, Role.EDITOR)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS:
            if obj.approved:
                return True
            # Unapproved articles are only visible to their author or an editor.
            return user.role == Role.EDITOR or (
                user.role == Role.JOURNALIST and obj.author_id == user.id
            )
        if user.role == Role.EDITOR:
            return True
        if user.role == Role.JOURNALIST:
            return obj.author_id == user.id
        return False


class IsEditorForApproval(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.EDITOR)
