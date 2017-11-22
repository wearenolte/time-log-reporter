# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/


from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sends the reports of the current week'

    def handle(self, *args, **options):
        self.stdout.write("Starting")
        self.stdout.write("Finishing")