<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <form @submit.prevent="handleSubmit" class="card space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="form-group md:col-span-2">
          <label class="form-label">Name *</label>
          <input
            v-model="form.name"
            type="text"
            required
            class="form-input"
            placeholder="Product or service name"
          />
          <p v-if="errors.name" class="text-error text-xs mt-1">{{ errors.name[0] }}</p>
        </div>

        <div class="form-group md:col-span-2">
          <label class="form-label">Description</label>
          <textarea
            v-model="form.description"
            rows="2"
            class="form-input"
            placeholder="Optional description"
          ></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">Default Price / Rate</label>
          <input
            v-model="form.price"
            type="number"
            step="0.01"
            class="form-input font-bold"
            placeholder="0.00"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4 border-t border-divider">
        <!-- Sellable Section -->
        <div class="space-y-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="form.sellable" class="form-checkbox" />
            <span class="font-bold">I sell this product/service</span>
          </label>
          
          <div v-if="form.sellable" class="space-y-4 pl-7">
            <div class="form-group">
              <label class="form-label">Income Account</label>
              <select v-model="form.income_account_id" class="form-input" required>
                <option :value="null">Select an account</option>
                <option v-for="acc in revenueAccounts" :key="acc.id" :value="acc.id">
                  {{ acc.code }} - {{ acc.name }}
                </option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">Sales Taxes</label>
              <div class="grid grid-cols-1 gap-2">
                <label v-for="tax in taxes" :key="tax.id" class="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    :value="tax.id" 
                    v-model="form.sales_tax_ids" 
                    class="form-checkbox"
                  />
                  <span class="text-sm">{{ tax.name }} ({{ (tax.rate * 100).toFixed(1) }}%)</span>
                </label>
              </div>
              <p v-if="taxes.length === 0" class="text-xs text-muted">No taxes defined.</p>
            </div>
          </div>
        </div>

        <!-- Purchaseable Section -->
        <div class="space-y-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="form.purchaseable" class="form-checkbox" />
            <span class="font-bold">I purchase this product/service</span>
          </label>
          
          <div v-if="form.purchaseable" class="space-y-4 pl-7">
            <div class="form-group">
              <label class="form-label">Expense Account</label>
              <select v-model="form.expense_account_id" class="form-input" required>
                <option :value="null">Select an account</option>
                <option v-for="acc in expenseAccounts" :key="acc.id" :value="acc.id">
                  {{ acc.code }} - {{ acc.name }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="pt-6 border-t border-divider flex justify-end gap-3">
        <button type="button" @click="router.push('/items')" class="btn-secondary">Cancel</button>
        <button
          type="submit"
          :disabled="submitting"
          class="btn-primary"
        >
          {{ submitting ? 'Saving...' : (isEdit ? 'Update Item' : 'Create Item') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import itemService from '../../services/itemService';
import accountService from '../../services/accountService';
import taxService from '../../services/taxService';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const submitting = ref(false);
const errors = ref({});

const accounts = ref([]);
const taxes = ref([]);

const revenueAccounts = computed(() => accounts.value.filter(a => 
  ['revenue', 'income'].includes(a.type.toLowerCase())
));
const expenseAccounts = computed(() => accounts.value.filter(a => 
  ['expense', 'expenses', 'cost of goods sold'].includes(a.type.toLowerCase())
));

const form = ref({
  name: '',
  description: '',
  price: 0,
  sellable: true,
  income_account_id: null,
  purchaseable: false,
  expense_account_id: null,
  sales_tax_ids: [],
});

const fetchData = async () => {
  try {
    const [accRes, taxRes] = await Promise.all([
      accountService.getAccounts({ per_page: 0 }),
      taxService.getTaxes({ per_page: 0, is_active: true })
    ]);
    accounts.value = accRes.data.accounts;
    taxes.value = taxRes.data.taxes;

    if (isEdit.value) {
      const itemRes = await itemService.getItem(route.params.id);
      const data = itemRes.data;
      form.value = {
        name: data.name,
        description: data.description || '',
        price: data.price,
        sellable: data.sellable,
        income_account_id: data.income_account_id,
        purchaseable: data.purchaseable,
        expense_account_id: data.expense_account_id,
        sales_tax_ids: data.sales_taxes ? data.sales_taxes.map(t => t.id) : [],
      };
    }
  } catch (error) {
    console.error('Failed to fetch data:', error);
    alert('Failed to load item data.');
  }
};

const handleSubmit = async () => {
  submitting.value = true;
  errors.value = {};
  
  // Clean up data based on checkboxes
  const payload = { ...form.value };
  if (!payload.sellable) {
    payload.income_account_id = null;
    payload.sales_tax_ids = [];
  }
  if (!payload.purchaseable) {
    payload.expense_account_id = null;
  }

  try {
    if (isEdit.value) {
      await itemService.updateItem(route.params.id, payload);
    } else {
      await itemService.createItem(payload);
    }
    router.push('/items');
  } catch (error) {
    if (error.response && error.response.status === 400) {
      errors.value = error.response.data;
    } else {
      console.error('Failed to save item:', error);
      alert('An error occurred while saving.');
    }
  } finally {
    submitting.value = false;
  }
};

onMounted(fetchData);
</script>
