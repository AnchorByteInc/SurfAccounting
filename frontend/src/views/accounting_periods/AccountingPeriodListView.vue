<template>
  <div class="space-y-6">
    <!-- Create New Period Form -->
    <div class="card">
      <h3 class="mb-4">Create New Period</h3>
      <form
        @submit.prevent="handleCreate"
        class="grid grid-cols-1 md:grid-cols-4 gap-6 items-end"
      >
        <div class="mb-0">
          <label class="form-label">Name</label>
          <input
            v-model="newPeriod.name"
            type="text"
            placeholder="e.g. FY 2026 Q1"
            required
            class="form-input"
          />
        </div>
        <div class="mb-0">
          <label class="form-label">Start Date</label>
          <input
            v-model="newPeriod.start_date"
            type="date"
            required
            class="form-input"
          />
        </div>
        <div class="mb-0">
          <label class="form-label">End Date</label>
          <input
            v-model="newPeriod.end_date"
            type="date"
            required
            class="form-input"
          />
        </div>
        <div class="mb-0">
          <button type="submit" :disabled="loading" class="btn-primary w-full">
            {{ loading ? "Creating..." : "Create Period" }}
          </button>
        </div>
      </form>
    </div>

    <!-- List of Periods -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="period in periods" :key="period.id">
            <td class="whitespace-nowrap font-medium text-on-surface">
              {{ period.name }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ formatDate(period.start_date) }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ formatDate(period.end_date) }}
            </td>
            <td class="whitespace-nowrap">
              <span
                class="badge"
                :class="
                  period.is_closed ? 'btn-error' : 'bg-green-100 text-green-800'
                "
              >
                {{ period.is_closed ? "Closed" : "Open" }}
              </span>
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <button
                  v-if="!period.is_closed"
                  @click="handleClose(period.id)"
                  class="p-2 hover:bg-primary/8 rounded-full text-secondary"
                  title="Close Period"
                >
                  <span class="material-icons text-[20px]">lock</span>
                </button>
                <button
                  v-if="!period.is_closed"
                  @click="handleDelete(period.id)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="periods.length === 0">
            <td colspan="5" class="px-6 py-10 text-center text-muted">
              No accounting periods found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { accountingPeriodService } from "../../services/accountingPeriodService";

const periods = ref([]);
const loading = ref(false);
const newPeriod = ref({
  name: "",
  start_date: "",
  end_date: "",
});

const fetchPeriods = async () => {
  try {
    const response = await accountingPeriodService.getAccountingPeriods();
    periods.value = response.data;
  } catch (error) {
    console.error("Failed to fetch periods:", error);
  }
};

const handleCreate = async () => {
  loading.value = true;
  try {
    await accountingPeriodService.createAccountingPeriod(newPeriod.value);
    newPeriod.value = { name: "", start_date: "", end_date: "" };
    await fetchPeriods();
  } catch (error) {
    console.error("Failed to create period:", error);
    alert(
      "Error creating period: " +
        (error.response?.data?.message || error.message),
    );
  } finally {
    loading.value = false;
  }
};

const handleClose = async (id) => {
  if (
    !confirm(
      "Are you sure you want to close this accounting period? This will lock all transactions within its date range.",
    )
  ) {
    return;
  }
  try {
    await accountingPeriodService.closeAccountingPeriod(id);
    await fetchPeriods();
  } catch (error) {
    console.error("Failed to close period:", error);
    const message =
      error.response?.data?.message ||
      error.response?.data?.msg ||
      "Failed to close period.";
    alert(message);
  }
};

const handleDelete = async (id) => {
  if (!confirm("Are you sure you want to delete this accounting period?")) {
    return;
  }
  try {
    await accountingPeriodService.deleteAccountingPeriod(id);
    await fetchPeriods();
  } catch (error) {
    console.error("Failed to delete period:", error);
    const message =
      error.response?.data?.message ||
      error.response?.data?.msg ||
      "Failed to delete period.";
    alert(message);
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "";
  return new Date(dateString).toLocaleDateString();
};

onMounted(() => {
  fetchPeriods();
});
</script>
