import api from './api';

export default {
  getPayments(params) {
    return api.get('/payments', { params });
  },
  getPayment(id) {
    return api.get(`/payments/${id}`);
  },
  createPayment(data) {
    return api.post('/payments', data);
  },
  updatePayment(id, data) {
    return api.put(`/payments/${id}`, data);
  },
  deletePayment(id) {
    return api.delete(`/payments/${id}`);
  },
  // Vendor payments
  getVendorPayments(params) {
    return api.get('/vendor_payments', { params });
  },
  getVendorPayment(id) {
    return api.get(`/vendor_payments/${id}`);
  },
  createVendorPayment(data) {
    return api.post('/vendor_payments', data);
  },
  updateVendorPayment(id, data) {
    return api.put(`/vendor_payments/${id}`, data);
  },
  deleteVendorPayment(id) {
    return api.delete(`/vendor_payments/${id}`);
  },
};
