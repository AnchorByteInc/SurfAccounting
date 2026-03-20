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

    <!-- Report Content -->
    <div id="report-content" class="card p-0 overflow-hidden min-h-[600px]">
      <div class="text-center px-6 pt-12 mb-12">
        <h2 class="text-xl font-bold uppercase tracking-widest text-on-surface">
          Accounts Receivable Aging
        </h2>
        <p class="text-muted">As of {{ today }}</p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
        ></div>
      </div>

      <div v-else-if="reportData" class="overflow-x-auto">
        <table class="standard-table">
          <thead>
            <tr class="uppercase text-[10px] tracking-widest">
              <th>Customer</th>
              <th class="text-right">Current</th>
              <th class="text-right">1-30 Days</th>
              <th class="text-right">31-60 Days</th>
              <th class="text-right">61-90 Days</th>
              <th class="text-right">Over 90 Days</th>
              <th class="text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in reportData.by_customer" :key="row.customer_name">
              <td class="whitespace-nowrap font-medium text-on-surface">
                {{ row.customer_name }}
              </td>
              <td class="whitespace-nowrap text-right text-on-surface">
                {{ formatCurrency(row.current) }}
              </td>
              <td class="whitespace-nowrap text-right text-on-surface">
                {{ formatCurrency(row["1-30"]) }}
              </td>
              <td class="whitespace-nowrap text-right text-on-surface">
                {{ formatCurrency(row["31-60"]) }}
              </td>
              <td class="whitespace-nowrap text-right text-on-surface">
                {{ formatCurrency(row["61-90"]) }}
              </td>
              <td class="whitespace-nowrap text-right text-on-surface">
                {{ formatCurrency(row["90+"]) }}
              </td>
              <td
                class="whitespace-nowrap text-right font-bold text-on-surface"
              >
                {{ formatCurrency(row.total) }}
              </td>
            </tr>
          </tbody>
          <tfoot class="font-bold bg-background">
            <tr>
              <td class="px-4 py-4 text-on-surface">Total</td>
              <td class="px-4 py-4 text-right text-on-surface">
                {{ formatCurrency(reportData.summary.current) }}
              </td>
              <td class="px-4 py-4 text-right text-on-surface">
                {{ formatCurrency(reportData.summary["1-30"]) }}
              </td>
              <td class="px-4 py-4 text-right text-on-surface">
                {{ formatCurrency(reportData.summary["31-60"]) }}
              </td>
              <td class="px-4 py-4 text-right text-on-surface">
                {{ formatCurrency(reportData.summary["61-90"]) }}
              </td>
              <td class="px-4 py-4 text-right text-on-surface">
                {{ formatCurrency(reportData.summary["90+"]) }}
              </td>
              <td class="px-4 py-4 text-right text-on-surface">
                {{ formatCurrency(reportData.summary.total) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { reportService } from "../../services/reportService";

const loading = ref(true);
const reportData = ref(null);
const today = new Date().toISOString().split("T")[0];

const fetchReport = async () => {
  loading.value = true;
  try {
    const response = await reportService.getARAging();
    reportData.value = response.data;
  } catch (error) {
    console.error("Error fetching A/R aging:", error);
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
  reportService.exportToPDF("report-content", `AR-Aging-${today}.pdf`);
};

onMounted(() => {
  fetchReport();
});
</script>
