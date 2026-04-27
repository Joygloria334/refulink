import React from "react";
import { View, Text, Pressable } from "react-native";

export default function LandingScreen({ navigation }) {
  return (
    <View className="flex-1 items-center justify-center bg-slate-100 px-6">
      <Text className="text-3xl font-bold text-slate-900 mb-3">Refulink</Text>
      <Text className="text-base text-slate-600 mb-10 text-center">
        This is the landing page
      </Text>

      <Pressable
        className="w-full max-w-xs rounded-xl bg-blue-600 py-4 mb-4"
        onPress={() => navigation.navigate("Login")}
      >
        <Text className="text-center text-white text-base font-semibold">
          Login
        </Text>
      </Pressable>

      <Pressable
        className="w-full max-w-xs rounded-xl border border-blue-600 py-4"
        onPress={() => navigation.navigate("Signup")}
      >
        <Text className="text-center text-blue-700 text-base font-semibold">
          Sign Up
        </Text>
      </Pressable>
    </View>
  );
}