"""
Alien ID Verification Service — calls the external IPRS Alien Check API.
Falls back to the local mock database if ALIEN_CHECK_API_URL is not configured.
"""
import logging
import requests
from requests.structures import CaseInsensitiveDict
from django.conf import settings

logger = logging.getLogger(__name__)

class AlienCheckError(Exception):
    """Raised when the external Alien Check API returns an error."""
    pass

# --- FIX 1: Added last_name to the main function signature ---
def verify_alien_id(identifier: str, last_name: str = None) -> dict:
    """
    Verify an Alien ID against the external IPRS Alien Check API.
    """
    api_url = getattr(settings, 'ALIEN_CHECK_API_URL', None)
    api_token = getattr(settings, 'ALIEN_CHECK_API_TOKEN', None)

    if not api_url or not api_token:
        # --- FIX 2: Pass the last_name to the mock helper ---
        return _verify_via_mock(identifier, last_name)

    return _verify_via_api(api_url, api_token, identifier)


def _verify_via_api(api_url: str, api_token: str, identifier: str) -> dict:
    """Call the live Alien Check endpoint (unchanged)."""
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {api_token}"
    headers["Content-Type"] = "application/json"

    payload = {
        "search_type": "ALIENCHECK",
        "identifier": identifier,
        "consent": "1",
        "consent_collected_by": "",
    }

    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        logger.error("Alien Check API request failed: %s", exc)
        raise AlienCheckError(f"Network error: {exc}")

    if resp.status_code != 200:
        raise AlienCheckError(f"Verification service returned status {resp.status_code}")

    try:
        data = resp.json()
    except ValueError:
        raise AlienCheckError("Verification service returned invalid JSON")

    identity = data.get("data", data)
    verified = bool(identity.get("valid", identity.get("identity_verified", False)))

    full_name = " ".join(
        filter(None, [
            identity.get("first_name", ""),
            identity.get("middle_name", ""),
            identity.get("last_name", identity.get("surname", "")),
        ])
    ) or identity.get("name", None)

    return {
        "verified": verified,
        "full_name": full_name,
        "id_number": identifier,
        "raw_response": data,
    }


def _verify_via_mock(identifier: str, last_name_input: str = None) -> dict:
    """Fall back to the local AlienID mock table."""
    import hashlib
    from .models import AlienID

    # --- FIX 3: Use cleaned identifier consistently ---
    id_clean = identifier.strip()
    hashed = hashlib.sha256(id_clean.encode()).hexdigest()
    
    record = AlienID.objects.filter(hashed_rin=hashed, is_active=True).first()

    if not record:
        record = AlienID.objects.filter(id_number=id_clean, is_active=True).first()

    if record:
        # Matching logic
        if last_name_input:
            if record.last_name.strip().lower() != last_name_input.strip().lower():
                return {
                    "verified": False,
                    "full_name": None, # Security: Hide real name on mismatch
                    "id_number": id_clean,
                    "raw_response": {
                        "source": "mock_db",
                        "error": "name_mismatch"
                    },
                }

        return {
            "verified": True,
            "full_name": record.full_name,
            "id_number": id_clean,
            "raw_response": {"source": "mock_db"},
        }

    return {
        "verified": False,
        "full_name": None,
        "id_number": id_clean,
        "raw_response": {"source": "mock_db", "error": "not_found"},
    }