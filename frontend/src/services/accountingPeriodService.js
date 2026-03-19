import api from './api';

export const accountingPeriodService = {
  getAccountingPeriods() {
    return api.get('/accounting_periods');
  },
  createAccountingPeriod(periodData) {
    return api.post('/accounting_periods', periodData);
  },
  closeAccountingPeriod(id) {
    return api.post(`/accounting_periods/${id}/close`);
  },
  deleteAccountingPeriod(id) {
    return api.delete(`/accounting_periods/${id}`);
  }
};
