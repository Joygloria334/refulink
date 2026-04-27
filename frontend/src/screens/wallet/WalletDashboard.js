import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  SafeAreaView,
  StatusBar,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { sendToken } from "../../services/transferService";
import { getBalance, getTransactions } from "../../services/walletService";

// ── Balance Card ─────────────────────────────────────────────────────────────

function BalanceCard({ balance, address, loading }) {
  return (
    <View className="bg-zinc-900 rounded-2xl p-6 mx-4 mt-4 border border-zinc-800">
      <Text className="text-zinc-400 text-sm mb-1">Available Balance</Text>
      {loading ? (
        <ActivityIndicator color="#FF6B00" size="large" style={{ marginVertical: 8 }} />
      ) : (
        <Text className="text-white text-4xl font-bold">
          KES {parseFloat(balance ?? 0).toFixed(2)}
        </Text>
      )}
      <Text className="text-zinc-500 text-xs mt-3" numberOfLines={1}>
        {address || "—"}
      </Text>
    </View>
  );
}

// ── Action Bar ────────────────────────────────────────────────────────────────

const ACTIONS = [
  { key: "send",     label: "Send",     icon: "↑" },
  { key: "receive",  label: "Receive",  icon: "↓" },
  { key: "scanQR",   label: "Scan QR",  icon: "⊡" },
  { key: "withdraw", label: "Withdraw", icon: "⊞" },
];

function ActionBar({ onPress }) {
  return (
    <View className="flex-row mx-4 mt-6 gap-2">
      {ACTIONS.map(({ key, label, icon }) => (
        <TouchableOpacity
          key={key}
          onPress={() => onPress(key)}
          className="flex-1 bg-orange-500 rounded-xl py-3 items-center"
          activeOpacity={0.8}
        >
          <Text className="text-black text-xl font-bold">{icon}</Text>
          <Text className="text-black text-xs font-semibold mt-1">{label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

// ── Transaction Item ──────────────────────────────────────────────────────────

function TransactionItem({ item }) {
  const isReceive = item.type === "receive";
  const shortAddress = item.counterparty
    ? `${item.counterparty.slice(0, 6)}…${item.counterparty.slice(-4)}`
    : "Unknown";
  const dateLabel = item.timestamp
    ? new Date(item.timestamp).toLocaleDateString()
    : "—";

  return (
    <View className="flex-row items-center px-4 py-3 border-b border-zinc-800">
      <View
        className="w-10 h-10 rounded-full items-center justify-center mr-3"
        style={{ backgroundColor: isReceive ? "#166534" : "#7f1d1d" }}
      >
        <Text className="text-white text-base font-bold">
          {isReceive ? "+" : "−"}
        </Text>
      </View>

      <View className="flex-1">
        <Text className="text-white text-sm font-semibold" numberOfLines={1}>
          {shortAddress}
        </Text>
        <Text className="text-zinc-500 text-xs mt-0.5">{dateLabel}</Text>
      </View>

      <View className="items-end">
        <Text
          className="text-base font-bold"
          style={{ color: isReceive ? "#22C55E" : "#EF4444" }}
        >
          {isReceive ? "+" : "−"}KES {parseFloat(item.amount_kes).toFixed(2)}
        </Text>
        <Text className="text-zinc-600 text-xs capitalize">{item.status}</Text>
      </View>
    </View>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function WalletDashboard({ navigation }) {
  const [balance, setBalance] = useState(null);
  const [address, setAddress] = useState("");
  const [transactions, setTransactions] = useState([]);
  const [loadingBalance, setLoadingBalance] = useState(true);
  const [loadingTx, setLoadingTx] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchBalance = useCallback(async () => {
    try {
      const data = await getBalance();
      setBalance(data.kes_balance);
      setAddress(data.stellar_address);
    } catch {
      setBalance(0);
    } finally {
      setLoadingBalance(false);
    }
  }, []);

  const fetchTransactions = useCallback(async () => {
    try {
      const txs = await getTransactions();
      setTransactions(txs ?? []);
    } catch {
      setTransactions([]);
    } finally {
      setLoadingTx(false);
    }
  }, []);

  useEffect(() => {
    fetchBalance();
    fetchTransactions();
  }, [fetchBalance, fetchTransactions]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchBalance(), fetchTransactions()]);
    setRefreshing(false);
  }, [fetchBalance, fetchTransactions]);

  const handleAction = (key) => {
    if (key === "send") {
      Alert.prompt("Send KES", "Destination Stellar address:", (dest) => {
        if (!dest) return;
        Alert.prompt("Amount (KES)", "Amount to send:", async (amt) => {
          if (!amt) return;
          try {
            const result = await sendToken(dest.trim(), parseFloat(amt));
            Alert.alert("Sent", `TX hash:\n${result.txHash}`);
            onRefresh();
          } catch (err) {
            Alert.alert("Transfer failed", err.message);
          }
        }, "plain-text");
      }, "plain-text");
      return;
    }
    if (key === "receive") {
      Alert.alert("Receive", `Your Stellar address:\n\n${address}`);
      return;
    }
    if (key === "scanQR") {
      navigation.navigate("VerificationDashboard");
      return;
    }
    if (key === "withdraw") {
      Alert.alert("Withdraw", "M-Pesa withdrawal coming soon.");
    }
  };

  const ListHeader = (
    <>
      <BalanceCard balance={balance} address={address} loading={loadingBalance} />
      <ActionBar onPress={handleAction} />
      <Text className="text-zinc-400 text-sm font-semibold px-4 mt-6 mb-1">
        Recent Transactions
      </Text>
      {loadingTx && (
        <ActivityIndicator color="#FF6B00" style={{ marginVertical: 16 }} />
      )}
      {!loadingTx && transactions.length === 0 && (
        <Text className="text-zinc-600 text-sm text-center py-8">
          No transactions yet.
        </Text>
      )}
    </>
  );

  return (
    <SafeAreaView className="flex-1 bg-black">
      <StatusBar barStyle="light-content" backgroundColor="#000000" />
      <FlatList
        data={transactions}
        keyExtractor={(item) => item.id || item.tx_hash}
        renderItem={({ item }) => <TransactionItem item={item} />}
        ListHeaderComponent={ListHeader}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#FF6B00"
          />
        }
      />
    </SafeAreaView>
  );
}
