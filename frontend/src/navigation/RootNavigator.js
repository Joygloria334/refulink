import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import LandingScreen from "../screens/LandingScreen";
import LoginScreen from "../screens/LoginScreen";
import SignupScreen from "../screens/SignupScreen";
import VerificationDashboard from "../screens/verification/VerificationDashboard";
import WalletDashboard from "../screens/wallet/WalletDashboard";

const Stack = createNativeStackNavigator();

export default function RootNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Landing"
      screenOptions={{
        headerTitleAlign: "center",
        headerStyle: { backgroundColor: "#000" },
        headerTintColor: "#FF6B00",
        headerTitleStyle: { fontWeight: "700" },
      }}
    >
      <Stack.Screen name="Landing" component={LandingScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Signup" component={SignupScreen} />
      <Stack.Screen
        name="VerificationDashboard"
        component={VerificationDashboard}
        options={{ title: "My Verification" }}
      />
      <Stack.Screen
        name="WalletDashboard"
        component={WalletDashboard}
        options={{ title: "Wallet" }}
      />
    </Stack.Navigator>
  );
}
