import api from "./api";

export const journalService = {
  getJournalEntries(params) {
    return api.get("/journal_entries", { params });
  },
  getJournalEntry(id) {
    return api.get(`/journal_entries/${id}`);
  },
  createJournalEntry(data) {
    return api.post("/journal_entries", data);
  },
  updateJournalEntry(id, data) {
    return api.put(`/journal_entries/${id}`, data);
  },
  deleteJournalEntry(id) {
    return api.delete(`/journal_entries/${id}`);
  },
};

export default journalService;
