import api from './api';

export default {
  getInvoices(params) {
    return api.get('/invoices', { params });
  },
  getInvoice(id) {
    return api.get(`/invoices/${id}`);
  },
  createInvoice(data) {
    return api.post('/invoices', data);
  },
  updateInvoice(id, data) {
    return api.put(`/invoices/${id}`, data);
  },
  deleteInvoice(id) {
    return api.delete(`/invoices/${id}`);
  },
  approveInvoice(id) {
    return api.post(`/invoices/${id}/post`);
  },
  // Invoice lines (usually handled within the invoice creation/update, but available)
  getInvoiceLines(params) {
    return api.get('/invoice_lines', { params });
  },
  getInvoiceLine(id) {
    return api.get(`/invoice_lines/${id}`);
  },
  createInvoiceLine(data) {
    return api.post('/invoice_lines', data);
  },
  updateInvoiceLine(id, data) {
    return api.put(`/invoice_lines/${id}`, data);
  },
  deleteInvoiceLine(id) {
    return api.delete(`/invoice_lines/${id}`);
  },
};
