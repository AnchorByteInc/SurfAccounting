<template>
  <div class="space-y-6">
    <form @submit.prevent="saveEntry" class="space-y-6">
      <div class="card grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="form-group">
          <label class="form-label">Date</label>
          <input v-model="form.date" type="date" required class="form-input" />
        </div>
        <div class="form-group">
          <label class="form-label">Transaction Type</label>
          <select v-model="form.transaction_type" class="form-select">
            <option value="Journal Entry">Journal Entry</option>
            <option value="Expense">Expense</option>
            <option value="Transfer">Transfer</option>
            <option value="Deposit">Deposit</option>
            <option value="Invoice">Invoice</option>
            <option value="Payment">Payment</option>
            <option value="Credit Card Payment">Credit Card Payment</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Reference</label>
          <input
            v-model="form.reference"
            type="text"
            class="form-input"
            placeholder="Optional ref #"
          />
        </div>
        <div class="form-group">
          <label class="form-label">Memo</label>
          <input
            v-model="form.memo"
            type="text"
            class="form-input"
            placeholder="Global description"
          />
        </div>
      </div>

      <div class="card p-0 overflow-hidden">
        <div class="px-6 py-4 border-b border-divider">
          <h3 class="text-lg font-bold text-on-surface">Journal Lines</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="standard-table">
            <thead>
              <tr>
                <th class="w-1/4">Account</th>
                <th class="w-1/4">Line Description</th>
                <th class="text-right">Debit</th>
                <th class="text-right">Credit</th>
                <th class="text-right"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(line, index) in form.lines" :key="index">
                <td class="p-2">
                  <select
                    v-model="line.account_id"
                    required
                    class="form-select rounded-[10px]"
                  >
                    <option disabled value="">Select an account</option>
                    <option
                      v-for="account in accounts"
                      :key="account.id"
                      :value="account.id"
                    >
                      {{ account.code }} - {{ account.name }}
                    </option>
                  </select>
                </td>
                <td class="p-2">
                  <input
                    v-model="line.description"
                    type="text"
                    class="form-input rounded-[10px]"
                    placeholder="Line details..."
                  />
                </td>
                <td class="p-2">
                  <input
                    v-model.number="line.debit"
                    type="number"
                    step="0.01"
                    min="0"
                    class="form-input rounded-[10px] text-right"
                    placeholder="0.00"
                    @input="clearOpposite(line, 'debit')"
                  />
                </td>
                <td class="p-2">
                  <input
                    v-model.number="line.credit"
                    type="number"
                    step="0.01"
                    min="0"
                    class="form-input rounded-[10px] text-right"
                    placeholder="0.00"
                    @input="clearOpposite(line, 'credit')"
                  />
                </td>
                <td class="p-2 text-right">
                  <button
                    type="button"
                    @click="removeLine(index)"
                    class="p-2 hover:bg-primary/8 rounded-full text-error"
                    :disabled="form.lines.length <= 2"
                    title="Remove"
                  >
                    <span class="material-icons">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-bold border-t border-divider">
                <td
                  class="px-6 py-4 text-right text-muted uppercase text-xs"
                  colspan="2"
                >
                  Totals
                </td>
                <td
                  class="px-6 py-4 text-right"
                  :class="{
                    'text-error': !isBalanced,
                    'text-on-surface': isBalanced,
                  }"
                >
                  {{ formatCurrency(totalDebits) }}
                </td>
                <td
                  class="px-6 py-4 text-right"
                  :class="{
                    'text-error': !isBalanced,
                    'text-on-surface': isBalanced,
                  }"
                >
                  {{ formatCurrency(totalCredits) }}
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="p-6 border-t border-divider">
          <button
            type="button"
            @click="addLine"
            class="h-[40px] px-4 rounded-full text-sm text-primary font-bold hover:bg-primary/8 flex items-center gap-1"
          >
            <span class="material-icons text-[18px]">add</span>
            Add Line
          </button>
        </div>
      </div>

      <div
        v-if="error"
        class="mx-4 p-4 rounded-lg bg-error/10 text-error font-bold text-sm"
      >
        {{ error }}
      </div>

      <div class="flex justify-end gap-4 px-6">
        <button
          type="button"
          @click="router.push('/journals')"
          class="btn-secondary"
        >
          Cancel
        </button>
        <button
          type="submit"
          class="btn-primary"
          :disabled="!isBalanced || loading"
        >
          {{ loading ? "Saving..." : "Save Entry" }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import journalService from "../../services/journalService";
import accountService from "../../services/accountService";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const loading = ref(false);
const error = ref(null);
const accounts = ref([]);

const form = ref({
  date: new Date().toISOString().substr(0, 10),
  transaction_type: "Journal Entry",
  reference: "",
  memo: "",
  lines: [
    { account_id: "", description: "", debit: null, credit: null },
    { account_id: "", description: "", debit: null, credit: null },
  ],
});

const totalDebits = computed(() => {
  return form.value.lines.reduce(
    (sum, line) => sum + (Number(line.debit) || 0),
    0,
  );
});

const totalCredits = computed(() => {
  return form.value.lines.reduce(
    (sum, line) => sum + (Number(line.credit) || 0),
    0,
  );
});

const isBalanced = computed(() => {
  const d = Math.round(totalDebits.value * 100);
  const c = Math.round(totalCredits.value * 100);
  return d === c && d > 0;
});

const fetchAccounts = async () => {
  try {
    const response = await accountService.getAccounts({ per_page: 1000 });
    accounts.value = response.data.accounts;
  } catch (err) {
    console.error("Failed to fetch accounts:", err);
  }
};

const fetchEntry = async () => {
  if (!isEdit.value) return;
  try {
    const response = await journalService.getJournalEntry(route.params.id);
    const data = response.data;
    form.value = {
      date: data.date,
      transaction_type: data.transaction_type || "Journal Entry",
      reference: data.reference || "",
      memo: data.memo || "",
      lines: data.lines.map((line) => ({
        id: line.id,
        account_id: line.account_id,
        description: line.description || "",
        debit: parseFloat(line.debit) || null,
        credit: parseFloat(line.credit) || null,
      })),
    };
  } catch (err) {
    console.error("Failed to fetch entry:", err);
    error.value = "Failed to load journal entry.";
  }
};

const addLine = () => {
  form.value.lines.push({
    account_id: "",
    description: "",
    debit: null,
    credit: null,
  });
};

const removeLine = (index) => {
  form.value.lines.splice(index, 1);
};

const clearOpposite = (line, field) => {
  if (field === "debit" && line.debit > 0) {
    line.credit = null;
  } else if (field === "credit" && line.credit > 0) {
    line.debit = null;
  }
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
};

const saveEntry = async () => {
  if (!isBalanced.value) {
    error.value = "Journal entry must be balanced and have non-zero amounts.";
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const payload = {
      ...form.value,
      lines: form.value.lines.filter(
        (line) => (line.debit || 0) > 0 || (line.credit || 0) > 0,
      ),
    };

    if (isEdit.value) {
      await journalService.updateJournalEntry(route.params.id, payload);
    } else {
      await journalService.createJournalEntry(payload);
    }
    router.push("/journals");
  } catch (err) {
    console.error("Save error:", err);
    error.value =
      err.response?.data?.message || "Failed to save journal entry.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchAccounts();
  fetchEntry();
});
</script>
