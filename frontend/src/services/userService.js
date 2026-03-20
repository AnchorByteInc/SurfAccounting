import api from "./api";

export default {
  getUsers() {
    return api.get("/users");
  },
  createUser(data) {
    return api.post("/users", data);
  },
  deleteUser(id) {
    return api.delete(`/users/${id}`);
  },
  forgotPassword(email) {
    return api.post("/auth/forgot-password", { email });
  },
  resetPassword(data) {
    return api.post("/auth/reset-password", data);
  },
};
