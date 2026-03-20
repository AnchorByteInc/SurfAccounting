import api from "./api";

export const reportService = {
  getIncomeStatement(startDate, endDate) {
    return api.get(
      `/reports/income-statement?start_date=${startDate}&end_date=${endDate}`,
    );
  },

  getBalanceSheet(asOfDate) {
    const params = asOfDate ? `?as_of_date=${asOfDate}` : "";
    return api.get(`/reports/balance-sheet${params}`);
  },

  getCashFlow(startDate, endDate) {
    return api.get(
      `/reports/cash-flow?start_date=${startDate}&end_date=${endDate}`,
    );
  },

  getARAging(asOfDate) {
    const params = asOfDate ? `?as_of_date=${asOfDate}` : "";
    return api.get(`/reports/ar-aging${params}`);
  },

  getAPAging(asOfDate) {
    const params = asOfDate ? `?as_of_date=${asOfDate}` : "";
    return api.get(`/reports/ap-aging${params}`);
  },

  getIntegrityCheck() {
    return api.get("/reports/integrity-check");
  },

  exportToPDF(elementId, filename) {
    // Simple PDF export using browser print functionality
    // In a real app, this might use libraries like jspdf or html2canvas
    // but for now, we'll trigger the print dialog which allows saving as PDF.
    const originalTitle = document.title;
    document.title = filename;
    window.print();
    document.title = originalTitle;
  },
};
