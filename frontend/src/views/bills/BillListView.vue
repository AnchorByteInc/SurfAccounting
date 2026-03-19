<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/bills/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="New Bill"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">New Bill</span>
        </button>
      </div>
    </Teleport>

    <!-- Filters -->
    <div class="card grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="mb-0">
        <label class="form-label">Bill Number</label>
        <input
          v-model="filters.bill_number"
          @input="handleFilter"
          type="text"
          placeholder="BILL-..."
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
            <th>Vendor</th>
            <th>Date</th>
            <th>Due Date</th>
            <th class="text-right">Total</th>
            <th class="text-right">Balance</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="bill in bills" 
            :key="bill.id"
            @click="editBill(bill.id)"
            class="cursor-pointer hover:bg-primary/8"
          >
            <td class="whitespace-nowrap font-medium text-on-surface">{{ bill.bill_number }}</td>
            <td class="whitespace-nowrap text-muted">{{ bill.vendor ? bill.vendor.name : 'N/A' }}</td>
            <td class="whitespace-nowrap text-muted">{{ bill.issue_date }}</td>
            <td class="whitespace-nowrap text-muted">{{ bill.due_date }}</td>
            <td class="whitespace-nowrap font-bold text-right text-on-surface">${{ Number(bill.total).toFixed(2) }}</td>
            <td class="whitespace-nowrap font-bold text-right text-on-surface">${{ Number(bill.balance).toFixed(2) }}</td>
            <td class="whitespace-nowrap">
              <span
                :class="[
                  'badge',
                  statusBadgeClasses[bill.status] || 'bg-gray-100 text-gray-800'
                ]"
              >
                {{ bill.status }}
              </span>
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <button
                  v-if="bill.status !== 'draft' && Number(bill.balance) > 0"
                  @click.stop="openPaymentModal(bill)"
                  class="p-2 hover:bg-primary/8 rounded-full text-green-600"
                  title="Pay"
                >
                  <span class="material-icons text-[20px]">payments</span>
                </button>
                <RouterLink
                  :to="`/bills/${bill.id}/edit`"
                  @click.stop
                  class="p-2 hover:bg-primary/8 rounded-full text-primary"
                  title="Edit"
                >
                  <span class="material-icons text-[20px]">edit</span>
                </RouterLink>
                <button
                  @click.stop="confirmDelete(bill)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="bills.length === 0">
            <td colspan="8" class="px-6 py-10 text-center text-muted">
              No bills found.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="px-6 py-4 flex items-center justify-between border-t border-divider">
        <div class="flex-1 flex justify-between sm:hidden">
          <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1" class="btn-secondary py-1 px-4">Previous</button>
          <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages" class="btn-secondary py-1 px-4">Next</button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-muted">
              Showing page <span class="font-bold text-on-surface">{{ currentPage }}</span> of <span class="font-bold text-on-surface">{{ totalPages }}</span>
            </p>
          </div>
          <div>
            <nav class="flex gap-2" aria-label="Pagination">
              <button
                v-for="p in totalPages"
                :key="p"
                @click="changePage(p)"
                class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold transition-colors"
                :class="p === currentPage ? 'bg-primary text-white' : 'text-muted hover:bg-primary/8'"
              >
                {{ p }}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
    <VendorPaymentModal
      :is-open="isPaymentModalOpen"
      :bill="selectedBill"
      @close="isPaymentModalOpen = false"
      @saved="fetchBills"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import billService from '../../services/billService';
import VendorPaymentModal from '../../components/VendorPaymentModal.vue';

const bills = ref([]);
const currentPage = ref(1);
const totalPages = ref(1);
const filters = reactive({
  bill_number: '',
  status: '',
  start_date: '',
  end_date: '',
});

const router = useRouter();

const isPaymentModalOpen = ref(false);
const selectedBill = ref(null);

const openPaymentModal = (bill) => {
  selectedBill.value = bill;
  isPaymentModalOpen.value = true;
};

const statusBadgeClasses = {
  'draft': 'bg-gray-100 text-gray-800',
  'approved': 'bg-blue-100 text-blue-800',
  'paid': 'bg-green-100 text-green-800',
  'overdue': 'badge-primary',
  'cancelled': 'btn-error text-[10px] px-2 py-1',
};

const fetchBills = async () => {
  try {
    const response = await billService.getBills({
      page: currentPage.value,
      per_page: 10,
      ...filters
    });
    bills.value = response.data.bills;
    totalPages.value = response.data.pages;
    currentPage.value = response.data.current_page;
  } catch (error) {
    console.error('Failed to fetch bills:', error);
  }
};

const editBill = (id) => {
  router.push(`/bills/${id}/edit`);
};

const handleFilter = () => {
  currentPage.value = 1;
  fetchBills();
};

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchBills();
};

const confirmDelete = async (bill) => {
  if (confirm(`Are you sure you want to delete bill "${bill.bill_number}"?`)) {
    try {
      await billService.deleteBill(bill.id);
      fetchBills();
    } catch (error) {
      console.error('Failed to delete bill:', error);
      const message = error.response?.data?.message || error.response?.data?.msg || 'Failed to delete bill.';
      alert(message);
    }
  }
};

onMounted(() => {
  fetchBills();
});
</script>
