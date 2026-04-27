from rest_framework import serializers


class TransactionSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.ChoiceField(choices=["send", "receive"])
    amount_kes = serializers.FloatField()
    counterparty = serializers.CharField(allow_blank=True)
    timestamp = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    asset_code = serializers.CharField()
    tx_hash = serializers.CharField(allow_blank=True)


class BalanceSerializer(serializers.Serializer):
    kes_balance = serializers.FloatField()
    stellar_address = serializers.CharField()


class SendTokenRequestSerializer(serializers.Serializer):
    destination_address = serializers.CharField(max_length=56, min_length=56)
    amount_kes = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)

    def validate_destination_address(self, value):
        if not value.startswith("G"):
            raise serializers.ValidationError("Destination must be a valid Stellar G... address.")
        return value


class AuditLogSerializer(serializers.Serializer):
    tx_hash = serializers.CharField(max_length=64)
    direction = serializers.ChoiceField(choices=["send", "receive"])
    amount_kes = serializers.DecimalField(max_digits=14, decimal_places=2)
    counterparty_address = serializers.CharField(max_length=56)
    status = serializers.ChoiceField(choices=["pending", "completed", "failed"])
