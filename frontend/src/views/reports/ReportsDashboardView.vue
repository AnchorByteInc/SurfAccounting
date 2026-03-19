<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Income Statement -->
      <div class="card card-hover flex flex-col">
        <h3 class="mb-2">Income Statement</h3>
        <p class="text-sm text-muted mb-6 flex-1">
          Shows your revenues, expenses, and net profit over a specific period.
        </p>
        <RouterLink
          to="/reports/income-statement"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          View Report
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Balance Sheet -->
      <div class="card card-hover flex flex-col">
        <h3 class="mb-2">Balance Sheet</h3>
        <p class="text-sm text-muted mb-6 flex-1">
          A snapshot of your assets, liabilities, and equity at a specific point in time.
        </p>
        <RouterLink
          to="/reports/balance-sheet"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          View Report
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Cash Flow -->
      <div class="card card-hover flex flex-col">
        <h3 class="mb-2">Statement of Cash Flows</h3>
        <p class="text-sm text-muted mb-6 flex-1">
          Shows how changes in balance sheet and income affect cash and cash equivalents.
        </p>
        <RouterLink
          to="/reports/cash-flow"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          View Report
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- A/R Aging -->
      <div class="card card-hover flex flex-col">
        <h3 class="mb-2">Accounts Receivable Aging</h3>
        <p class="text-sm text-muted mb-6 flex-1">
          Summarizes your unpaid customer invoices by how long they have been outstanding.
        </p>
        <RouterLink
          to="/reports/ar-aging"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          View Report
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- A/P Aging -->
      <div class="card card-hover flex flex-col">
        <h3 class="mb-2">Accounts Payable Aging</h3>
        <p class="text-sm text-muted mb-6 flex-1">
          Summarizes your unpaid bills from vendors by how long they have been outstanding.
        </p>
        <RouterLink
          to="/reports/ap-aging"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          View Report
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Balance Verification -->
      <div class="card card-hover flex flex-col">
        <h3 class="mb-2">Balance Verification</h3>
        <p class="text-sm text-muted mb-6 flex-1">
          Perform accounting integrity checks to ensure your books are in balance.
        </p>
        <RouterLink
          to="/reports/integrity-check"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          View Dashboard
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
