<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/journals/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="New Journal Entry"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">New Journal Entry</span>
        </button>
        <div class="relative">
          <button
            @click.stop="toggleMoreMenu"
            class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8 text-primary"
            title="More Options"
          >
            <span class="material-icons">more_vert</span>
          </button>
          <div
            v-if="showMoreMenu"
            class="absolute right-0 mt-1 w-48 bg-white rounded-[14px] shadow-lg border border-gray-100 py-1 z-50"
          >
            <button
              @click="
                showImportModal = true;
                showMoreMenu = false;
              "
              class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-primary/5 flex items-center gap-2"
            >
              <span class="material-icons text-[18px]">upload_file</span>
              Bulk Import
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <BulkImportModal
      :is-open="showImportModal"
      title="Bulk Import Journal Entries"
      upload-url="/journal_entries/bulk-import"
      :template-fields="[
        'date',
        'transaction_type',
        'reference',
        'memo',
        'account_code',
        'debit',
        'credit',
        'description',
        'source_module',
        'source_id',
        'vendor_id',
        'customer_id',
      ]"
      @close="showImportModal = false"
      @success="fetchEntries"
    />

    <!-- Filters -->
    <div class="card flex flex-wrap gap-6">
      <div class="mb-0">
        <label class="form-label">Reference</label>
        <input
          v-model="filters.reference"
          type="text"
          class="form-input"
          placeholder="Search reference..."
        />
      </div>
      <div class="mb-0">
        <label class="form-label">Memo</label>
        <input
          v-model="filters.memo"
          type="text"
          class="form-input"
          placeholder="Search memo..."
        />
      </div>
      <div class="mb-0">
        <label class="form-label">Start Date</label>
        <input v-model="filters.start_date" type="date" class="form-input" />
      </div>
      <div class="mb-0">
        <label class="form-label">End Date</label>
        <input v-model="filters.end_date" type="date" class="form-input" />
      </div>
      <div class="flex items-end">
        <button @click="fetchEntries" class="btn-secondary">Filter</button>
      </div>
    </div>

    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Reference</th>
            <th>Memo</th>
            <th class="text-right">Total Amount</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in entries"
            :key="entry.id"
            @click="editEntry(entry.id)"
            class="cursor-pointer hover:bg-primary/8"
          >
            <td class="whitespace-nowrap text-muted">{{ entry.date }}</td>
            <td class="whitespace-nowrap text-muted">
              <span
                class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/5 text-primary"
              >
                {{ entry.transaction_type || "Journal Entry" }}
              </span>
            </td>
            <td class="whitespace-nowrap font-medium text-on-surface">
              {{ entry.reference }}
            </td>
            <td class="whitespace-nowrap text-muted truncate max-w-xs">
              {{ entry.memo }}
            </td>
            <td class="whitespace-nowrap font-bold text-on-surface text-right">
              {{ formatCurrency(calculateTotal(entry)) }}
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <RouterLink
                  :to="`/journals/${entry.id}/edit`"
                  @click.stop
                  class="p-2 hover:bg-primary/8 rounded-full text-primary"
                  title="Edit"
                >
                  <span class="material-icons text-[20px]">edit</span>
                </RouterLink>
                <button
                  @click.stop="confirmDelete(entry.id)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="entries.length === 0">
            <td colspan="6" class="px-6 py-10 text-center text-muted">
              No journal entries found.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div
        v-if="pagination.pages > 1"
        class="px-6 py-4 flex items-center justify-between border-t border-divider"
      >
        <div class="flex-1 flex justify-between sm:hidden">
          <button
            @click="prevPage"
            :disabled="pagination.current_page === 1"
            class="btn-secondary py-1 px-4"
          >
            Previous
          </button>
          <button
            @click="nextPage"
            :disabled="pagination.current_page === pagination.pages"
            class="btn-secondary py-1 px-4"
          >
            Next
          </button>
        </div>
        <div
          class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between"
        >
          <div>
            <p class="text-sm text-muted">
              Showing
              <span class="font-bold text-on-surface">{{
                (pagination.current_page - 1) * pagination.per_page + 1
              }}</span>
              to
              <span class="font-bold text-on-surface">{{
                Math.min(
                  pagination.current_page * pagination.per_page,
                  pagination.total,
                )
              }}</span>
              of
              <span class="font-bold text-on-surface">{{
                pagination.total
              }}</span>
              results
            </p>
          </div>
          <div>
            <nav class="flex gap-2" aria-label="Pagination">
              <button
                v-for="page in pagination.pages"
                :key="page"
                @click="changePage(page)"
                class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold transition-colors"
                :class="
                  page === pagination.current_page
                    ? 'bg-primary text-white'
                    : 'text-muted hover:bg-primary/8'
                "
              >
                {{ page }}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import journalService from "../../services/journalService";
import BulkImportModal from "../../components/BulkImportModal.vue";

const router = useRouter();

const entries = ref([]);
const showImportModal = ref(false);
const showMoreMenu = ref(false);

const toggleMoreMenu = () => {
  showMoreMenu.value = !showMoreMenu.value;
};

const closeMoreMenu = () => {
  showMoreMenu.value = false;
};
const filters = ref({
  reference: "",
  memo: "",
  start_date: "",
  end_date: "",
});
const pagination = ref({
  total: 0,
  pages: 0,
  current_page: 1,
  per_page: 10,
});

const editEntry = (id) => {
  router.push(`/journals/${id}/edit`);
};

const fetchEntries = async () => {
  try {
    const params = {
      ...filters.value,
      page: pagination.value.current_page,
      per_page: pagination.value.per_page,
    };
    const response = await journalService.getJournalEntries(params);
    entries.value = response.data.journal_entries;
    pagination.value.total = response.data.total;
    pagination.value.pages = response.data.pages;
    pagination.value.current_page = response.data.current_page;
  } catch (error) {
    console.error("Failed to fetch journal entries:", error);
  }
};

const calculateTotal = (entry) => {
  if (!entry.lines) return 0;
  return entry.lines.reduce(
    (sum, line) => sum + parseFloat(line.debit || 0),
    0,
  );
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
};

const confirmDelete = async (id) => {
  if (confirm("Are you sure you want to delete this journal entry?")) {
    try {
      await journalService.deleteJournalEntry(id);
      fetchEntries();
    } catch (error) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.msg ||
        "Failed to delete journal entry. It might be linked to other transactions or in a closed period.";
      alert(message);
      console.error("Delete error:", error);
    }
  }
};

const changePage = (page) => {
  pagination.value.current_page = page;
  fetchEntries();
};

const prevPage = () => {
  if (pagination.value.current_page > 1) {
    pagination.value.current_page--;
    fetchEntries();
  }
};

const nextPage = () => {
  if (pagination.value.current_page < pagination.value.pages) {
    pagination.value.current_page++;
    fetchEntries();
  }
};

onMounted(() => {
  fetchEntries();
  window.addEventListener("click", closeMoreMenu);
});

onUnmounted(() => {
  window.removeEventListener("click", closeMoreMenu);
});
</script>
