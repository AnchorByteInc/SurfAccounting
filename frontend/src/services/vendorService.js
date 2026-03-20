import api from "./api";

export default {
  getVendors(params) {
    return api.get("/vendors", { params });
  },
  getVendor(id) {
    return api.get(`/vendors/${id}`);
  },
  createVendor(data) {
    return api.post("/vendors", data);
  },
  updateVendor(id, data) {
    return api.put(`/vendors/${id}`, data);
  },
  deleteVendor(id) {
    return api.delete(`/vendors/${id}`);
  },
};
