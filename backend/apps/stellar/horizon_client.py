import os

from stellar_sdk import Server

_HORIZON_URL = os.getenv("STELLAR_HORIZON_URL", "https://horizon-testnet.stellar.org")
_KES_ASSET_CODE = "KES"
_KES_ASSET_ISSUER = os.getenv(
    "KES_ASSET_ISSUER",
    "GDAS5OGUZVKJP6UFKNTN23QKOUNDZV7RQCGQH6MOMX5DTDEYZMQFPVK",  # ClickPesa testnet
)


def _server() -> Server:
    return Server(_HORIZON_URL)


def get_kes_balance(stellar_address: str) -> float:
    """Returns KES balance for the given Stellar address. 0.0 if no trustline."""
    try:
        account = _server().accounts().account_id(stellar_address).call()
    except Exception:
        return 0.0
    for bal in account.get("balances", []):
        if (
            bal.get("asset_code") == _KES_ASSET_CODE
            and bal.get("asset_issuer") == _KES_ASSET_ISSUER
        ):
            return float(bal["balance"])
    return 0.0


def get_transactions(stellar_address: str, limit: int = 20) -> list:
    """
    Fetches recent payment operations for the given Stellar address from Horizon.
    Returns a list of normalised transaction dicts ready for the API response.
    KES anchor is 1:1, so amount_kes == raw token amount.
    """
    try:
        payments = (
            _server()
            .payments()
            .for_account(stellar_address)
            .limit(limit)
            .order(desc=True)
            .call()
        )
    except Exception:
        return []

    result = []
    for record in payments.get("_embedded", {}).get("records", []):
        op_type = record.get("type")
        if op_type not in ("payment", "create_account"):
            continue

        is_receive = record.get("to") == stellar_address

        if op_type == "payment":
            asset_code = record.get("asset_code", "XLM")
            amount = float(record.get("amount", 0))
        else:
            asset_code = "XLM"
            amount = float(record.get("starting_balance", 0))

        result.append({
            "id": record.get("id", ""),
            "type": "receive" if is_receive else "send",
            "amount_kes": amount,
            "counterparty": record.get("from") if is_receive else record.get("to", ""),
            "timestamp": record.get("created_at", ""),
            "status": "completed",
            "asset_code": asset_code,
            "tx_hash": record.get("transaction_hash", ""),
        })
    return result
