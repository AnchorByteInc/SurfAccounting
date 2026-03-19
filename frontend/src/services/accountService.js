import api from './api';

export default {
  getAccounts(params) {
    return api.get('/accounts', { params });
  },
  getAccount(id) {
    return api.get(`/accounts/${id}`);
  },
  createAccount(data) {
    return api.post('/accounts', data);
  },
  updateAccount(id, data) {
    return api.put(`/accounts/${id}`, data);
  },
  deleteAccount(id) {
    return api.delete(`/accounts/${id}`);
  },
};
