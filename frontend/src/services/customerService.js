import api from "./api";

export default {
  getCustomers(params) {
    return api.get("/customers", { params });
  },
  getCustomer(id) {
    return api.get(`/customers/${id}`);
  },
  createCustomer(data) {
    return api.post("/customers", data);
  },
  updateCustomer(id, data) {
    return api.put(`/customers/${id}`, data);
  },
  deleteCustomer(id) {
    return api.delete(`/customers/${id}`);
  },
};
