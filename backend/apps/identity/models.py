from django.db import models

class AlienID(models.Model):
    """
    Mock IPRS (Integrated Population Registration System) database.
    Used to verify Alien IDs and Refugee Identity Numbers (RIN) 
    during the KYC process.
    """
    # Primary Identifiers
    id_number = models.CharField(
        max_length=20, 
        unique=True, 
        db_index=True,
        help_text="The Alien ID card number (e.g., 123456)"
    )
    rin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    hashed_rin = models.CharField(max_length=64, unique=True, null=True, blank=True)
    
    # Identity Details
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True, 
        help_text="Designates if this ID is currently valid in the registry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Alien ID"
        verbose_name_plural = "Alien IDs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"