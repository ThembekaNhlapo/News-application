from django.core.management.base import BaseCommand

from news.permissions_utils import get_or_create_role_groups


class Command(BaseCommand):
    help = 'Creates the Reader, Editor, and Journalist groups with their permissions.'

    def handle(self, *args, **options):
        groups = get_or_create_role_groups()
        for role, group in groups.items():
            self.stdout.write(
                self.style.SUCCESS(f'Group "{group.name}" ready ({role}).')
            )
