<template>
  <div v-if="isOpen" class="modal-backdrop" @click="close">
    <div class="modal-container" @click.stop>
      <form @submit.prevent="submitPayment">
        <div>
          <h2 class="mb-6" id="modal-title">
            Record Payment for Invoice {{ invoice?.invoice_number }}
          </h2>
          <div class="space-y-4">
            <div class="form-group">
              <label class="form-label">Payment Date</label>
              <input
                v-model="payment.date"
                type="date"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label class="form-label">Amount</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface/50">$</span>
                <input
                  v-model.number="payment.amount"
                  type="number"
                  step="0.01"
                  required
                  class="form-input pl-8"
                  :max="invoice?.balance"
                />
              </div>
              <p class="mt-2 text-xs text-muted">Remaining Balance: ${{ Number(invoice?.balance).toFixed(2) }}</p>
            </div>
            <div class="form-group">
              <label class="form-label">Payment Method</label>
              <select
                v-model="payment.method"
                required
                class="form-select"
              >
                <option value="Cash">Cash</option>
                <option value="Check">Check</option>
                <option value="Credit Card">Credit Card</option>
                <option value="Bank Transfer">Bank Transfer</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Deposit To Account</label>
              <select
                v-model="payment.account_id"
                required
                class="form-select"
              >
                <option v-for="a in bankAccounts" :key="a.id" :value="a.id">
                  {{ a.code }} - {{ a.name }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div class="mt-8 flex flex-col sm:flex-row-reverse gap-4">
          <button
            type="submit"
            :disabled="isSubmitting"
            class="btn-primary w-full sm:w-auto"
          >
            {{ isSubmitting ? 'Recording...' : 'Record Payment' }}
          </button>
          <button
            type="button"
            @click="close"
            class="btn-secondary w-full sm:w-auto"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue';
import paymentService from '../services/paymentService';
import accountService from '../services/accountService';

const props = defineProps({
  isOpen: Boolean,
  invoice: Object,
});

const emit = defineEmits(['close', 'saved']);

const isSubmitting = ref(false);
const bankAccounts = ref([]);

const payment = reactive({
  date: new Date().toISOString().split('T')[0],
  amount: 0,
  method: 'Bank Transfer',
  account_id: '',
});

const fetchBankAccounts = async () => {
  try {
    const response = await accountService.getAccounts({ per_page: 100, type: 'payment' });
    bankAccounts.value = response.data.accounts;
    if (bankAccounts.value.length > 0 && !payment.account_id) {
      // Try to find "Cash" or "Bank" as default
      const defaultAcc = bankAccounts.value.find(a => a.name === 'Cash' || a.name === 'Bank') || bankAccounts.value[0];
      payment.account_id = defaultAcc.id;
    }
  } catch (error) {
    console.error('Failed to fetch bank accounts:', error);
  }
};

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.invoice) {
    payment.amount = props.invoice.balance;
    payment.date = new Date().toISOString().split('T')[0];
    fetchBankAccounts();
  }
}, { immediate: true });

const close = () => {
  emit('close');
};

const submitPayment = async () => {
  isSubmitting.value = true;
  try {
    const paymentData = {
      ...payment,
      invoice_id: props.invoice.id,
      customer_id: props.invoice.customer_id,
    };
    await paymentService.createPayment(paymentData);
    emit('saved');
    close();
  } catch (error) {
    console.error('Failed to record payment:', error);
    alert('Failed to record payment.');
  } finally {
    isSubmitting.value = false;
  }
};
</script>
