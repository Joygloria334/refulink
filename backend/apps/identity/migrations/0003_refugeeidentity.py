from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("identity", "0002_alter_alienid_options_remove_alienid_full_name_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RefugeeIdentity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hashed_rin", models.CharField(db_index=True, max_length=64, unique=True)),
                ("stellar_public_key", models.CharField(max_length=56, unique=True)),
                (
                    "verification_status",
                    models.CharField(
                        choices=[
                            ("UNVERIFIED", "Unverified"),
                            ("PENDING", "Pending"),
                            ("VOUCHED", "Vouched"),
                        ],
                        default="UNVERIFIED",
                        max_length=20,
                    ),
                ),
                ("vouched_by", models.CharField(blank=True, default="", max_length=56)),
                ("vouched_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refugee_identity",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Refugee Identity",
                "verbose_name_plural": "Refugee Identities",
                "ordering": ["-created_at"],
            },
        ),
    ]
