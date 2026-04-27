import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";

import StatusBadge from "../../components/shared/StatusBadge";
import QRScanner from "../../components/shared/QRScanner";
import { getVouchStatus, requestVouch } from "../../services/verificationService";

const STATUS_DESCRIPTIONS = {
  UNVERIFIED: "Your identity has not yet been verified on the Stellar network.",
  PENDING: "Your vouch request is pending. The Ambassador must sign on-chain.",
  VOUCHED: "Your identity is verified and recorded on the Stellar blockchain.",
};

export default function VerificationDashboard() {
  const [identity, setIdentity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [vouching, setVouching] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getVouchStatus();
      setIdentity(data);
    } catch {
      Alert.alert("Error", "Could not load verification status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(fetchStatus);

  const handleQRScan = async (ambassadorPublicKey) => {
    setScanning(false);
    if (!ambassadorPublicKey.startsWith("G") || ambassadorPublicKey.length !== 56) {
      Alert.alert("Invalid QR", "This QR code does not contain a valid Ambassador key.");
      return;
    }
    try {
      setVouching(true);
      await requestVouch(ambassadorPublicKey);
      Alert.alert(
        "Request Submitted",
        "Your vouch request has been sent. The Ambassador will review and sign the agreement."
      );
      await fetchStatus();
    } catch (err) {
      const message = err.response?.data?.detail || "Failed to submit vouch request.";
      Alert.alert("Error", message);
    } finally {
      setVouching(false);
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-black items-center justify-center">
        <ActivityIndicator color="#FF6B00" size="large" />
      </View>
    );
  }

  const currentStatus = identity?.verification_status ?? "UNVERIFIED";
  const isVouched = currentStatus === "VOUCHED";
  const isPending = currentStatus === "PENDING";

  return (
    <ScrollView
      className="flex-1 bg-black"
      contentContainerStyle={{ paddingHorizontal: 24, paddingTop: 48, paddingBottom: 40 }}
    >
      {/* Header */}
      <Text className="text-white text-3xl font-bold mb-1">Verification</Text>
      <Text className="text-gray-400 text-sm mb-8">
        RefuLink Social Vouching System
      </Text>

      {/* Status Card */}
      <View
        style={{ borderColor: "#FF6B00", borderWidth: 1 }}
        className="bg-neutral-900 rounded-2xl p-5 mb-6"
      >
        <Text className="text-gray-400 text-xs uppercase tracking-widest mb-3">
          Current Status
        </Text>
        <StatusBadge status={currentStatus} />
        <Text className="text-gray-300 text-sm mt-4 leading-5">
          {STATUS_DESCRIPTIONS[currentStatus]}
        </Text>
      </View>

      {/* Identity Details */}
      {identity?.hashed_rin && (
        <View className="bg-neutral-900 rounded-2xl p-5 mb-6">
          <Text className="text-gray-400 text-xs uppercase tracking-widest mb-4">
            Identity Details
          </Text>

          <InfoRow label="Reference Hash" value={truncate(identity.hashed_rin, 24)} />
          <InfoRow
            label="Stellar Address"
            value={truncate(identity.stellar_public_key, 24)}
          />
          {identity.vouched_by ? (
            <InfoRow
              label="Vouched By"
              value={truncate(identity.vouched_by, 24)}
            />
          ) : null}
          {identity.vouched_at ? (
            <InfoRow
              label="Vouched At"
              value={new Date(identity.vouched_at).toLocaleDateString()}
            />
          ) : null}
        </View>
      )}

      {/* Action */}
      {!isVouched && (
        <TouchableOpacity
          onPress={() => setScanning(true)}
          disabled={isPending || vouching}
          style={{
            backgroundColor: isPending || vouching ? "#4B2200" : "#FF6B00",
            borderRadius: 12,
            paddingVertical: 16,
            alignItems: "center",
            marginTop: 8,
          }}
        >
          {vouching ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={{ color: "#fff", fontWeight: "700", fontSize: 16 }}>
              {isPending ? "Awaiting Ambassador Signature" : "Scan Ambassador QR Code"}
            </Text>
          )}
        </TouchableOpacity>
      )}

      {isVouched && (
        <View
          style={{
            borderColor: "#22C55E",
            borderWidth: 1,
            borderRadius: 12,
            paddingVertical: 16,
            alignItems: "center",
            backgroundColor: "#052E16",
          }}
        >
          <Text style={{ color: "#22C55E", fontWeight: "700", fontSize: 16 }}>
            Identity Verified on Stellar
          </Text>
        </View>
      )}

      {/* QR Scanner Modal */}
      <QRScanner
        visible={scanning}
        onScan={handleQRScan}
        onClose={() => setScanning(false)}
      />
    </ScrollView>
  );
}

function InfoRow({ label, value }) {
  return (
    <View className="mb-3">
      <Text className="text-gray-500 text-xs mb-1">{label}</Text>
      <Text className="text-white text-sm font-mono">{value}</Text>
    </View>
  );
}

function truncate(str, maxLen) {
  if (!str) return "";
  if (str.length <= maxLen) return str;
  return `${str.slice(0, maxLen / 2)}…${str.slice(-maxLen / 2)}`;
}
