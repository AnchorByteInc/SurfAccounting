import { defineStore } from "pinia";
import api from "../services/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token: localStorage.getItem("token") || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(username, password) {
      try {
        const response = await api.post("/auth/login", { username, password });
        const { access_token, user } = response.data;
        this.setUser(user, access_token);
      } catch (error) {
        throw error;
      }
    },
    setUser(user, token) {
      this.user = user;
      this.token = token;
      localStorage.setItem("token", token);
    },
    logout() {
      this.user = null;
      this.token = null;
      localStorage.removeItem("token");
    },
  },
});
