import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a superuser non-interactively if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('ADMIN_USERNAME')
        email = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD')

        if not username or not email or not password:
            self.stdout.write(self.style.ERROR('ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD must be set in environment variables.'))
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}".'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists.'))
