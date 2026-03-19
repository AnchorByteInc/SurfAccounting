<template>
  <div class="space-y-6">
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="error" class="mx-4 p-4 rounded-lg bg-error/10 text-error font-bold" role="alert">
      <p>Error: {{ error }}</p>
    </div>

    <div v-else class="space-y-10">
      <!-- Dashboard UI cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="card card-hover">
          <p class="text-[10px] font-bold text-muted uppercase tracking-widest mb-2">Monthly Revenue</p>
          <p class="text-2xl font-bold text-primary">${{ formatCurrency(metrics.revenue) }}</p>
        </div>
        <div class="card card-hover">
          <p class="text-[10px] font-bold text-muted uppercase tracking-widest mb-2">Monthly Expenses</p>
          <p class="text-2xl font-bold text-secondary">${{ formatCurrency(metrics.expenses) }}</p>
        </div>
        <div class="card card-hover">
          <p class="text-[10px] font-bold text-muted uppercase tracking-widest mb-2">Monthly Net Income</p>
          <p class="text-2xl font-bold" :class="metrics.net_income >= 0 ? 'text-primary' : 'text-error'">${{ formatCurrency(metrics.net_income) }}</p>
        </div>
        <div class="card card-hover">
          <p class="text-[10px] font-bold text-muted uppercase tracking-widest mb-2">Outstanding A/R</p>
          <p class="text-2xl font-bold text-on-surface">${{ formatCurrency(metrics.outstanding_ar) }}</p>
        </div>
        <div class="card card-hover">
          <p class="text-[10px] font-bold text-muted uppercase tracking-widest mb-2">Outstanding A/P</p>
          <p class="text-2xl font-bold text-on-surface">${{ formatCurrency(metrics.outstanding_ap) }}</p>
        </div>
        <div class="card card-hover">
          <p class="text-[10px] font-bold text-muted uppercase tracking-widest mb-2">Total Cash Balance</p>
          <p class="text-2xl font-bold text-primary">${{ formatCurrency(metrics.cash_balance) }}</p>
        </div>
      </div>

      <!-- Charts -->
      <div class="card">
        <h3 class="mb-6">Revenue vs Expenses (Last 6 Months)</h3>
        <div class="h-80 w-full">
          <Bar v-if="chartData.labels.length > 0" :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '../services/api'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const metrics = ref({
  revenue: 0,
  expenses: 0,
  net_income: 0,
  outstanding_ar: 0,
  outstanding_ap: 0,
  cash_balance: 0
})

const chartData = reactive({
  labels: [],
  datasets: []
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value) => '$' + value.toLocaleString()
      }
    }
  }
}

const loading = ref(true)
const error = ref(null)

const fetchData = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await api.get('/dashboard')
    const { metrics: resMetrics, monthly_data } = response.data
    metrics.value = resMetrics
    
    // Prepare chart data
    chartData.labels = monthly_data.map(d => d.month)
    chartData.datasets = [
      {
        label: 'Revenue',
        backgroundColor: '#10B981', // green-500
        data: monthly_data.map(d => d.revenue)
      },
      {
        label: 'Expenses',
        backgroundColor: '#EF4444', // red-500
        data: monthly_data.map(d => d.expenses)
      }
    ]
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
    error.value = 'Failed to load dashboard data. Please try again later.'
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value) => {
  if (value === undefined || value === null) return '0.00'
  return parseFloat(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(() => {
  fetchData()
})
</script>
