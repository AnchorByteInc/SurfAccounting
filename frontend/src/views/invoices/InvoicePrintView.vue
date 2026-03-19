<template>
  <div v-if="invoice" class="p-10 max-w-4xl mx-auto bg-white" id="printable-area">
    <div class="flex justify-between items-start border-b pb-8 mb-8">
      <div class="flex items-start gap-6">
        <div class="flex-shrink-0">
          <img v-if="settings?.invoice_logo_url" :src="getFullImageUrl(settings.invoice_logo_url)" :alt="settings.business_name" class="max-h-24 max-w-[200px] object-contain" />
          <img v-else :src="defaultLogo" alt="Surf Accounting" class="max-h-24 max-w-[200px] object-contain" />
        </div>
        <div>
          <h1 class="text-4xl font-bold text-gray-800 uppercase tracking-wide">Invoice</h1>
          <p class="mt-2 text-gray-600 font-medium"># {{ invoice.invoice_number }}</p>
        </div>
      </div>
      <div class="text-right">
        <h2 class="text-xl font-bold text-gray-800">{{ settings?.business_name || 'Your Business Name' }}</h2>
        <p class="text-gray-600">{{ settings?.address || '123 Business Rd' }}</p>
        <p class="text-gray-600">{{ settings?.city || 'City' }}, {{ settings?.state || 'ST' }} {{ settings?.zip || '12345' }}</p>
        <p class="text-gray-600">{{ settings?.email || 'email@example.com' }}</p>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-8 mb-12">
      <div>
        <h3 class="text-sm font-bold text-gray-500 uppercase mb-2">Bill To:</h3>
        <p class="text-lg font-bold text-gray-800">{{ invoice.customer?.name }}</p>
        <p class="text-gray-600">{{ invoice.customer?.email }}</p>
        <p class="text-gray-600">{{ invoice.customer?.phone }}</p>
        <p class="text-gray-600">{{ invoice.customer?.billing_address }}</p>
      </div>
      <div class="text-right">
        <div class="flex justify-end space-x-4">
          <span class="text-gray-500 font-bold uppercase text-xs">Invoice Date:</span>
          <span class="text-gray-800">{{ invoice.issue_date }}</span>
        </div>
        <div class="flex justify-end space-x-4 mt-1">
          <span class="text-gray-500 font-bold uppercase text-xs">Due Date:</span>
          <span class="text-gray-800">{{ invoice.due_date }}</span>
        </div>
        <div class="flex justify-end space-x-4 mt-1">
          <span class="text-gray-500 font-bold uppercase text-xs">Status:</span>
          <span class="text-gray-800 font-bold">{{ invoice.status.toUpperCase() }}</span>
        </div>
      </div>
    </div>

    <table class="w-full mb-12">
      <thead>
        <tr class="border-b-2 border-gray-300">
          <th class="py-3 text-left font-bold text-gray-700 uppercase text-sm">Description</th>
          <th class="py-3 text-right font-bold text-gray-700 uppercase text-sm w-24">Qty</th>
          <th class="py-3 text-right font-bold text-gray-700 uppercase text-sm w-32">Price</th>
          <th class="py-3 text-right font-bold text-gray-700 uppercase text-sm w-32">Total</th>
        </tr>
      </thead>
      <tbody class="divide-y">
        <tr v-for="line in invoice.lines" :key="line.id">
          <td class="py-4 text-gray-800">{{ line.description }}</td>
          <td class="py-4 text-right text-gray-800">{{ Number(line.quantity).toFixed(2) }}</td>
          <td class="py-4 text-right text-gray-800">${{ Number(line.unit_price).toFixed(2) }}</td>
          <td class="py-4 text-right text-gray-800 font-medium">${{ Number(line.line_total).toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>

    <div class="flex justify-end">
      <div class="w-64 space-y-3">
        <div class="flex justify-between text-sm">
          <span class="text-gray-600 font-bold uppercase">Subtotal:</span>
          <span class="text-gray-800 font-medium">${{ Number(invoice.subtotal).toFixed(2) }}</span>
        </div>
        <template v-if="invoice.tax_breakdown && invoice.tax_breakdown.length > 1">
          <div v-for="tax in invoice.tax_breakdown" :key="tax.id" class="flex justify-between text-sm">
            <span class="text-gray-600 font-bold uppercase">{{ tax.name }}:</span>
            <span class="text-gray-800 font-medium">${{ Number(tax.amount).toFixed(2) }}</span>
          </div>
        </template>
        <div v-else class="flex justify-between text-sm">
          <span class="text-gray-600 font-bold uppercase">Tax:</span>
          <span class="text-gray-800 font-medium">${{ Number(invoice.tax).toFixed(2) }}</span>
        </div>
        <div class="flex justify-between text-xl border-t-2 border-gray-800 pt-3">
          <span class="font-bold text-gray-800">TOTAL:</span>
          <span class="font-bold text-gray-800">${{ Number(invoice.total).toFixed(2) }}</span>
        </div>
        <div v-if="invoice.balance < invoice.total" class="flex justify-between text-sm text-green-600 font-bold">
          <span>Amount Paid:</span>
          <span>-${{ (Number(invoice.total) - Number(invoice.balance)).toFixed(2) }}</span>
        </div>
        <div class="flex justify-between text-lg font-bold bg-gray-100 p-2 rounded mt-2">
          <span class="text-gray-800">BALANCE DUE:</span>
          <span class="text-gray-900">${{ Number(invoice.balance).toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <div class="mt-20 pt-8 border-t text-center text-gray-500 text-xs">
      <p>Thank you for your business!</p>
      <p class="mt-1">Generated by Surf Accounting</p>
    </div>

    <!-- Print Button (hidden when printing) -->
    <div class="mt-12 no-print flex justify-center gap-4">
      <button
        @click="printInvoice"
        class="btn-primary"
      >
        <span class="material-icons">print</span>
        Print / Save as PDF
      </button>
      <button
        @click="$router.back()"
        class="btn-secondary"
      >
        Go Back
      </button>
    </div>
  </div>
  <div v-else class="flex justify-center items-center h-64">
    <p class="text-gray-500 animate-pulse">Loading invoice for print...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import invoiceService from '../../services/invoiceService';
import settingsService from '../../services/settingsService';
import { getFullImageUrl } from '../../utils/imageUtils';
import defaultLogo from '../../assets/logo.svg';

const route = useRoute();
const invoice = ref(null);
const settings = ref(null);

const fetchInvoice = async () => {
  try {
    const response = await invoiceService.getInvoice(route.params.id);
    invoice.value = response.data;
  } catch (error) {
    console.error('Failed to fetch invoice:', error);
  }
};

const fetchSettings = async () => {
  try {
    const response = await settingsService.getSettingsList();
    if (response.data.settings.length > 0) {
      settings.value = response.data.settings[0];
    }
  } catch (error) {
    console.error('Failed to fetch settings:', error);
  }
};

const printInvoice = () => {
  window.print();
};

onMounted(async () => {
  await Promise.all([fetchInvoice(), fetchSettings()]);
  // Optionally auto-trigger print dialog if preferred:
  // setTimeout(() => window.print(), 500);
});
</script>
