from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Print planned content seed status; initial homepage content is currently static."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "GLORY foundation is ready. The next phase will add database-backed Scripture, prayer, profiles, and saved reflections."
        ))
