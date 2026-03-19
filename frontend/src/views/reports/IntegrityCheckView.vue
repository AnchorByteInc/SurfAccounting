<template>
  <div class="space-y-6">
    <div class="flex items-center justify-end px-4 no-print">
      <button
        @click="fetchReport"
        class="btn-primary"
      >
        <span class="material-icons">refresh</span>
        Refresh Checks
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="reportData" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Trial Balance Card -->
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-on-surface">Trial Balance</h3>
          <span :class="reportData.trial_balance.status === 'pass' ? 'bg-green-100 text-green-800' : 'badge-primary'" class="badge">
            {{ reportData.trial_balance.status }}
          </span>
        </div>
        <p class="text-sm text-muted mb-6">Checks if the sum of all debits and credits in the general ledger is zero.</p>
        <div class="flex justify-between items-center pt-4 border-t border-divider">
          <span class="text-sm font-bold text-muted uppercase tracking-widest text-[10px]">Net Balance</span>
          <span :class="reportData.trial_balance.status === 'pass' ? 'text-primary' : 'text-error'" class="font-bold text-lg">
            {{ formatCurrency(reportData.trial_balance.sum) }}
          </span>
        </div>
      </div>

      <!-- Balance Sheet Card -->
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-on-surface">Balance Sheet Equation</h3>
          <span :class="reportData.balance_sheet.status === 'pass' ? 'bg-green-100 text-green-800' : 'badge-primary'" class="badge">
            {{ reportData.balance_sheet.status }}
          </span>
        </div>
        <p class="text-sm text-muted mb-6">Verifies that Assets = Liabilities + Equity.</p>
        <div class="space-y-3 pt-4 border-t border-divider">
          <div class="flex justify-between text-sm">
            <span class="text-muted">Assets</span>
            <span class="text-on-surface font-medium">{{ formatCurrency(reportData.balance_sheet.assets) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-muted">Liabilities + Equity</span>
            <span class="text-on-surface font-medium">{{ formatCurrency(reportData.balance_sheet.liabilities + reportData.balance_sheet.equity) }}</span>
          </div>
          <div class="flex justify-between items-center pt-3 border-t border-divider font-bold">
            <span class="text-sm text-muted uppercase tracking-widest text-[10px]">Difference</span>
            <span :class="reportData.balance_sheet.status === 'pass' ? 'text-primary' : 'text-error'" class="text-lg">
              {{ formatCurrency(reportData.balance_sheet.difference) }}
            </span>
          </div>
        </div>
      </div>

      <!-- AR Subsidiary Ledger Card -->
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-on-surface">A/R Subsidiary Ledger</h3>
          <span :class="reportData.ar_subsidiary.status === 'pass' ? 'bg-green-100 text-green-800' : 'badge-primary'" class="badge">
            {{ reportData.ar_subsidiary.status }}
          </span>
        </div>
        <p class="text-sm text-muted mb-6">Ensures the sum of all customer balances matches the Accounts Receivable GL account.</p>
        <div class="space-y-3 pt-4 border-t border-divider text-sm">
          <div class="flex justify-between">
            <span class="text-muted">Customer Total</span>
            <span class="text-on-surface font-medium">{{ formatCurrency(reportData.ar_subsidiary.customer_total) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted">GL Account Balance</span>
            <span class="text-on-surface font-medium">{{ formatCurrency(reportData.ar_subsidiary.gl_balance) }}</span>
          </div>
        </div>
      </div>

      <!-- AP Subsidiary Ledger Card -->
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-on-surface">A/P Subsidiary Ledger</h3>
          <span :class="reportData.ap_subsidiary.status === 'pass' ? 'bg-green-100 text-green-800' : 'badge-primary'" class="badge">
            {{ reportData.ap_subsidiary.status }}
          </span>
        </div>
        <p class="text-sm text-muted mb-6">Ensures the sum of all vendor balances matches the Accounts Payable GL account.</p>
        <div class="space-y-3 pt-4 border-t border-divider text-sm">
          <div class="flex justify-between">
            <span class="text-muted">Vendor Total</span>
            <span class="text-on-surface font-medium">{{ formatCurrency(reportData.ap_subsidiary.vendor_total) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted">GL Account Balance (Credit)</span>
            <span class="text-on-surface font-medium">{{ formatCurrency(-reportData.ap_subsidiary.gl_balance) }}</span>
          </div>
        </div>
      </div>

      <!-- Journal Entry Integrity Card -->
      <div class="card card-hover md:col-span-2 p-0 overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-bold text-on-surface">Journal Entry Integrity</h3>
            <span :class="reportData.journal_entries.status === 'pass' ? 'bg-green-100 text-green-800' : 'badge-primary'" class="badge">
              {{ reportData.journal_entries.status }}
            </span>
          </div>
          <p class="text-sm text-muted">Checks if any journal entries in the system are currently unbalanced.</p>
        </div>
        
        <div v-if="reportData.journal_entries.unbalanced_count > 0" class="border-t border-divider">
          <h4 class="text-sm font-bold text-error p-6 mb-0">Unbalanced Entries Found: {{ reportData.journal_entries.unbalanced_count }}</h4>
          <div class="overflow-x-auto">
            <table class="standard-table">
              <thead>
                <tr class="uppercase text-[10px] tracking-widest">
                  <th>ID</th>
                  <th>Date</th>
                  <th>Reference</th>
                  <th>Memo</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="je in reportData.journal_entries.unbalanced_details" :key="je.id">
                  <td class="whitespace-nowrap text-muted">{{ je.id }}</td>
                  <td class="whitespace-nowrap text-muted">{{ je.date }}</td>
                  <td class="whitespace-nowrap text-on-surface font-medium">{{ je.reference }}</td>
                  <td class="whitespace-nowrap text-muted">{{ je.memo }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="text-center py-8 text-primary font-bold border-t border-divider">
          <span class="material-icons text-4xl block mb-2">check_circle</span>
          All journal entries are balanced.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportService } from '../../services/reportService'

const loading = ref(true)
const reportData = ref(null)

const fetchReport = async () => {
  loading.value = true
  try {
    const response = await reportService.getIntegrityCheck()
    reportData.value = response.data
  } catch (error) {
    console.error('Error fetching integrity check:', error)
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

onMounted(() => {
  fetchReport()
})
</script>
