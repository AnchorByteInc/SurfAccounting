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
        <label class="form-label">As of Date</label>
        <input v-model="filters.date" type="date" class="form-input">
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
        <h2 class="text-xl font-bold uppercase tracking-widest text-on-surface">Balance Sheet</h2>
        <p class="text-muted">As of {{ filters.date }}</p>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="reportData" class="max-w-3xl mx-auto space-y-12 mb-12">
        <!-- Assets -->
        <section>
          <h3 class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface">Assets</h3>
          
          <div class="space-y-4 px-4">
            <div class="space-y-2">
              <div v-for="item in reportData.assets" :key="item.account_code" class="flex justify-between">
                <span class="text-on-surface">{{ item.account_name }}</span>
                <span class="font-medium text-on-surface">{{ formatCurrency(item.balance) }}</span>
              </div>
            </div>

            <div class="flex justify-between p-4 bg-background rounded-[10px] font-bold text-lg text-on-surface mt-6">
              <span>Total Assets</span>
              <span>{{ formatCurrency(reportData.total_assets) }}</span>
            </div>
          </div>
        </section>

        <!-- Liabilities and Equity -->
        <section>
          <h3 class="text-lg font-bold border-b border-divider pb-2 mb-6 uppercase tracking-wider text-on-surface">Liabilities & Equity</h3>
          
          <div class="space-y-8 px-4">
            <!-- Liabilities -->
            <div>
              <h4 class="font-bold text-muted mb-4 uppercase text-xs tracking-widest">Liabilities</h4>
              <div class="space-y-2 pl-4">
                <div v-for="item in reportData.liabilities" :key="item.account_code" class="flex justify-between">
                  <span class="text-on-surface">{{ item.account_name }}</span>
                  <span class="font-medium text-on-surface">{{ formatCurrency(item.balance) }}</span>
                </div>

                <div class="flex justify-between pt-2 border-t border-divider font-bold text-on-surface mt-4">
                  <span>Total Liabilities</span>
                  <span>{{ formatCurrency(reportData.total_liabilities) }}</span>
                </div>
              </div>
            </div>

            <!-- Equity -->
            <div>
              <h4 class="font-bold text-muted mb-4 uppercase text-xs tracking-widest">Equity</h4>
              <div class="space-y-2 pl-4">
                <div v-for="item in reportData.equity" :key="item.account_code" class="flex justify-between">
                  <span class="text-on-surface">{{ item.account_name }}</span>
                  <span class="font-medium text-on-surface">{{ formatCurrency(item.balance) }}</span>
                </div>
                <div class="flex justify-between pt-2 border-t border-divider font-bold text-on-surface mt-4">
                  <span>Total Equity</span>
                  <span>{{ formatCurrency(reportData.total_equity) }}</span>
                </div>
              </div>
            </div>

            <div class="flex justify-between p-4 bg-background rounded-[10px] font-bold text-lg text-on-surface">
              <span>Total Liabilities & Equity</span>
              <span>{{ formatCurrency(reportData.total_liabilities + reportData.total_equity) }}</span>
            </div>
          </div>
        </section>

        <!-- Balance Check -->
        <div v-if="Math.abs(reportData.total_assets - (reportData.total_liabilities + reportData.total_equity)) > 0.01" class="p-4 bg-error/10 text-error rounded-[10px] text-center font-bold no-print">
          Warning: Balance sheet is not balanced! Difference: {{ formatCurrency(reportData.total_assets - (reportData.total_liabilities + reportData.total_equity)) }}
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
  date: new Date().toISOString().split('T')[0]
})

const fetchReport = async () => {
  loading.value = true
  try {
    const response = await reportService.getBalanceSheet(filters.date)
    reportData.value = response.data
  } catch (error) {
    console.error('Error fetching balance sheet:', error)
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
  reportService.exportToPDF('report-content', `Balance-Sheet-${filters.date}.pdf`)
}

onMounted(() => {
  fetchReport()
})
</script>
