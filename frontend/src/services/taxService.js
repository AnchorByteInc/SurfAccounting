import api from "./api";

export default {
  getTaxes(params) {
    return api.get("/taxes", { params });
  },
  getTax(id) {
    return api.get(`/taxes/${id}`);
  },
  createTax(data) {
    return api.post("/taxes", data);
  },
  updateTax(id, data) {
    return api.put(`/taxes/${id}`, data);
  },
  deleteTax(id) {
    return api.delete(`/taxes/${id}`);
  },
};
