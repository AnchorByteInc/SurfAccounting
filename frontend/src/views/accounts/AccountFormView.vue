<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <form @submit.prevent="handleSubmit" class="card space-y-6">
      <div class="grid grid-cols-2 gap-6">
        <div class="form-group">
          <label class="form-label">Code *</label>
          <input
            v-model="form.code"
            type="text"
            required
            class="form-input"
            placeholder="e.g. 1000"
          />
          <p v-if="errors.code" class="text-error text-xs mt-2">{{ errors.code[0] || errors.code }}</p>
        </div>
        <div class="form-group">
          <label class="form-label">Name *</label>
          <input
            v-model="form.name"
            type="text"
            required
            class="form-input"
            placeholder="Account name"
          />
          <p v-if="errors.name" class="text-error text-xs mt-2">{{ errors.name[0] || errors.name }}</p>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-6">
        <div class="form-group">
          <label class="form-label">Type *</label>
          <select
            v-model="form.type"
            required
            class="form-select"
          >
            <option value="" disabled>Select Type</option>
            <option v-for="type in accountTypes" :key="type" :value="type">{{ type }}</option>
          </select>
          <p v-if="errors.type" class="text-error text-xs mt-2">{{ errors.type[0] || errors.type }}</p>
        </div>
        <div class="form-group">
          <label class="form-label">Subtype</label>
          <input
            v-model="form.subtype"
            type="text"
            class="form-input"
            placeholder="e.g. Bank, Accounts Receivable"
          />
          <p v-if="errors.subtype" class="text-error text-xs mt-2">{{ errors.subtype[0] || errors.subtype }}</p>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Parent Account</label>
        <select
          v-model="form.parent_id"
          class="form-select"
        >
          <option :value="null">None (Root)</option>
          <option v-for="acc in availableParents" :key="acc.id" :value="acc.id">
            {{ acc.code }} - {{ acc.name }}
          </option>
        </select>
        <p v-if="errors.parent_id" class="text-error text-xs mt-2">{{ errors.parent_id[0] || errors.parent_id }}</p>
      </div>

      <div class="flex items-center space-x-8">
        <div class="flex items-center space-x-3">
          <label class="switch">
            <input type="checkbox" v-model="form.is_active" />
            <span class="slider"></span>
          </label>
          <span class="form-label mb-0">Active</span>
        </div>
        <div class="flex items-center space-x-3">
          <label class="switch">
            <input type="checkbox" v-model="form.is_system" />
            <span class="slider"></span>
          </label>
          <span class="form-label mb-0">System Account</span>
        </div>
      </div>

      <div class="pt-6 border-t border-divider flex justify-end">
        <button
          type="submit"
          :disabled="submitting"
          class="btn-primary"
        >
          {{ submitting ? 'Saving...' : 'Save Account' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import accountService from '../../services/accountService';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const submitting = ref(false);
const errors = ref({});
const accounts = ref([]);

const accountTypes = [
  "Asset",
  "Liability",
  "Equity",
  "Revenue",
  "Expense",
];

const form = ref({
  code: '',
  name: '',
  type: '',
  subtype: '',
  parent_id: null,
  is_active: true,
  is_system: false,
});

const fetchAccounts = async () => {
  try {
    const response = await accountService.getAccounts({ per_page: 1000 });
    accounts.value = response.data.accounts;
  } catch (error) {
    console.error('Failed to fetch accounts:', error);
  }
};

const availableParents = computed(() => {
  if (!isEdit.value) return accounts.value;
  // Prevent selecting itself or its children as parent (simplified: just prevent itself)
  return accounts.value.filter(acc => acc.id !== parseInt(route.params.id));
});

const fetchAccount = async () => {
  if (!isEdit.value) return;
  try {
    const response = await accountService.getAccount(route.params.id);
    const { code, name, type, subtype, parent_id, is_active, is_system } = response.data;
    form.value = {
      code,
      name,
      type,
      subtype: subtype || '',
      parent_id: parent_id || null,
      is_active,
      is_system: is_system || false,
    };
  } catch (error) {
    console.error('Failed to fetch account:', error);
    alert('Failed to load account data.');
    router.push('/settings/accounts');
  }
};

const handleSubmit = async () => {
  submitting.value = true;
  errors.value = {};
  
  // Create a copy of form to send
  const payload = { ...form.value };
  
  try {
    if (isEdit.value) {
      await accountService.updateAccount(route.params.id, payload);
    } else {
      await accountService.createAccount(payload);
    }
    router.push('/settings/accounts');
  } catch (error) {
    if (error.response && error.response.status === 400) {
      errors.value = error.response.data;
      if (typeof errors.value === 'string') {
        alert(errors.value);
      }
    } else {
      console.error('Failed to save account:', error);
      alert('An error occurred while saving.');
    }
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchAccounts();
  fetchAccount();
});
</script>
