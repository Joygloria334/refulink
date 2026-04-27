from datetime import date

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False

_AGREEMENT_TEMPLATE = """VOUCHING AGREEMENT — RefuLink Programme

I, the undersigned Trusted Ambassador, hereby attest that I have personally \
verified the identity of the refugee associated with the Reference Hash below. \
I confirm that the identity documents presented are authentic and that the \
information is accurate to the best of my knowledge.

By signing this attestation on the Stellar blockchain, I acknowledge that this \
record is immutable and will serve as the basis for the individual's access to \
financial inclusion services under the RefuLink programme.

Ambassador Public Key : {ambassador_public_key}
Refugee Reference Hash: {hashed_rin}
Date                  : {date}

I accept full responsibility for the accuracy of this verification."""

_SUPPORTED = {
    "sw": "Swahili",
    "so": "Somali",
}


def translate_vouching_agreement(
    ambassador_public_key: str,
    hashed_rin: str,
    signing_date: str = "",
) -> dict:
    """
    Returns the vouching agreement text in English, Swahili, and Somali.
    Falls back to English for any language where translation fails.
    """
    if not signing_date:
        signing_date = date.today().isoformat()

    english = _AGREEMENT_TEMPLATE.format(
        ambassador_public_key=ambassador_public_key,
        hashed_rin=hashed_rin,
        date=signing_date,
    )

    translations = {"en": english}

    if not _TRANSLATOR_AVAILABLE:
        for code in _SUPPORTED:
            translations[code] = english
        return translations

    for lang_code in _SUPPORTED:
        try:
            # deep-translator handles chunking internally for long texts
            translated = GoogleTranslator(source="en", target=lang_code).translate(english)
            translations[lang_code] = translated or english
        except Exception:
            translations[lang_code] = english

    return translations
