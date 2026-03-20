import api from "./api";

export default {
  getBills(params) {
    return api.get("/bills", { params });
  },
  getBill(id) {
    return api.get(`/bills/${id}`);
  },
  createBill(data) {
    return api.post("/bills", data);
  },
  updateBill(id, data) {
    return api.put(`/bills/${id}`, data);
  },
  deleteBill(id) {
    return api.delete(`/bills/${id}`);
  },
  approveBill(id) {
    return api.post(`/bills/${id}/post`);
  },
  // Bill lines
  getBillLines(params) {
    return api.get("/bill_lines", { params });
  },
  getBillLine(id) {
    return api.get(`/bill_lines/${id}`);
  },
  createBillLine(data) {
    return api.post("/bill_lines", data);
  },
  updateBillLine(id, data) {
    return api.put(`/bill_lines/${id}`, data);
  },
  deleteBillLine(id) {
    return api.delete(`/bill_lines/${id}`);
  },
  // Vendor Payments
  getVendorPayments(params) {
    return api.get("/vendor_payments", { params });
  },
  createVendorPayment(data) {
    return api.post("/vendor_payments", data);
  },
};
