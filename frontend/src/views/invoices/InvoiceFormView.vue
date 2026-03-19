<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div v-if="isEdit && (invoice.status === 'draft' || (['approved', 'sent', 'overdue'].includes(invoice.status) && Number(invoice.balance) > 0))" class="pill-nav flex items-center gap-2">
        <button
          v-if="invoice.status === 'draft'"
          @click="approveInvoice"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Approve Invoice"
        >
          <span class="material-icons text-[20px]">check_circle</span>
          <span class="text-sm font-medium">Approve</span>
        </button>

        <button
          v-if="['approved', 'sent', 'overdue'].includes(invoice.status) && Number(invoice.balance) > 0"
          @click="isPaymentModalOpen = true"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-green-600/8 gap-2 text-green-600"
          title="Record Payment"
        >
          <span class="material-icons text-[20px]">payments</span>
          <span class="text-sm font-medium">Pay</span>
        </button>
      </div>

      <div class="pill-nav flex items-center">
        <button
          @click="saveInvoice"
          :disabled="isSubmitting"
          class="h-[40px] w-[40px] flex items-center justify-center rounded-full hover:bg-primary/8 text-primary"
          :title="isEdit ? 'Update Invoice' : 'Create Invoice'"
        >
          <span class="material-icons text-[20px]">save</span>
        </button>

        <template v-if="isEdit">
          <RouterLink
            :to="`/invoices/${invoice.id}/print`"
            class="h-[40px] w-[40px] flex items-center justify-center rounded-full hover:bg-primary/8 text-primary"
            title="Print"
          >
            <span class="material-icons text-[20px]">print</span>
          </RouterLink>

          <div v-if="invoice.status !== 'cancelled' && invoice.status !== 'paid'" class="relative">
            <button
              @click.stop="toggleMoreMenu"
              class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8 text-primary"
              title="More Options"
            >
              <span class="material-icons">more_vert</span>
            </button>
            <div 
              v-if="showMoreMenu"
              class="absolute right-0 mt-2 w-48 bg-white rounded-[14px] shadow-lg border border-gray-100 py-1 z-50 overflow-hidden"
              @click.stop
            >
              <button 
                v-if="invoice.status !== 'cancelled' && invoice.status !== 'paid'"
                @click="cancelInvoice(); showMoreMenu = false"
                class="w-full text-left px-4 py-2 text-sm text-error hover:bg-error/5 flex items-center gap-2 transition-colors"
              >
                <span class="material-icons text-[18px]">cancel</span>
                Cancel Invoice
              </button>
              <button 
                v-if="invoice.status === 'draft'"
                @click="confirmDelete(); showMoreMenu = false"
                class="w-full text-left px-4 py-2 text-sm text-error hover:bg-error/5 flex items-center gap-2 transition-colors"
              >
                <span class="material-icons text-[18px]">delete</span>
                Delete Invoice
              </button>
            </div>
          </div>
        </template>
      </div>
    </Teleport>

    <form @submit.prevent="saveInvoice" class="space-y-6">
      <!-- Main Invoice Details -->
      <div class="card grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div class="form-group">
            <label class="form-label">Customer *</label>
            <select
              v-model="invoice.customer_id"
              required
              class="form-select"
            >
              <option value="" disabled>Select a customer</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">
                {{ c.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Invoice Number (Auto-generated if empty)</label>
            <input
              v-model="invoice.invoice_number"
              type="text"
              class="form-input"
              placeholder="e.g. INV-0001"
            />
          </div>
        </div>
        <div class="space-y-4">
          <div class="form-group">
            <label class="form-label">Issue Date *</label>
            <input
              v-model="invoice.issue_date"
              type="date"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Due Date *</label>
            <input
              v-model="invoice.due_date"
              type="date"
              required
              :min="invoice.issue_date"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Status</label>
            <div class="py-2">
              <span :class="['badge', statusBadgeClasses[invoice.status] || 'bg-gray-100 text-gray-800']">
                {{ invoice.status }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Invoice Lines -->
      <div class="card p-0 overflow-hidden">
        <div class="px-6 py-4 border-b border-divider">
          <h3 class="text-lg font-bold text-on-surface">Invoice Lines</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="standard-table">
            <thead>
              <tr>
                <th class="w-48">Product/Service</th>
                <th>Description</th>
                <th>Account</th>
                <th class="w-24">Qty</th>
                <th class="w-32">Price</th>
                <th class="w-48">Taxes</th>
                <th class="text-right w-32">Total</th>
                <th class="w-16"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(line, index) in invoice.lines" :key="index">
                <td class="p-2">
                  <select
                    v-model="line.item_id"
                    @change="onItemChange(line)"
                    class="form-select rounded-[10px]"
                  >
                    <option :value="null">-- Select --</option>
                    <option v-for="item in availableItems" :key="item.id" :value="item.id">
                      {{ item.name }}
                    </option>
                  </select>
                </td>
                <td class="p-2">
                  <input
                    v-model="line.description"
                    type="text"
                    required
                    class="form-input rounded-[10px]"
                  />
                </td>
                <td class="p-2">
                  <select
                    v-model="line.account_id"
                    required
                    class="form-select rounded-[10px]"
                  >
                    <option v-for="a in revenueAccounts" :key="a.id" :value="a.id">
                      {{ a.code }} - {{ a.name }}
                    </option>
                  </select>
                </td>
                <td class="p-2">
                  <input
                    v-model.number="line.quantity"
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    class="form-input rounded-[10px]"
                  />
                </td>
                <td class="p-2">
                  <input
                    v-model.number="line.unit_price"
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    class="form-input rounded-[10px]"
                  />
                </td>
                <td class="p-2">
                  <div class="flex flex-wrap gap-x-3 gap-y-1">
                    <label v-for="tax in availableTaxes" :key="tax.id" class="inline-flex items-center text-xs cursor-pointer hover:bg-primary/8 p-1 rounded">
                      <input
                        type="checkbox"
                        :value="tax.id"
                        v-model="line.tax_ids"
                        class="w-3 h-3 rounded text-primary focus:ring-primary mr-1"
                      />
                      {{ tax.name }}
                    </label>
                  </div>
                  <div v-if="availableTaxes.length === 0" class="text-xs text-muted italic">
                    No taxes defined
                  </div>
                </td>
                <td class="px-6 py-2 text-right font-bold text-on-surface">
                  ${{ (line.quantity * line.unit_price).toFixed(2) }}
                </td>
                <td class="p-2 text-center">
                  <button
                    type="button"
                    @click="removeLine(index)"
                    class="p-2 hover:bg-primary/8 rounded-full text-error"
                    :disabled="invoice.lines.length === 1"
                    title="Remove"
                  >
                    <span class="material-icons">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="p-6 border-t border-divider">
          <button
            type="button"
            @click="addLine"
            class="h-[40px] px-4 rounded-full text-sm text-primary font-bold hover:bg-primary/8 flex items-center gap-1"
          >
            <span class="material-icons text-[18px]">add</span>
            Add Line Item
          </button>
        </div>
      </div>

      <!-- Totals -->
      <div class="flex justify-end px-6">
        <div class="w-full md:w-64 space-y-3">
          <div class="flex justify-between text-sm">
            <span class="text-muted">Subtotal</span>
            <span class="font-bold text-on-surface">${{ totals.subtotal.toFixed(2) }}</span>
          </div>
          <template v-if="Object.keys(totals.taxBreakdown).length > 1">
            <div v-for="(amount, name) in totals.taxBreakdown" :key="name" class="flex justify-between text-sm">
              <span class="text-muted">{{ name }}</span>
              <span class="font-bold text-on-surface">${{ amount.toFixed(2) }}</span>
            </div>
          </template>
          <div v-else class="flex justify-between text-sm">
            <span class="text-muted">Tax</span>
            <span class="font-bold text-on-surface">${{ totals.tax.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between text-lg font-bold border-t border-divider pt-3 text-on-surface">
            <span>Total</span>
            <span>${{ totals.total.toFixed(2) }}</span>
          </div>
        </div>
      </div>

    </form>
    <PaymentModal
      :is-open="isPaymentModalOpen"
      :invoice="invoice"
      @close="isPaymentModalOpen = false"
      @saved="fetchInvoice"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import invoiceService from '../../services/invoiceService';
import itemService from '../../services/itemService';
import customerService from '../../services/customerService';
import accountService from '../../services/accountService';
import taxService from '../../services/taxService';
import PaymentModal from '../../components/PaymentModal.vue';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const isSubmitting = ref(false);
const customers = ref([]);
const revenueAccounts = ref([]);
const availableTaxes = ref([]);
const availableItems = ref([]);
const isPaymentModalOpen = ref(false);
const showMoreMenu = ref(false);

const statusBadgeClasses = {
  'draft': 'bg-gray-100 text-gray-800',
  'approved': 'badge-primary',
  'sent': 'badge-primary',
  'paid': 'bg-green-100 text-green-800',
  'overdue': 'bg-red-100 text-red-800',
  'cancelled': 'bg-gray-400 text-white',
};

const invoice = reactive({
  customer_id: '',
  invoice_number: '',
  issue_date: new Date().toISOString().split('T')[0],
  due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  status: 'draft',
  lines: [
    {
      item_id: null,
      description: '',
      account_id: '',
      quantity: 1,
      unit_price: 0,
      tax_ids: [],
    }
  ],
});

const totals = computed(() => {
  let subtotal = 0;
  let totalTax = 0;
  let taxBreakdown = {};

  invoice.lines.forEach(line => {
    const lineSubtotal = (line.quantity * line.unit_price || 0);
    subtotal += lineSubtotal;

    if (line.tax_ids && line.tax_ids.length > 0) {
      line.tax_ids.forEach(taxId => {
        const tax = availableTaxes.value.find(t => t.id === taxId);
        if (tax) {
          const taxAmount = lineSubtotal * Number(tax.rate);
          totalTax += taxAmount;

          if (taxBreakdown[tax.name]) {
            taxBreakdown[tax.name] += taxAmount;
          } else {
            taxBreakdown[tax.name] = taxAmount;
          }
        }
      });
    }
  });

  return {
    subtotal,
    tax: totalTax,
    taxBreakdown,
    total: subtotal + totalTax,
  };
});

const fetchCustomers = async () => {
  try {
    const response = await customerService.getCustomers({ per_page: 100 });
    customers.value = response.data.customers;
  } catch (error) {
    console.error('Failed to fetch customers:', error);
  }
};

const fetchAccounts = async () => {
  try {
    const response = await accountService.getAccounts({ per_page: 100, type: 'revenue' });
    revenueAccounts.value = response.data.accounts;
  } catch (error) {
    console.error('Failed to fetch accounts:', error);
  }
};

const fetchTaxes = async () => {
  try {
    const response = await taxService.getTaxes({ per_page: 0, is_active: true });
    availableTaxes.value = response.data.taxes;
  } catch (error) {
    console.error('Failed to fetch taxes:', error);
  }
};

const fetchItems = async () => {
  try {
    const response = await itemService.getItems({ per_page: 0, sellable: true });
    availableItems.value = response.data.items;
  } catch (error) {
    console.error('Failed to fetch items:', error);
  }
};

const fetchInvoice = async () => {
  if (!isEdit.value) return;
  try {
    const response = await invoiceService.getInvoice(route.params.id);
    // Map taxes to tax_ids
    if (response.data.lines) {
      response.data.lines.forEach(line => {
        line.tax_ids = line.taxes ? line.taxes.map(t => t.id) : [];
      });
    }
    Object.assign(invoice, response.data);
  } catch (error) {
    console.error('Failed to fetch invoice:', error);
    alert('Failed to load invoice.');
    router.push('/invoices');
  }
};

const onItemChange = (line) => {
  if (!line.item_id) return;
  const item = availableItems.value.find(i => i.id === line.item_id);
  if (item) {
    line.description = item.description || item.name;
    line.unit_price = Number(item.price);
    if (item.income_account_id) {
      line.account_id = item.income_account_id;
    }
    if (item.sales_taxes && item.sales_taxes.length > 0) {
      line.tax_ids = item.sales_taxes.map(t => t.id);
    }
  }
};

const addLine = () => {
  invoice.lines.push({
    item_id: null,
    description: '',
    account_id: revenueAccounts.value.length > 0 ? revenueAccounts.value[0].id : '',
    quantity: 1,
    unit_price: 0,
    tax_ids: [],
  });
};

const removeLine = (index) => {
  invoice.lines.splice(index, 1);
};

const approveInvoice = async () => {
  if (!isEdit.value) return;
  if (!confirm('Are you sure you want to approve this invoice? This will post it to the General Ledger.')) return;
  
  isSubmitting.value = true;
  try {
    await invoiceService.approveInvoice(route.params.id);
    await fetchInvoice();
  } catch (error) {
    console.error('Failed to approve invoice:', error);
    alert(error.response?.data?.message || 'Failed to approve invoice.');
  } finally {
    isSubmitting.value = false;
  }
};

const cancelInvoice = async () => {
  if (!isEdit.value) return;
  if (!confirm('Are you sure you want to cancel this invoice? This cannot be undone.')) return;
  
  isSubmitting.value = true;
  try {
    await invoiceService.updateInvoice(route.params.id, { status: 'cancelled' });
    await fetchInvoice();
  } catch (error) {
    console.error('Failed to cancel invoice:', error);
    alert('Failed to cancel invoice.');
  } finally {
    isSubmitting.value = false;
  }
};

const confirmDelete = async () => {
  if (!isEdit.value) return;
  if (!confirm(`Are you sure you want to delete invoice "${invoice.invoice_number}"?`)) return;
  
  isSubmitting.value = true;
  try {
    await invoiceService.deleteInvoice(route.params.id);
    router.push('/invoices');
  } catch (error) {
    console.error('Failed to delete invoice:', error);
    alert('Failed to delete invoice.');
  } finally {
    isSubmitting.value = false;
  }
};

const saveInvoice = async () => {
  // 10.1.4 Frontend form validation
  if (invoice.due_date < invoice.issue_date) {
    alert('Due date cannot be before issue date.');
    return;
  }
  
  if (invoice.lines.some(l => l.quantity <= 0)) {
    alert('All line items must have a quantity greater than zero.');
    return;
  }

  if (invoice.lines.some(l => l.unit_price < 0)) {
    alert('Unit price cannot be negative.');
    return;
  }

  isSubmitting.value = true;
  try {
    if (isEdit.value) {
      await invoiceService.updateInvoice(route.params.id, invoice);
    } else {
      await invoiceService.createInvoice(invoice);
    }
    router.push('/invoices');
  } catch (error) {
    console.error('Failed to save invoice:', error);
    const errorMsg = error.response?.data?.msg || 'Failed to save invoice. Please check all fields.';
    alert(errorMsg);
  } finally {
    isSubmitting.value = false;
  }
};

const toggleMoreMenu = () => {
  showMoreMenu.value = !showMoreMenu.value;
};

const closeMoreMenu = () => {
  showMoreMenu.value = false;
};

onMounted(async () => {
  window.addEventListener('click', closeMoreMenu);
  await Promise.all([
    fetchCustomers(),
    fetchAccounts(),
    fetchTaxes(),
    fetchItems()
  ]);
  
  if (isEdit.value) {
    await fetchInvoice();
  } else if (revenueAccounts.value.length > 0) {
    invoice.lines[0].account_id = revenueAccounts.value[0].id;
  }
});

onUnmounted(() => {
  window.removeEventListener('click', closeMoreMenu);
});
</script>
