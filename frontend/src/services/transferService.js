import AsyncStorage from "@react-native-async-storage/async-storage";

import api from "./api";

/**
 * Sends KES tokens to a destination Stellar address via the backend relay.
 *
 * Architecture: the backend holds the signing key in the SENDER_SECRET_KEY env var
 * and submits the transaction to Horizon server-side.
 *
 * For production client-side signing, replace the api.post call with:
 *   1. Build unsigned XDR via stellar-base
 *   2. Sign with privateKey from SecureStore (expo-secure-store)
 *   3. Submit signed XDR directly to Horizon
 *   4. Call logTransaction() for the audit trail
 *
 * @param {string} destinationAddress  56-char Stellar G... address
 * @param {number|string} amountKes    Positive KES amount
 * @returns {{ success: boolean, txHash: string, amount: string, destination: string }}
 */
export const sendToken = async (destinationAddress, amountKes) => {
  if (!destinationAddress || !amountKes) {
    throw new Error("Destination and amount are required.");
  }
  if (typeof destinationAddress !== "string" || !destinationAddress.startsWith("G") || destinationAddress.length !== 56) {
    throw new Error("Invalid Stellar address. Must be a 56-character G... key.");
  }
  if (parseFloat(amountKes) <= 0) {
    throw new Error("Amount must be greater than zero.");
  }

  const token = await AsyncStorage.getItem("access_token");
  if (!token) throw new Error("Not authenticated. Please log in.");

  const { data } = await api.post("/wallet/send/", {
    destination_address: destinationAddress,
    amount_kes: parseFloat(amountKes),
  });

  return {
    success: true,
    txHash: data.tx_hash,
    amount: data.amount_kes,
    destination: data.destination,
  };
};

/**
 * Posts a transaction audit record to the backend.
 * Non-blocking — caller should fire-and-forget (don't await the error).
 */
export const logTransaction = async (
  txHash,
  direction,
  amountKes,
  counterpartyAddress,
  txStatus = "completed"
) => {
  try {
    await api.post("/wallet/audit/", {
      tx_hash: txHash,
      direction,
      amount_kes: amountKes,
      counterparty_address: counterpartyAddress,
      status: txStatus,
    });
  } catch {
    // Audit failures must not surface to the user
  }
};
