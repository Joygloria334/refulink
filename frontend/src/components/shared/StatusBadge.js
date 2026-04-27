import React from "react";
import { View, Text } from "react-native";

const STATUS_CONFIG = {
  UNVERIFIED: {
    label: "Unverified",
    bg: "#1A1A1A",
    border: "#4B5563",
    text: "#9CA3AF",
    dot: "#6B7280",
  },
  PENDING: {
    label: "Pending",
    bg: "#1F0E00",
    border: "#FF6B00",
    text: "#FF6B00",
    dot: "#FF6B00",
  },
  VOUCHED: {
    label: "Vouched",
    bg: "#052E16",
    border: "#22C55E",
    text: "#22C55E",
    dot: "#22C55E",
  },
};

export default function StatusBadge({ status = "UNVERIFIED" }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.UNVERIFIED;

  return (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        alignSelf: "flex-start",
        paddingHorizontal: 14,
        paddingVertical: 7,
        borderRadius: 999,
        borderWidth: 1,
        backgroundColor: config.bg,
        borderColor: config.border,
      }}
    >
      <View
        style={{
          width: 8,
          height: 8,
          borderRadius: 4,
          backgroundColor: config.dot,
          marginRight: 7,
        }}
      />
      <Text style={{ color: config.text, fontWeight: "600", fontSize: 13 }}>
        {config.label}
      </Text>
    </View>
  );
}
