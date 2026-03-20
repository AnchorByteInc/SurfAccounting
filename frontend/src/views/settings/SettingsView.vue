<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Business & Branding -->
      <div class="card card-hover flex flex-col">
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary"
          >
            <span class="material-icons">business</span>
          </div>
          <h3 class="m-0">Branding & Business</h3>
        </div>
        <p class="text-sm text-muted mb-6 flex-1">
          Set your business name, address, currency, and company logos.
        </p>
        <RouterLink
          to="/settings/branding"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          Manage Branding
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Chart of Accounts -->
      <div class="card card-hover flex flex-col">
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary"
          >
            <span class="material-icons">account_balance</span>
          </div>
          <h3 class="m-0">Chart of Accounts</h3>
        </div>
        <p class="text-sm text-muted mb-6 flex-1">
          Manage your accounts, their codes, types, and hierarchy.
        </p>
        <RouterLink
          to="/settings/accounts"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          Manage Accounts
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Accounting Periods -->
      <div class="card card-hover flex flex-col">
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary"
          >
            <span class="material-icons">calendar_today</span>
          </div>
          <h3 class="m-0">Accounting Periods</h3>
        </div>
        <p class="text-sm text-muted mb-6 flex-1">
          Open and close accounting periods to lock transactions for specific
          date ranges.
        </p>
        <RouterLink
          to="/settings/accounting-periods"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          Manage Periods
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Taxes -->
      <div class="card card-hover flex flex-col">
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary"
          >
            <span class="material-icons">percent</span>
          </div>
          <h3 class="m-0">Taxes</h3>
        </div>
        <p class="text-sm text-muted mb-6 flex-1">
          Configure tax rates and settings for your sales and purchases.
        </p>
        <RouterLink
          to="/settings/taxes"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          Manage Taxes
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>

      <!-- Users -->
      <div class="card card-hover flex flex-col">
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary"
          >
            <span class="material-icons">people</span>
          </div>
          <h3 class="m-0">Users</h3>
        </div>
        <p class="text-sm text-muted mb-6 flex-1">
          Manage system users, their credentials and access levels.
        </p>
        <RouterLink
          to="/settings/users"
          class="text-primary font-bold hover:opacity-80 flex items-center gap-1 mt-auto"
        >
          Manage Users
          <span class="material-icons text-[18px]">arrow_forward</span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from "vue-router";
</script>
