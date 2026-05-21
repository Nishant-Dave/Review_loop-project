from django.core.management.base import BaseCommand
from reviews.models import Cafe

class Command(BaseCommand):
    help = 'Generates missing QR codes for all Cafes'

    def handle(self, *args, **options):
        cafes = Cafe.objects.all()
        generated_count = 0
        already_had_count = 0

        for cafe in cafes:
            if not cafe.qr_code:
                # cafe.save() will automatically generate and save the QR code if missing
                cafe.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully generated QR code for cafe: "{cafe.name}"'))
                generated_count += 1
            else:
                already_had_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'QR code generation completed. Generated: {generated_count}, Already existing: {already_had_count}.'
        ))
