import hashlib
from django.core.management.base import BaseCommand
from apps.identity.models import AlienID

class Command(BaseCommand):
    help = "Seeds the mock IPRS database with sample Alien ID and RIN records"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Mock IPRS data...")

        sample_records = [
            {
                "id_number": "ID123456",
                "rin": "REF-001-AAA",
                "first_name": "Jane",
                "last_name": "Doe",
                "is_active": True,
            },
            {
                "id_number": "ID789012",
                "rin": "REF-002-BBB",
                "first_name": "John",
                "last_name": "Smith",
                "is_active": True,
            },
            {
                "id_number": "ID111222",
                "rin": "REF-003-CCC",
                "first_name": "Musa",
                "last_name": "Hassan",
                "is_active": False,
            },
        ]

        for data in sample_records:
            # Generate the SHA-256 hash of the RIN
            rin_hash = hashlib.sha256(data['rin'].encode()).hexdigest()
            
            obj, created = AlienID.objects.update_or_create(
                id_number=data['id_number'],
                defaults={
                    "rin": data['rin'],
                    "hashed_rin": rin_hash,
                    "first_name": data['first_name'],
                    "last_name": data['last_name'],
                    "is_active": data['is_active'],
                }
            )

            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status}: {data['id_number']}"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded Mock IPRS database."))