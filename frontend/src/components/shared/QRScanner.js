import React, { useEffect, useRef, useState } from "react";
import {
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { Camera } from "expo-camera";

export default function QRScanner({ visible, onScan, onClose }) {
  const [hasPermission, setHasPermission] = useState(null);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    if (visible) {
      setScanned(false);
      Camera.requestCameraPermissionsAsync().then(({ status }) => {
        setHasPermission(status === "granted");
      });
    }
  }, [visible]);

  const handleBarCodeScanned = ({ type, data }) => {
    if (scanned) return;
    setScanned(true);
    onScan(data);
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
        <Text style={styles.title}>Scan Ambassador QR Code</Text>
        <Text style={styles.subtitle}>
          Point your camera at the Ambassador's QR code
        </Text>

        {hasPermission === null && (
          <Text style={styles.info}>Requesting camera permission…</Text>
        )}

        {hasPermission === false && (
          <Text style={styles.error}>
            Camera access denied. Please enable it in Settings.
          </Text>
        )}

        {hasPermission === true && (
          <Camera
            style={styles.camera}
            onBarCodeScanned={handleBarCodeScanned}
            barCodeScannerSettings={{
              barCodeTypes: ["qr"],
            }}
          >
            <View style={styles.overlay}>
              <View style={styles.scanFrame} />
            </View>
          </Camera>
        )}

        <TouchableOpacity style={styles.cancelBtn} onPress={onClose}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
    alignItems: "center",
    paddingTop: 60,
  },
  title: {
    color: "#FF6B00",
    fontSize: 20,
    fontWeight: "700",
    marginBottom: 8,
  },
  subtitle: {
    color: "#9CA3AF",
    fontSize: 14,
    marginBottom: 32,
    textAlign: "center",
    paddingHorizontal: 24,
  },
  camera: {
    width: "100%",
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    alignItems: "center",
    justifyContent: "center",
  },
  scanFrame: {
    width: 240,
    height: 240,
    borderWidth: 2,
    borderColor: "#FF6B00",
    borderRadius: 12,
    backgroundColor: "transparent",
  },
  info: { color: "#9CA3AF", marginTop: 40 },
  error: { color: "#EF4444", marginTop: 40, textAlign: "center", paddingHorizontal: 24 },
  cancelBtn: {
    marginTop: 24,
    marginBottom: 40,
    paddingHorizontal: 32,
    paddingVertical: 14,
    backgroundColor: "#1A1A1A",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#374151",
  },
  cancelText: { color: "#fff", fontWeight: "600", fontSize: 15 },
});
