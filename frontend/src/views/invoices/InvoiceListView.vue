<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/invoices/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="New Invoice"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">New Invoice</span>
        </button>
      </div>
    </Teleport>

    <!-- Filters -->
    <div class="card grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="mb-0">
        <label class="form-label">Invoice Number</label>
        <input
          v-model="filters.invoice_number"
          @input="handleFilter"
          type="text"
          placeholder="INV-..."
          class="form-input"
        />
      </div>
      <div class="mb-0">
        <label class="form-label">Status</label>
        <select
          v-model="filters.status"
          @change="handleFilter"
          class="form-select"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="approved">Approved</option>
          <option value="sent">Sent</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div class="mb-0">
        <label class="form-label">From Date</label>
        <input
          v-model="filters.start_date"
          @input="handleFilter"
          type="date"
          class="form-input"
        />
      </div>
      <div class="mb-0">
        <label class="form-label">To Date</label>
        <input
          v-model="filters.end_date"
          @input="handleFilter"
          type="date"
          class="form-input"
        />
      </div>
    </div>

    <!-- Table -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Number</th>
            <th>Customer</th>
            <th>Date</th>
            <th>Due Date</th>
            <th class="text-right">Total</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="invoice in invoices"
            :key="invoice.id"
            @click="editInvoice(invoice.id)"
            class="cursor-pointer hover:bg-primary/8"
          >
            <td class="whitespace-nowrap font-medium text-on-surface">
              {{ invoice.invoice_number }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ invoice.customer ? invoice.customer.name : "N/A" }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ invoice.issue_date }}
            </td>
            <td class="whitespace-nowrap text-muted">{{ invoice.due_date }}</td>
            <td class="whitespace-nowrap font-bold text-right">
              ${{ Number(invoice.total).toFixed(2) }}
            </td>
            <td class="whitespace-nowrap">
              <span
                :class="[
                  'badge',
                  statusBadgeClasses[invoice.status] ||
                    'bg-gray-100 text-gray-800',
                ]"
              >
                {{ invoice.status }}
              </span>
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <button
                  v-if="invoice.balance > 0"
                  @click.stop="openPaymentModal(invoice)"
                  class="p-2 hover:bg-primary/8 rounded-full text-green-600"
                  title="Record Payment"
                >
                  <span class="material-icons text-[20px]">payments</span>
                </button>
                <RouterLink
                  :to="`/invoices/${invoice.id}/edit`"
                  @click.stop
                  class="p-2 hover:bg-primary/8 rounded-full text-primary"
                  title="Edit"
                >
                  <span class="material-icons text-[20px]">edit</span>
                </RouterLink>
                <RouterLink
                  :to="`/invoices/${invoice.id}/print`"
                  @click.stop
                  class="p-2 hover:bg-primary/8 rounded-full"
                  title="Print"
                >
                  <span class="material-icons text-[20px]">print</span>
                </RouterLink>
                <button
                  @click.stop="confirmDelete(invoice)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="invoices.length === 0">
            <td colspan="7" class="px-6 py-10 text-center text-muted">
              No invoices found.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="px-6 py-4 flex items-center justify-between border-t border-divider"
      >
        <div class="flex-1 flex justify-between sm:hidden">
          <button
            @click="changePage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="btn-secondary py-1 px-4"
          >
            Previous
          </button>
          <button
            @click="changePage(currentPage + 1)"
            :disabled="currentPage === totalPages"
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
              Showing page
              <span class="font-bold text-on-surface">{{ currentPage }}</span>
              of <span class="font-bold text-on-surface">{{ totalPages }}</span>
            </p>
          </div>
          <div>
            <nav class="flex gap-2" aria-label="Pagination">
              <button
                v-for="p in totalPages"
                :key="p"
                @click="changePage(p)"
                class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold transition-colors"
                :class="
                  p === currentPage
                    ? 'bg-primary text-white'
                    : 'text-muted hover:bg-primary/8'
                "
              >
                {{ p }}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
    <PaymentModal
      :is-open="isPaymentModalOpen"
      :invoice="selectedInvoice"
      @close="isPaymentModalOpen = false"
      @saved="fetchInvoices"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import invoiceService from "../../services/invoiceService";
import PaymentModal from "../../components/PaymentModal.vue";

const invoices = ref([]);
const currentPage = ref(1);
const totalPages = ref(1);
const filters = reactive({
  invoice_number: "",
  status: "",
  start_date: "",
  end_date: "",
});

const isPaymentModalOpen = ref(false);
const selectedInvoice = ref(null);

const router = useRouter();

const openPaymentModal = (invoice) => {
  selectedInvoice.value = invoice;
  isPaymentModalOpen.value = true;
};

const statusBadgeClasses = {
  draft: "bg-gray-100 text-gray-800",
  approved: "badge-primary",
  sent: "badge-primary",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
  cancelled: "bg-gray-400 text-white",
};

const fetchInvoices = async () => {
  try {
    const response = await invoiceService.getInvoices({
      page: currentPage.value,
      per_page: 10,
      ...filters,
    });
    invoices.value = response.data.invoices;
    totalPages.value = response.data.pages;
    currentPage.value = response.data.current_page;
  } catch (error) {
    console.error("Failed to fetch invoices:", error);
  }
};

const editInvoice = (id) => {
  router.push(`/invoices/${id}/edit`);
};

const handleFilter = () => {
  currentPage.value = 1;
  fetchInvoices();
};

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchInvoices();
};

const confirmDelete = async (invoice) => {
  if (
    confirm(
      `Are you sure you want to delete invoice "${invoice.invoice_number}"?`,
    )
  ) {
    try {
      await invoiceService.deleteInvoice(invoice.id);
      fetchInvoices();
    } catch (error) {
      console.error("Failed to delete invoice:", error);
      const message =
        error.response?.data?.message ||
        error.response?.data?.msg ||
        "Failed to delete invoice.";
      alert(message);
    }
  }
};

onMounted(() => {
  fetchInvoices();
});
</script>
