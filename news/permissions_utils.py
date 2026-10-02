"""
Creates (idempotently) the three role Groups and assigns them the
correct model-level permissions on Article and Newsletter:

- Reader:     view only
- Editor:     view, change, delete
- Journalist: add, view, change, delete
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import Article, Newsletter, Role

ROLE_PERMISSION_CODENAMES = {
    Role.READER: ['view'],
    Role.EDITOR: ['view', 'change', 'delete'],
    Role.JOURNALIST: ['add', 'view', 'change', 'delete'],
}

ROLE_GROUP_NAMES = {
    Role.READER: 'Reader',
    Role.EDITOR: 'Editor',
    Role.JOURNALIST: 'Journalist',
}


def get_or_create_role_groups():
    """Return {role_value: Group}, creating groups/permissions as needed."""
    groups = {}
    for model in (Article, Newsletter):
        content_type = ContentType.objects.get_for_model(model)
        model_name = model._meta.model_name
        for role, group_name in ROLE_GROUP_NAMES.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            groups[role] = group
            for action in ROLE_PERMISSION_CODENAMES[role]:
                codename = f'{action}_{model_name}'
                try:
                    permission = Permission.objects.get(
                        codename=codename, content_type=content_type
                    )
                except Permission.DoesNotExist:
                    continue
                group.permissions.add(permission)
    return groups
