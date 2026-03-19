<template>
  <div class="space-y-6">
    <form @submit.prevent="saveBill" class="space-y-6">
      <!-- Main Bill Details -->
      <div class="card grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div class="form-group">
            <label class="form-label">Vendor *</label>
            <select
              v-model="bill.vendor_id"
              required
              class="form-select"
            >
              <option value="" disabled>Select a vendor</option>
              <option v-for="v in vendors" :key="v.id" :value="v.id">
                {{ v.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Bill Number *</label>
            <input
              v-model="bill.bill_number"
              type="text"
              required
              class="form-input"
              placeholder="BILL-0001"
            />
          </div>
        </div>
        <div class="space-y-4">
          <div class="form-group">
            <label class="form-label">Issue Date *</label>
            <input
              v-model="bill.issue_date"
              type="date"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Due Date *</label>
            <input
              v-model="bill.due_date"
              type="date"
              required
              :min="bill.issue_date"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Status</label>
            <div class="p-2 bg-primary/5 rounded font-bold capitalize text-primary text-center">
              {{ bill.status }}
            </div>
          </div>
        </div>
      </div>

      <!-- Bill Lines -->
      <div class="card p-0 overflow-hidden">
        <div class="px-6 py-4 border-b border-divider">
          <h3 class="text-lg font-bold text-on-surface">Bill Lines</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="standard-table">
            <thead>
              <tr>
                <th class="w-48">Product/Service</th>
                <th>Description</th>
                <th>Account</th>
                <th class="w-24">Qty</th>
                <th class="w-32">Unit Cost</th>
                <th class="w-48">Taxes</th>
                <th class="text-right w-32">Total</th>
                <th class="w-16"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(line, index) in bill.lines" :key="index">
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
                    <option v-for="a in expenseAccounts" :key="a.id" :value="a.id">
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
                    v-model.number="line.unit_cost"
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
                  ${{ (line.quantity * line.unit_cost || 0).toFixed(2) }}
                </td>
                <td class="p-2 text-center">
                  <button
                    type="button"
                    @click="removeLine(index)"
                    class="p-2 hover:bg-primary/8 rounded-full text-error"
                    :disabled="bill.lines.length === 1"
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

      <!-- Action Buttons -->
      <div class="flex justify-end gap-4 px-6">
        <button
          type="button"
          @click="$router.push('/bills')"
          class="btn-secondary"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="btn-primary"
        >
          {{ isSubmitting ? 'Saving...' : (isEdit ? 'Update Bill' : 'Create Bill') }}
        </button>
      </div>
    </form>

    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center" v-if="bill.id">
        <button
          v-if="bill.status === 'draft'"
          type="button"
          @click="approveBill"
          :disabled="isSubmitting"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Approve Bill"
        >
          <span class="material-icons text-[20px]">check_circle</span>
          <span class="text-sm font-medium">Approve</span>
        </button>
        <button
          v-if="(bill.status === 'approved' || bill.status === 'overdue') && Number(bill.balance) > 0"
          type="button"
          @click="isPaymentModalOpen = true"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-green-600"
          title="Pay Bill"
        >
          <span class="material-icons text-[20px]">payments</span>
          <span class="text-sm font-medium">Pay</span>
        </button>
      </div>
    </Teleport>

    <VendorPaymentModal
      :is-open="isPaymentModalOpen"
      :bill="bill"
      @close="isPaymentModalOpen = false"
      @saved="handlePaymentSaved"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import billService from '../../services/billService';
import VendorPaymentModal from '../../components/VendorPaymentModal.vue';
import itemService from '../../services/itemService';
import vendorService from '../../services/vendorService';
import accountService from '../../services/accountService';
import taxService from '../../services/taxService';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const isPaymentModalOpen = ref(false);
const isSubmitting = ref(false);
const vendors = ref([]);
const expenseAccounts = ref([]);
const availableTaxes = ref([]);
const availableItems = ref([]);
const defaultTaxRate = ref(0); // Removing its usage below, but keeping the ref for now to avoid errors if I miss any other usage

const bill = reactive({
  vendor_id: '',
  bill_number: '',
  issue_date: new Date().toISOString().split('T')[0],
  due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  status: 'draft',
  lines: [
    {
      item_id: null,
      description: '',
      account_id: '',
      quantity: 1,
      unit_cost: 0,
      tax_ids: [],
    }
  ],
});

const totals = computed(() => {
  let subtotal = 0;
  let totalTax = 0;
  let taxBreakdown = {};

  bill.lines.forEach(line => {
    const lineSubtotal = (line.quantity * line.unit_cost || 0);
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

const fetchVendors = async () => {
  try {
    const response = await vendorService.getVendors({ per_page: 100 });
    vendors.value = response.data.vendors;
  } catch (error) {
    console.error('Failed to fetch vendors:', error);
  }
};

const fetchAccounts = async () => {
  try {
    // Usually expense or asset accounts are used for bills
    const response = await accountService.getAccounts({ per_page: 0 });
    // For simplicity, we filter in the frontend if the API doesn't support it well, 
    // or just show all accounts if appropriate.
    // Based on the invoice example, it uses 'revenue'. For bills, 'expense' is better.
    expenseAccounts.value = response.data.accounts.filter(a => 
      ['expense', 'expenses', 'cost of goods sold', 'asset'].includes(a.type.toLowerCase())
    );
    // If no filtered accounts, just use all
    if (expenseAccounts.value.length === 0) {
      expenseAccounts.value = response.data.accounts;
    }
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
    const response = await itemService.getItems({ per_page: 0, purchaseable: true });
    availableItems.value = response.data.items;
  } catch (error) {
    console.error('Failed to fetch items:', error);
  }
};

const handlePaymentSaved = () => {
  fetchBill();
  isPaymentModalOpen.value = false;
};

const approveBill = async () => {
  if (!bill.id) return;
  try {
    isSubmitting.value = true;
    await billService.updateBill(bill.id, bill);
    await billService.approveBill(bill.id);
    await fetchBill();
  } catch (error) {
    console.error('Failed to approve bill:', error);
    alert('Failed to approve bill: ' + (error.response?.data?.message || error.message));
  } finally {
    isSubmitting.value = false;
  }
};

const fetchBill = async () => {
  if (!isEdit.value) return;
  try {
    const response = await billService.getBill(route.params.id);
    // Map taxes to tax_ids
    if (response.data.lines) {
      response.data.lines.forEach(line => {
        line.tax_ids = line.taxes ? line.taxes.map(t => t.id) : [];
      });
    }
    Object.assign(bill, response.data);
  } catch (error) {
    console.error('Failed to fetch bill:', error);
    alert('Failed to load bill.');
    router.push('/bills');
  }
};

const onItemChange = (line) => {
  if (!line.item_id) return;
  const item = availableItems.value.find(i => i.id === line.item_id);
  if (item) {
    line.description = item.description || item.name;
    line.unit_cost = Number(item.price);
    if (item.expense_account_id) {
      line.account_id = item.expense_account_id;
    }
  }
};

const addLine = () => {
  bill.lines.push({
    item_id: null,
    description: '',
    account_id: expenseAccounts.value.length > 0 ? expenseAccounts.value[0].id : '',
    quantity: 1,
    unit_cost: 0,
    tax_ids: [],
  });
};

const removeLine = (index) => {
  bill.lines.splice(index, 1);
};

const saveBill = async () => {
  // 10.1.4 Frontend form validation
  if (bill.due_date < bill.issue_date) {
    alert('Due date cannot be before issue date.');
    return;
  }
  
  if (bill.lines.some(l => l.quantity <= 0)) {
    alert('All line items must have a quantity greater than zero.');
    return;
  }

  if (bill.lines.some(l => l.unit_cost < 0)) {
    alert('Unit cost cannot be negative.');
    return;
  }

  isSubmitting.value = true;
  try {
    if (isEdit.value) {
      await billService.updateBill(route.params.id, bill);
    } else {
      await billService.createBill(bill);
    }
    router.push('/bills');
  } catch (error) {
    console.error('Failed to save bill:', error);
    const errorMsg = error.response?.data?.msg || 'Failed to save bill. Please check all fields.';
    alert(errorMsg);
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(async () => {
  await Promise.all([
    fetchVendors(),
    fetchAccounts(),
    fetchTaxes(),
    fetchItems()
  ]);
  
  if (isEdit.value) {
    await fetchBill();
  } else if (expenseAccounts.value.length > 0) {
    bill.lines[0].account_id = expenseAccounts.value[0].id;
  }
});
</script>
