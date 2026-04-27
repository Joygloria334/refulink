from rest_framework import serializers


class RINVerificationSerializer(serializers.Serializer):
    """Accepts the alien ID number for verification."""
    identifier = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Alien ID number to verify (e.g. 12345678)",
    )


class AlienCheckResponseSerializer(serializers.Serializer):
    """Shapes the successful verification response."""
    verified = serializers.BooleanField()
    message = serializers.CharField()
    user_info = serializers.DictField(child=serializers.CharField(), required=False)
    tokens = serializers.DictField(child=serializers.CharField(), required=False)


class RegisterRefugeeIdentitySerializer(serializers.Serializer):
    """Links an authenticated user's account to a Stellar public key."""
    stellar_public_key = serializers.CharField(
        max_length=56,
        min_length=56,
        help_text="Refugee's Stellar G... public key (56 chars)",
    )

    def validate_stellar_public_key(self, value):
        if not value.startswith("G"):
            raise serializers.ValidationError("Stellar public key must start with 'G'.")
        return value


class RequestVouchSerializer(serializers.Serializer):
    """Initiates a vouch request from an Ambassador's public key."""
    ambassador_public_key = serializers.CharField(
        max_length=56,
        min_length=56,
        help_text="Trusted Ambassador's Stellar G... public key (56 chars)",
    )

    def validate_ambassador_public_key(self, value):
        if not value.startswith("G"):
            raise serializers.ValidationError("Ambassador public key must start with 'G'.")
        return value


class VouchStatusSerializer(serializers.Serializer):
    """Returns the current verification status for a refugee."""
    verification_status = serializers.CharField()
    stellar_public_key = serializers.CharField()
    hashed_rin = serializers.CharField()
    vouched_by = serializers.CharField(allow_blank=True)
    vouched_at = serializers.DateTimeField(allow_null=True)
