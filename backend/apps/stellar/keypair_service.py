import hashlib

from stellar_sdk import Keypair


def generate_keypair() -> dict:
    """
    Generates a new random Stellar keypair.
    Returns {"public_key": str, "secret_key": str}.
    The secret_key must be returned to the client ONCE and never persisted server-side.
    """
    kp = Keypair.random()
    return {
        "public_key": kp.public_key,
        "secret_key": kp.secret,
    }


def hash_rin(rin: str) -> str:
    """SHA-256 hashes a Refugee Identity Number. Returns 64-char hex string."""
    return hashlib.sha256(rin.encode("utf-8")).hexdigest()
