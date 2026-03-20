import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import BaseLayout from "../components/BaseLayout.vue";

const routes = [
  {
    path: "/",
    component: BaseLayout,
    meta: { requiresAuth: true, pageTitle: "Dashboard" },
    children: [
      {
        path: "",
        name: "Home",
        component: () => import("../views/HomeView.vue"),
        meta: { pageTitle: "Dashboard" },
      },
      {
        path: "customers",
        name: "CustomerList",
        component: () => import("../views/customers/CustomerListView.vue"),
        meta: { pageTitle: "Customers" },
      },
      {
        path: "customers/new",
        name: "CustomerCreate",
        component: () => import("../views/customers/CustomerFormView.vue"),
        meta: { pageTitle: "New Customer", backPath: "/customers" },
      },
      {
        path: "customers/:id/edit",
        name: "CustomerEdit",
        component: () => import("../views/customers/CustomerFormView.vue"),
        meta: { pageTitle: "Edit Customer", backPath: "/customers" },
      },
      {
        path: "vendors",
        name: "VendorList",
        component: () => import("../views/vendors/VendorListView.vue"),
        meta: { pageTitle: "Vendors" },
      },
      {
        path: "vendors/new",
        name: "VendorCreate",
        component: () => import("../views/vendors/VendorFormView.vue"),
        meta: { pageTitle: "New Vendor", backPath: "/vendors" },
      },
      {
        path: "vendors/:id/edit",
        name: "VendorEdit",
        component: () => import("../views/vendors/VendorFormView.vue"),
        meta: { pageTitle: "Edit Vendor", backPath: "/vendors" },
      },
      {
        path: "items",
        name: "ItemList",
        component: () => import("../views/items/ItemListView.vue"),
        meta: { pageTitle: "Products & Services" },
      },
      {
        path: "items/new",
        name: "ItemCreate",
        component: () => import("../views/items/ItemFormView.vue"),
        meta: { pageTitle: "New Item", backPath: "/items" },
      },
      {
        path: "items/:id/edit",
        name: "ItemEdit",
        component: () => import("../views/items/ItemFormView.vue"),
        meta: { pageTitle: "Edit Item", backPath: "/items" },
      },
      {
        path: "invoices",
        name: "InvoiceList",
        component: () => import("../views/invoices/InvoiceListView.vue"),
        meta: { pageTitle: "Invoices" },
      },
      {
        path: "invoices/new",
        name: "InvoiceCreate",
        component: () => import("../views/invoices/InvoiceFormView.vue"),
        meta: { pageTitle: "New Invoice", backPath: "/invoices" },
      },
      {
        path: "invoices/:id/edit",
        name: "InvoiceEdit",
        component: () => import("../views/invoices/InvoiceFormView.vue"),
        meta: { pageTitle: "Edit Invoice", backPath: "/invoices" },
      },
      {
        path: "bills",
        name: "BillList",
        component: () => import("../views/bills/BillListView.vue"),
        meta: { pageTitle: "Bills" },
      },
      {
        path: "bills/new",
        name: "BillCreate",
        component: () => import("../views/bills/BillFormView.vue"),
        meta: { pageTitle: "New Bill", backPath: "/bills" },
      },
      {
        path: "bills/:id/edit",
        name: "BillEdit",
        component: () => import("../views/bills/BillFormView.vue"),
        meta: { pageTitle: "Edit Bill", backPath: "/bills" },
      },
      {
        path: "journals",
        name: "JournalList",
        component: () => import("../views/journals/JournalListView.vue"),
        meta: { pageTitle: "General Journal Entries" },
      },
      {
        path: "journals/new",
        name: "JournalCreate",
        component: () => import("../views/journals/JournalFormView.vue"),
        meta: { pageTitle: "New Journal Entry", backPath: "/journals" },
      },
      {
        path: "journals/:id/edit",
        name: "JournalEdit",
        component: () => import("../views/journals/JournalFormView.vue"),
        meta: { pageTitle: "Edit Journal Entry", backPath: "/journals" },
      },
      {
        path: "reports",
        name: "ReportsDashboard",
        component: () => import("../views/reports/ReportsDashboardView.vue"),
        meta: { pageTitle: "Financial Reports" },
      },
      {
        path: "reports/income-statement",
        name: "IncomeStatement",
        component: () => import("../views/reports/IncomeStatementView.vue"),
        meta: { pageTitle: "Income Statement", backPath: "/reports" },
      },
      {
        path: "reports/balance-sheet",
        name: "BalanceSheet",
        component: () => import("../views/reports/BalanceSheetView.vue"),
        meta: { pageTitle: "Balance Sheet", backPath: "/reports" },
      },
      {
        path: "reports/cash-flow",
        name: "CashFlow",
        component: () => import("../views/reports/CashFlowView.vue"),
        meta: { pageTitle: "Statement of Cash Flows", backPath: "/reports" },
      },
      {
        path: "reports/ar-aging",
        name: "ARAging",
        component: () => import("../views/reports/ARAgingView.vue"),
        meta: { pageTitle: "A/R Aging", backPath: "/reports" },
      },
      {
        path: "reports/ap-aging",
        name: "APAging",
        component: () => import("../views/reports/APAgingView.vue"),
        meta: { pageTitle: "A/P Aging", backPath: "/reports" },
      },
      {
        path: "reports/integrity-check",
        name: "IntegrityCheck",
        component: () => import("../views/reports/IntegrityCheckView.vue"),
        meta: { pageTitle: "Integrity Check", backPath: "/reports" },
      },
      {
        path: "settings",
        meta: { pageTitle: "Settings" },
        children: [
          {
            path: "",
            name: "Settings",
            component: () => import("../views/settings/SettingsView.vue"),
            meta: { pageTitle: "Settings" },
          },
          {
            path: "branding",
            name: "BrandingSettings",
            component: () =>
              import("../views/settings/BrandingSettingsView.vue"),
            meta: { pageTitle: "Branding & Business", backPath: "/settings" },
          },
          {
            path: "accounts",
            name: "AccountList",
            component: () => import("../views/accounts/AccountListView.vue"),
            meta: { pageTitle: "Chart of Accounts", backPath: "/settings" },
          },
          {
            path: "accounts/new",
            name: "AccountCreate",
            component: () => import("../views/accounts/AccountFormView.vue"),
            meta: { pageTitle: "New Account", backPath: "/settings/accounts" },
          },
          {
            path: "accounts/:id/edit",
            name: "AccountEdit",
            component: () => import("../views/accounts/AccountFormView.vue"),
            meta: { pageTitle: "Edit Account", backPath: "/settings/accounts" },
          },
          {
            path: "accounting-periods",
            name: "AccountingPeriodList",
            component: () =>
              import("../views/accounting_periods/AccountingPeriodListView.vue"),
            meta: { pageTitle: "Accounting Periods", backPath: "/settings" },
          },
          {
            path: "taxes",
            name: "TaxList",
            component: () => import("../views/settings/TaxListView.vue"),
            meta: { pageTitle: "Tax Management", backPath: "/settings" },
          },
          {
            path: "taxes/new",
            name: "TaxCreate",
            component: () => import("../views/settings/TaxFormView.vue"),
            meta: { pageTitle: "New Tax", backPath: "/settings/taxes" },
          },
          {
            path: "taxes/:id/edit",
            name: "TaxEdit",
            component: () => import("../views/settings/TaxFormView.vue"),
            meta: { pageTitle: "Edit Tax", backPath: "/settings/taxes" },
          },
          {
            path: "users",
            name: "UserList",
            component: () => import("../views/settings/UserListView.vue"),
            meta: { pageTitle: "User Management", backPath: "/settings" },
          },
          {
            path: "users/new",
            name: "UserCreate",
            component: () => import("../views/settings/UserFormView.vue"),
            meta: { pageTitle: "Add New User", backPath: "/settings/users" },
          },
        ],
      },
    ],
  },
  {
    path: "/invoices/:id/print",
    name: "InvoicePrint",
    component: () => import("../views/invoices/InvoicePrintView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/LoginView.vue"),
    meta: { requiresGuest: true },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    next("/login");
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next("/");
  } else {
    next();
  }
});

export default router;
