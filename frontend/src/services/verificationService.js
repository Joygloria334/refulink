import api from "./api";

export const getVouchStatus = async () => {
  const { data } = await api.get("/identity/vouch-status/");
  return data;
};

export const registerIdentity = async (stellarPublicKey) => {
  const { data } = await api.post("/identity/register-identity/", {
    stellar_public_key: stellarPublicKey,
  });
  return data;
};

export const requestVouch = async (ambassadorPublicKey) => {
  const { data } = await api.post("/identity/request-vouch/", {
    ambassador_public_key: ambassadorPublicKey,
  });
  return data;
};
