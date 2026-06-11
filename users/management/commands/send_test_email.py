from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from users.email_service import send_welcome_email

User = get_user_model()


class Command(BaseCommand):
    help = 'Send a test welcome email to a user email or user id'

    def add_arguments(self, parser):
        parser.add_argument('identifier', nargs=1, help='User email or user id')

    def handle(self, *args, **options):
        ident = options['identifier'][0]
        try:
            if ident.isdigit():
                user = User.objects.get(id=int(ident))
            else:
                user = User.objects.get(email=ident)
        except User.DoesNotExist:
            raise CommandError(f'User not found for identifier: {ident}')

        success = send_welcome_email(user)
        if success:
            self.stdout.write(self.style.SUCCESS(f'Welcome email sent to {user.email}'))
        else:
            raise CommandError('Failed to send welcome email. Check logs for details.')
