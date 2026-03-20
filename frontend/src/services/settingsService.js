import api from "./api";

export default {
  getSettingsList(params) {
    return api.get("/settings", { params });
  },
  getSettings(id) {
    return api.get(`/settings/${id}`);
  },
  createSettings(data) {
    return api.post("/settings", data);
  },
  updateSettings(id, data) {
    return api.put(`/settings/${id}`, data);
  },
  deleteSettings(id) {
    return api.delete(`/settings/${id}`);
  },
  uploadLogo(formData) {
    return api.post("/settings/upload-logo", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};
