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
        <input v-model="filters.startDate" type="date" class="form-input">
      </div>
      <div class="mb-0">
        <label class="form-label">End Date</label>
        <input v-model="filters.endDate" type="date" class="form-input">
      </div>
      <button
        @click="fetchReport"
        class="btn-primary"
      >
        Run Report
      </button>
    </div>

    <!-- Report Content -->
    <div id="report-content" class="card p-0 overflow-hidden min-h-[600px]">
      <div class="text-center px-6 pt-12 mb-12">
        <h2 class="text-xl font-bold uppercase tracking-widest text-on-surface">Statement of Cash Flows</h2>
        <p class="text-muted">{{ filters.startDate }} to {{ filters.endDate }}</p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="reportData" class="max-w-3xl mx-auto space-y-12 mb-12">
        <!-- Operating Activities -->
        <section>
          <h3 class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface">Cash flow from Operating Activities</h3>
          <div class="space-y-3 px-4 text-on-surface">
            <div class="flex justify-between">
              <span>Net Income</span>
              <span class="font-medium">{{ formatCurrency(reportData.net_income) }}</span>
            </div>
            <div class="flex justify-between">
              <span>Adjustments: Change in Accounts Receivable</span>
              <span class="font-medium">{{ formatCurrency(reportData.change_in_ar) }}</span>
            </div>
            <div v-for="item in reportData.ar_breakdown" :key="item.id" class="flex justify-between pl-6 text-sm italic text-muted">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.change) }}</span>
            </div>

            <div class="flex justify-between">
              <span>Adjustments: Change in Accounts Payable</span>
              <span class="font-medium">{{ formatCurrency(reportData.change_in_ap) }}</span>
            </div>
            <div v-for="item in reportData.ap_breakdown" :key="item.id" class="flex justify-between pl-6 text-sm italic text-muted">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.change) }}</span>
            </div>
            <div v-if="reportData.change_in_amort !== 0" class="flex justify-between">
              <span>Adjustments: Amortization</span>
              <span class="font-medium">{{ formatCurrency(reportData.change_in_amort) }}</span>
            </div>
            <div class="flex justify-between pt-3 border-t border-divider font-bold mt-4">
              <span>Net cash provided by Operating Activities</span>
              <span>{{ formatCurrency(reportData.net_operating_cash) }}</span>
            </div>
          </div>
        </section>

        <!-- Investing Activities -->
        <section v-if="reportData.net_investing_cash !== 0">
          <h3 class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface">Cash flow from Investing Activities</h3>
          <div class="space-y-3 px-4 text-on-surface">
            <div class="flex justify-between">
              <span>Net cash from Investing Activities</span>
              <span class="font-medium">{{ formatCurrency(reportData.net_investing_cash) }}</span>
            </div>
          </div>
        </section>

        <!-- Financing Activities -->
        <section v-if="reportData.net_financing_cash !== 0">
          <h3 class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface">Cash flow from Financing Activities</h3>
          <div class="space-y-3 px-4 text-on-surface">
            <div v-for="item in reportData.financing_breakdown" :key="item.id" class="flex justify-between pl-6 text-sm italic text-muted">
              <span>{{ item.name }}</span>
              <span>{{ formatCurrency(item.change) }}</span>
            </div>
            <div class="flex justify-between pt-3 border-t border-divider font-bold">
              <span>Net cash from Financing Activities</span>
              <span class="font-medium">{{ formatCurrency(reportData.net_financing_cash) }}</span>
            </div>
          </div>
        </section>

        <!-- Summary -->
        <div class="pt-6 space-y-4 px-4">
          <div class="flex justify-between border-t border-divider pt-4 font-bold text-on-surface">
            <span>Net increase (decrease) in cash and cash equivalents</span>
            <span>{{ formatCurrency(reportData.net_change_in_cash) }}</span>
          </div>
          <div class="flex justify-between text-muted italic">
            <span>Cash and cash equivalents at beginning of period</span>
            <span>{{ formatCurrency(reportData.starting_cash) }}</span>
          </div>
          <div class="flex justify-between p-4 bg-background rounded-[10px] font-bold text-lg text-on-surface">
            <span>Cash and cash equivalents at end of period</span>
            <span>{{ formatCurrency(reportData.ending_cash) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { reportService } from '../../services/reportService'

const loading = ref(true)
const reportData = ref(null)

const filters = reactive({
  startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
  endDate: new Date().toISOString().split('T')[0]
})

const fetchReport = async () => {
  loading.value = true
  try {
    const response = await reportService.getCashFlow(filters.startDate, filters.endDate)
    reportData.value = response.data
  } catch (error) {
    console.error('Error fetching cash flow:', error)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value)
}

const exportPDF = () => {
  reportService.exportToPDF('report-content', `Cash-Flow-${filters.startDate}-to-${filters.endDate}.pdf`)
}

onMounted(() => {
  fetchReport()
})
</script>
