import os
import time

from stellar_sdk import Address, Keypair, Network, SorobanServer, TransactionBuilder
from stellar_sdk import scval
from stellar_sdk.soroban_rpc import GetTransactionStatus

_RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org")
_CONTRACT_ID = os.getenv("ORBITAL_CONTRACT_ID", "")
_NETWORK = Network.TESTNET_NETWORK_PASSPHRASE
_POLL_INTERVAL = 2   # seconds between status polls
_POLL_MAX = 20       # max attempts (~40 seconds)
_ERR_NO_CONTRACT = "ORBITAL_CONTRACT_ID is not set"


def _server() -> SorobanServer:
    return SorobanServer(_RPC_URL)


def _wait_for_transaction(server: SorobanServer, tx_hash: str) -> dict:
    for _ in range(_POLL_MAX):
        result = server.get_transaction(tx_hash)
        if result.status == GetTransactionStatus.SUCCESS:
            return {"success": True, "hash": tx_hash}
        if result.status == GetTransactionStatus.FAILED:
            raise RuntimeError(f"Soroban transaction failed: {tx_hash}")
        time.sleep(_POLL_INTERVAL)
    raise TimeoutError(f"Soroban transaction timed out: {tx_hash}")


def register_identity(
    ambassador_secret: str,
    refugee_public_key: str,
    hashed_rin_hex: str,
) -> dict:
    """
    Calls VouchContract.register_identity() on Stellar.
    Stores hashed_rin on-chain and initialises verified=false for the refugee address.
    Returns {"success": True, "hash": "<tx_hash>"} on success.
    """
    if not _CONTRACT_ID:
        raise EnvironmentError(_ERR_NO_CONTRACT)

    server = _server()
    ambassador_kp = Keypair.from_secret(ambassador_secret)
    source = server.load_account(ambassador_kp.public_key)

    hashed_rin_bytes = bytes.fromhex(hashed_rin_hex)
    if len(hashed_rin_bytes) != 32:
        raise ValueError("hashed_rin_hex must be a 64-char hex string (SHA-256)")

    params = [
        scval.to_address(Address(ambassador_kp.public_key)),
        scval.to_address(Address(refugee_public_key)),
        scval.to_bytes(hashed_rin_bytes),
    ]

    tx = (
        TransactionBuilder(
            source_account=source,
            network_passphrase=_NETWORK,
            base_fee=100,
        )
        .set_timeout(30)
        .append_invoke_contract_function_op(
            contract_id=_CONTRACT_ID,
            function_name="register_identity",
            parameters=params,
        )
        .build()
    )

    simulation = server.simulate_transaction(tx)
    if hasattr(simulation, "error") and simulation.error:
        raise RuntimeError(f"Simulation error: {simulation.error}")

    prepared = server.prepare_transaction(tx, simulation)
    prepared.sign(ambassador_kp)
    response = server.send_transaction(prepared)
    return _wait_for_transaction(server, response.hash)


def set_verified(
    ambassador_secret: str,
    refugee_public_key: str,
    verified: bool,
) -> dict:
    """
    Calls VouchContract.set_verified() on Stellar.
    Flips the on-chain verified flag for the refugee address.
    Returns {"success": True, "hash": "<tx_hash>"} on success.
    """
    if not _CONTRACT_ID:
        raise EnvironmentError(_ERR_NO_CONTRACT)

    server = _server()
    ambassador_kp = Keypair.from_secret(ambassador_secret)
    source = server.load_account(ambassador_kp.public_key)

    params = [
        scval.to_address(Address(ambassador_kp.public_key)),
        scval.to_address(Address(refugee_public_key)),
        scval.to_bool(verified),
    ]

    tx = (
        TransactionBuilder(
            source_account=source,
            network_passphrase=_NETWORK,
            base_fee=100,
        )
        .set_timeout(30)
        .append_invoke_contract_function_op(
            contract_id=_CONTRACT_ID,
            function_name="set_verified",
            parameters=params,
        )
        .build()
    )

    simulation = server.simulate_transaction(tx)
    if hasattr(simulation, "error") and simulation.error:
        raise RuntimeError(f"Simulation error: {simulation.error}")

    prepared = server.prepare_transaction(tx, simulation)
    prepared.sign(ambassador_kp)
    response = server.send_transaction(prepared)
    return _wait_for_transaction(server, response.hash)


def vouch_refugee(
    ambassador_secret: str,
    refugee_public_key: str,
    hashed_rin_hex: str,
) -> dict:
    """
    Calls VouchContract.vouch() on Stellar.
    The ambassador_secret signs the transaction — keep it server-side only.
    hashed_rin_hex is the 64-char hex SHA-256 of the refugee's RIN.
    Returns {"success": True, "hash": "<tx_hash>"} on success.
    """
    if not _CONTRACT_ID:
        raise EnvironmentError(_ERR_NO_CONTRACT)

    server = _server()
    ambassador_kp = Keypair.from_secret(ambassador_secret)
    source = server.load_account(ambassador_kp.public_key)

    hashed_rin_bytes = bytes.fromhex(hashed_rin_hex)
    if len(hashed_rin_bytes) != 32:
        raise ValueError("hashed_rin_hex must be a 64-char hex string (SHA-256)")

    params = [
        scval.to_address(Address(ambassador_kp.public_key)),
        scval.to_address(Address(refugee_public_key)),
        scval.to_bytes(hashed_rin_bytes),
    ]

    tx = (
        TransactionBuilder(
            source_account=source,
            network_passphrase=_NETWORK,
            base_fee=100,
        )
        .set_timeout(30)
        .append_invoke_contract_function_op(
            contract_id=_CONTRACT_ID,
            function_name="vouch",
            parameters=params,
        )
        .build()
    )

    simulation = server.simulate_transaction(tx)
    if hasattr(simulation, "error") and simulation.error:
        raise RuntimeError(f"Simulation error: {simulation.error}")

    prepared = server.prepare_transaction(tx, simulation)
    prepared.sign(ambassador_kp)

    response = server.send_transaction(prepared)
    return _wait_for_transaction(server, response.hash)
