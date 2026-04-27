import api from "./api";

export const getBalance = async () => {
  const { data } = await api.get("/wallet/balance/");
  return data; // { kes_balance: float, stellar_address: string }
};

export const getTransactions = async (limit = 20) => {
  const { data } = await api.get("/wallet/transactions/", { params: { limit } });
  return data.transactions; // array of transaction objects
};
