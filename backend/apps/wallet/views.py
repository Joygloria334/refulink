import os

from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder

from apps.stellar.horizon_client import get_kes_balance, get_transactions

from .models import TransactionLog
from .serializers import (
    AuditLogSerializer,
    BalanceSerializer,
    SendTokenRequestSerializer,
    TransactionSerializer,
)

_HORIZON_URL = os.getenv("STELLAR_HORIZON_URL", "https://horizon-testnet.stellar.org")
_KES_ASSET_CODE = "KES"
_ERR_NO_IDENTITY = "No Stellar identity registered."
_KES_ASSET_ISSUER = os.getenv(
    "KES_ASSET_ISSUER",
    "GDAS5OGUZVKJP6UFKNTN23QKOUNDZV7RQCGQH6MOMX5DTDEYZMQFPVK",
)


def _get_identity(user):
    try:
        return user.refugee_identity
    except Exception:
        return None


class BalanceView(views.APIView):
    """GET /api/wallet/balance/ — Returns KES balance from Horizon."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        identity = _get_identity(request.user)
        if not identity:
            return Response(
                {"detail": _ERR_NO_IDENTITY},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            balance = get_kes_balance(identity.stellar_public_key)
        except Exception as exc:
            return Response(
                {"detail": f"Horizon error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        serializer = BalanceSerializer(
            data={"kes_balance": balance, "stellar_address": identity.stellar_public_key}
        )
        serializer.is_valid()
        return Response(serializer.data)


class TransactionHistoryView(views.APIView):
    """
    GET /api/wallet/transactions/
    Fetches the user's Stellar payment history from Horizon and returns it
    as a clean JSON list formatted for the mobile wallet feed.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        identity = _get_identity(request.user)
        if not identity:
            return Response(
                {"detail": _ERR_NO_IDENTITY},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            transactions = get_transactions(identity.stellar_public_key)
        except Exception as exc:
            return Response(
                {"detail": f"Horizon error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        serializer = TransactionSerializer(data=transactions, many=True)
        serializer.is_valid()
        return Response({"transactions": serializer.data})


class SendTokenView(views.APIView):
    """
    POST /api/wallet/send/
    Backend relay: builds, signs, and submits a KES payment on Stellar.
    Uses SENDER_SECRET_KEY env var for signing.

    Body: { destination_address: str, amount_kes: decimal }

    Note: In production, move signing to the client (stellar-base) and use
    this endpoint only for submission + audit. The client should sign locally
    with a key stored in expo-secure-store and POST the signed XDR here.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = SendTokenRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identity = _get_identity(request.user)
        if not identity:
            return Response(
                {"detail": _ERR_NO_IDENTITY},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sender_secret = os.getenv("SENDER_SECRET_KEY", "")
        destination = serializer.validated_data["destination_address"]
        amount = str(serializer.validated_data["amount_kes"])

        if not sender_secret:
            # Dev / offline mode: log the intent without hitting Stellar
            import uuid
            tx_hash = f"dev-{uuid.uuid4().hex[:16]}"
            TransactionLog.objects.create(
                user=request.user,
                tx_hash=tx_hash,
                direction=TransactionLog.Direction.SEND,
                amount_kes=serializer.validated_data["amount_kes"],
                counterparty_address=destination,
                status=TransactionLog.TxStatus.COMPLETED,
            )
            return Response(
                {
                    "detail": "Dev mode: transaction logged without Stellar submission.",
                    "tx_hash": tx_hash,
                    "amount_kes": amount,
                    "destination": destination,
                },
                status=status.HTTP_200_OK,
            )

        try:
            server = Server(_HORIZON_URL)
            sender_kp = Keypair.from_secret(sender_secret)
            source = server.load_account(sender_kp.public_key)
            kes_asset = Asset(_KES_ASSET_CODE, _KES_ASSET_ISSUER)

            tx = (
                TransactionBuilder(
                    source_account=source,
                    network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                    base_fee=100,
                )
                .set_timeout(30)
                .append_payment_op(
                    destination=destination,
                    asset=kes_asset,
                    amount=amount,
                )
                .build()
            )
            tx.sign(sender_kp)
            response = server.submit_transaction(tx)
            tx_hash = response.get("hash") or response.get("id", "unknown")
        except Exception as exc:
            return Response(
                {"detail": f"Transaction failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        TransactionLog.objects.create(
            user=request.user,
            tx_hash=tx_hash,
            direction=TransactionLog.Direction.SEND,
            amount_kes=serializer.validated_data["amount_kes"],
            counterparty_address=destination,
            status=TransactionLog.TxStatus.COMPLETED,
        )

        return Response(
            {
                "detail": "Transaction submitted.",
                "tx_hash": tx_hash,
                "amount_kes": amount,
                "destination": destination,
            },
            status=status.HTTP_200_OK,
        )


class AuditLogView(views.APIView):
    """
    POST /api/wallet/audit/
    Clients that sign and submit transactions locally (client-side signing)
    call this endpoint to create the internal audit record.
    Idempotent — duplicate tx_hash is silently accepted.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AuditLogSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tx_hash = serializer.validated_data["tx_hash"]
        if TransactionLog.objects.filter(tx_hash=tx_hash).exists():
            return Response({"detail": "Already logged."}, status=status.HTTP_200_OK)

        TransactionLog.objects.create(
            user=request.user,
            **serializer.validated_data,
        )
        return Response({"detail": "Audit logged."}, status=status.HTTP_201_CREATED)
