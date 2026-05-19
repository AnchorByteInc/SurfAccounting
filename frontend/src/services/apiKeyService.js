import api from "./api";

export default {
  getApiKeys() {
    return api.get("/api-keys");
  },
  createApiKey(data) {
    return api.post("/api-keys", data);
  },
  revokeApiKey(id) {
    return api.delete(`/api-keys/${id}`);
  },
};
