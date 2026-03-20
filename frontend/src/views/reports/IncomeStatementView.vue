<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center no-print">
        <button
          @click="exportPDF"
          class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8"
          title="Export PDF"
        >
          <span class="material-icons">download</span>
        </button>
      </div>
    </Teleport>

    <!-- Filters -->
    <div class="card flex flex-wrap gap-6 items-end no-print">
      <div class="mb-0">
        <label class="form-label">Start Date</label>
        <input v-model="filters.startDate" type="date" class="form-input" />
      </div>
      <div class="mb-0">
        <label class="form-label">End Date</label>
        <input v-model="filters.endDate" type="date" class="form-input" />
      </div>
      <button @click="fetchReport" class="btn-primary">Run Report</button>
    </div>

    <!-- Report Content -->
    <div id="report-content" class="card p-0 overflow-hidden min-h-[600px]">
      <div class="text-center px-6 pt-12 mb-12">
        <h2 class="text-xl font-bold uppercase tracking-widest text-on-surface">
          Income Statement
        </h2>
        <p class="text-muted">
          {{ filters.startDate }} to {{ filters.endDate }}
        </p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
        ></div>
      </div>

      <div v-else-if="reportData" class="max-w-3xl mx-auto space-y-12 mb-12">
        <!-- Revenue -->
        <section>
          <h3
            class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface"
          >
            Revenue
          </h3>
          <div class="space-y-2 px-4">
            <div
              v-for="item in reportData.revenue"
              :key="item.account_name"
              class="flex justify-between text-on-surface"
            >
              <span>{{ item.account_name }}</span>
              <span class="font-medium">{{
                formatCurrency(item.balance)
              }}</span>
            </div>
            <div
              class="flex justify-between pt-3 border-t border-divider font-bold text-on-surface mt-4"
            >
              <span>Total Revenue</span>
              <span>{{ formatCurrency(reportData.total_revenue) }}</span>
            </div>
          </div>
        </section>

        <!-- Expenses -->
        <section>
          <h3
            class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface"
          >
            Expenses
          </h3>
          <div class="space-y-2 px-4">
            <div
              v-for="item in reportData.expenses"
              :key="item.account_name"
              class="flex justify-between text-on-surface"
            >
              <span>{{ item.account_name }}</span>
              <span class="font-medium">{{
                formatCurrency(item.balance)
              }}</span>
            </div>
            <div
              class="flex justify-between pt-3 border-t border-divider font-bold text-on-surface mt-4"
            >
              <span>Total Expenses</span>
              <span>{{ formatCurrency(reportData.total_expenses) }}</span>
            </div>
          </div>
        </section>

        <!-- Net Income -->
        <div class="pt-6 px-4">
          <div
            class="flex justify-between p-4 bg-background rounded-[10px] font-bold text-lg text-on-surface"
          >
            <span>Net Income</span>
            <span
              :class="
                reportData.net_income >= 0 ? 'text-primary' : 'text-error'
              "
            >
              {{ formatCurrency(reportData.net_income) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from "vue";
import { reportService } from "../../services/reportService";

const loading = ref(true);
const reportData = ref(null);

const filters = reactive({
  startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    .toISOString()
    .split("T")[0],
  endDate: new Date().toISOString().split("T")[0],
});

const fetchReport = async () => {
  loading.value = true;
  try {
    const response = await reportService.getIncomeStatement(
      filters.startDate,
      filters.endDate,
    );
    reportData.value = response.data;
  } catch (error) {
    console.error("Error fetching income statement:", error);
  } finally {
    loading.value = false;
  }
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
};

const exportPDF = () => {
  reportService.exportToPDF(
    "report-content",
    `Income-Statement-${filters.startDate}-to-${filters.endDate}.pdf`,
  );
};

onMounted(() => {
  fetchReport();
});
</script>
