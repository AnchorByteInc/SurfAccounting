<template>
  <div class="max-w-2xl mx-auto">
    <div class="card">
      <form @submit.prevent="saveTax" class="space-y-4">
        <div>
          <label class="form-label">Tax Name</label>
          <input
            v-model="tax.name"
            type="text"
            required
            placeholder="e.g. GST, VAT"
            class="form-input"
          />
        </div>

        <div>
          <label class="form-label">Rate (%)</label>
          <input
            v-model="taxRatePercent"
            type="number"
            step="0.01"
            required
            placeholder="e.g. 7.00"
            class="form-input"
          />
          <p class="text-xs text-muted mt-1">Enter the percentage value. 7% should be entered as 7.</p>
        </div>

        <div>
          <label class="form-label">Description</label>
          <textarea
            v-model="tax.description"
            rows="3"
            placeholder="Optional description"
            class="form-input"
          ></textarea>
        </div>

        <div class="flex items-center gap-2">
          <input
            v-model="tax.is_active"
            type="checkbox"
            id="is_active"
            class="w-4 h-4 text-primary rounded border-divider focus:ring-primary"
          />
          <label for="is_active" class="form-label mb-0">Active</label>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="form-label">Asset Account (for billing)</label>
            <select v-model="tax.asset_account_id" class="form-input">
              <option :value="null">None (Use Default)</option>
              <option v-for="acc in assetAccounts" :key="acc.id" :value="acc.id">
                {{ acc.code }} - {{ acc.name }}
              </option>
            </select>
            <p class="text-xs text-muted mt-1">GL account for recoverable tax from vendor bills.</p>
          </div>

          <div>
            <label class="form-label">Liability Account (for invoicing)</label>
            <select v-model="tax.liability_account_id" class="form-input">
              <option :value="null">None (Use Default)</option>
              <option v-for="acc in liabilityAccounts" :key="acc.id" :value="acc.id">
                {{ acc.code }} - {{ acc.name }}
              </option>
            </select>
            <p class="text-xs text-muted mt-1">GL account for tax payable from customer invoices.</p>
          </div>
        </div>

        <div class="pt-4 flex justify-end gap-3">
          <button
            type="button"
            @click="router.back()"
            class="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="submitting"
            class="btn-primary"
          >
            {{ submitting ? 'Saving...' : 'Save Tax' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import taxService from '../../services/taxService';
import accountService from '../../services/accountService';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const submitting = ref(false);
const accounts = ref([]);

const assetAccounts = computed(() => accounts.value.filter(a => a.type === 'Asset'));
const liabilityAccounts = computed(() => accounts.value.filter(a => a.type === 'Liability'));

const tax = ref({
  name: '',
  rate: 0,
  description: '',
  is_active: true,
  asset_account_id: null,
  liability_account_id: null
});

const taxRatePercent = computed({
  get: () => (tax.value.rate * 100).toFixed(2),
  set: (val) => {
    tax.value.rate = parseFloat(val) / 100;
  }
});

const fetchTax = async () => {
  if (!isEdit.value) return;
  try {
    const response = await taxService.getTax(route.params.id);
    tax.value = response.data;
  } catch (error) {
    console.error('Failed to fetch tax:', error);
    alert('Failed to load tax data.');
  }
};

const saveTax = async () => {
  submitting.value = true;
  try {
    if (isEdit.value) {
      await taxService.updateTax(route.params.id, tax.value);
    } else {
      await taxService.createTax(tax.value);
    }
    router.push('/settings/taxes');
  } catch (error) {
    console.error('Failed to save tax:', error);
    const msg = error.response?.data?.message || 'Failed to save tax.';
    alert(msg);
  } finally {
    submitting.value = false;
  }
};

const fetchAccounts = async () => {
  try {
    const response = await accountService.getAccounts({ per_page: 1000 });
    accounts.value = response.data.accounts;
  } catch (error) {
    console.error('Failed to fetch accounts:', error);
  }
};

onMounted(() => {
  fetchTax();
  fetchAccounts();
});
</script>
