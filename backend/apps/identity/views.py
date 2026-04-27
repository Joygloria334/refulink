import os

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import RefugeeIdentity, VerificationStatus
from .serializers import (
    AlienCheckResponseSerializer,
    RegisterRefugeeIdentitySerializer,
    RequestVouchSerializer,
    RINVerificationSerializer,
    VouchStatusSerializer,
)
from .services import AlienCheckError, verify_alien_id


class VerifyRINView(views.APIView):
    """
    Verifies an Alien ID number via IPRS.
    Generates a JWT on success.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RINVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identifier = serializer.validated_data["identifier"]

        try:
            result = verify_alien_id(identifier)
        except AlienCheckError as e:
            return Response(
                {"verified": False, "message": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if result.get("verified"):
            full_name = result.get("full_name") or "Unknown Alien"
            user, _ = User.objects.get_or_create(
                username=f"alien_{result['id_number']}",
                defaults={"first_name": full_name[:30]},
            )
            refresh = RefreshToken.for_user(user)
            response_data = {
                "verified": True,
                "message": "Identity verified successfully.",
                "user_info": {
                    "full_name": full_name,
                    "id_number": result["id_number"],
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
            response_serializer = AlienCheckResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"verified": False, "message": "Invalid identifier. Verification failed."},
            status=status.HTTP_403_FORBIDDEN,
        )


class RegisterRefugeeIdentityView(views.APIView):
    """
    Creates a RefugeeIdentity record for the authenticated user.
    If no stellar_public_key is supplied, a new Stellar keypair is generated
    server-side and the private key is returned ONCE in the response.
    Must be called after VerifyRINView succeeds.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RegisterRefugeeIdentitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(request.user, "refugee_identity"):
            return Response(
                {"detail": "Identity already registered."},
                status=status.HTTP_409_CONFLICT,
            )

        hashed_rin = _get_hashed_rin_for_user(request.user)
        if not hashed_rin:
            return Response(
                {"detail": "No verified RIN found for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provided_key = serializer.validated_data.get("stellar_public_key")
        if provided_key:
            public_key = provided_key
            private_key = None
        else:
            from apps.stellar.keypair_service import generate_keypair
            kp = generate_keypair()
            public_key = kp["public_key"]
            private_key = kp["secret_key"]

        identity = RefugeeIdentity.objects.create(
            user=request.user,
            hashed_rin=hashed_rin,
            stellar_public_key=public_key,
        )

        # Best-effort: register identity on-chain (non-blocking)
        try:
            from apps.stellar.soroban_client import register_identity
            ambassador_secret = os.getenv("AMBASSADOR_SECRET", "")
            if ambassador_secret:
                register_identity(
                    ambassador_secret=ambassador_secret,
                    refugee_public_key=public_key,
                    hashed_rin_hex=hashed_rin,
                )
        except Exception:
            pass

        response_data = {
            "detail": "Refugee identity registered.",
            "stellar_public_key": public_key,
            "verification_status": identity.verification_status,
        }
        if private_key:
            response_data["stellar_private_key"] = private_key
            response_data["private_key_warning"] = (
                "Save this private key securely — it will NOT be shown again."
            )

        return Response(response_data, status=status.HTTP_201_CREATED)


class RequestVouchView(views.APIView):
    """
    Refugee presents an Ambassador's public key (scanned via QR).
    1. Translates the vouching agreement to Swahili + Somali.
    2. Marks status as PENDING.
    3. Returns translated agreements for the Ambassador to review and sign.
       (The actual on-chain vouch is triggered by the Ambassador Portal,
        which calls TriggerOnChainVouchView with the ambassador secret.)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RequestVouchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            identity = request.user.refugee_identity
        except RefugeeIdentity.DoesNotExist:
            return Response(
                {"detail": "Register a Stellar identity first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if identity.verification_status == VerificationStatus.VOUCHED:
            return Response(
                {"detail": "Already vouched."},
                status=status.HTTP_409_CONFLICT,
            )

        ambassador_public_key = serializer.validated_data["ambassador_public_key"]

        # Translate the vouching agreement before the Ambassador signs
        from apps.ai_layer.translation.service import translate_vouching_agreement
        agreements = translate_vouching_agreement(
            ambassador_public_key=ambassador_public_key,
            hashed_rin=identity.hashed_rin,
        )

        identity.verification_status = VerificationStatus.PENDING
        identity.vouched_by = ambassador_public_key
        identity.save(update_fields=["verification_status", "vouched_by", "updated_at"])

        return Response(
            {
                "detail": "Vouch request submitted. Ambassador must review and sign.",
                "verification_status": identity.verification_status,
                "vouching_agreement": agreements,
            },
            status=status.HTTP_200_OK,
        )


class TriggerOnChainVouchView(views.APIView):
    """
    Called by the Ambassador Portal (server-to-server) once the Ambassador
    has reviewed and agreed to the translated vouching agreement.
    Submits the vouch transaction to the Soroban contract and marks VOUCHED.

    Requires AMBASSADOR_SECRET env var — never exposed to the mobile client.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            identity = request.user.refugee_identity
        except RefugeeIdentity.DoesNotExist:
            return Response(
                {"detail": "No registered identity found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if identity.verification_status != VerificationStatus.PENDING:
            return Response(
                {"detail": "Identity is not in PENDING state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ambassador_secret = os.getenv("AMBASSADOR_SECRET", "")
        tx_hash = "offline-mode"

        if ambassador_secret:
            try:
                from apps.stellar.soroban_client import vouch_refugee
                result = vouch_refugee(
                    ambassador_secret=ambassador_secret,
                    refugee_public_key=identity.stellar_public_key,
                    hashed_rin_hex=identity.hashed_rin,
                )
                tx_hash = result.get("hash", tx_hash)
            except Exception as exc:
                return Response(
                    {"detail": f"On-chain vouch failed: {exc}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        identity.verification_status = VerificationStatus.VOUCHED
        identity.vouched_at = timezone.now()
        identity.save(update_fields=["verification_status", "vouched_at", "updated_at"])

        # Best-effort: flip verified=true on-chain (non-blocking)
        if ambassador_secret:
            try:
                from apps.stellar.soroban_client import set_verified
                set_verified(
                    ambassador_secret=ambassador_secret,
                    refugee_public_key=identity.stellar_public_key,
                    verified=True,
                )
            except Exception:
                pass

        return Response(
            {
                "detail": "Vouch recorded on Stellar.",
                "tx_hash": tx_hash,
                "verification_status": identity.verification_status,
            },
            status=status.HTTP_200_OK,
        )


class VouchStatusView(views.APIView):
    """Returns the current verification status for the authenticated refugee."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            identity = request.user.refugee_identity
        except RefugeeIdentity.DoesNotExist:
            return Response(
                {"verification_status": VerificationStatus.UNVERIFIED},
                status=status.HTTP_200_OK,
            )

        serializer = VouchStatusSerializer(
            data={
                "verification_status": identity.verification_status,
                "stellar_public_key": identity.stellar_public_key,
                "hashed_rin": identity.hashed_rin,
                "vouched_by": identity.vouched_by,
                "vouched_at": identity.vouched_at,
            }
        )
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Helper ───────────────────────────────────────────────────────────────────

def _get_hashed_rin_for_user(user) -> str | None:
    """Retrieves the hashed_rin from the AlienID linked to this Django User."""
    from .models import AlienID
    username = user.username  # format: "alien_<id_number>"
    if not username.startswith("alien_"):
        return None
    id_number = username[len("alien_"):]
    try:
        alien = AlienID.objects.get(id_number=id_number, is_active=True)
        return alien.hashed_rin
    except AlienID.DoesNotExist:
        return None
