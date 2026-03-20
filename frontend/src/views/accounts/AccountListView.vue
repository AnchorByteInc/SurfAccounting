<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/settings/accounts/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Add Account"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">Add Account</span>
        </button>
        <div class="relative">
          <button
            @click.stop="toggleMoreMenu"
            class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8 text-primary"
            title="More Options"
          >
            <span class="material-icons">more_vert</span>
          </button>
          <div
            v-if="showMoreMenu"
            class="absolute right-0 mt-1 w-48 bg-white rounded-[14px] shadow-lg border border-gray-100 py-1 z-50"
          >
            <button
              @click="
                showImportModal = true;
                showMoreMenu = false;
              "
              class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-primary/5 flex items-center gap-2"
            >
              <span class="material-icons text-[18px]">upload_file</span>
              Bulk Import
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <BulkImportModal
      :is-open="showImportModal"
      title="Bulk Import Chart of Accounts"
      upload-url="/accounts/bulk-import"
      :template-fields="[
        'name',
        'code',
        'type',
        'subtype',
        'parent_code',
        'is_active',
      ]"
      @close="showImportModal = false"
      @success="fetchAccounts"
    />

    <!-- Hierarchy View -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Type</th>
            <th>Subtype</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="account in rootAccounts" :key="account.id">
            <AccountRow
              :account="account"
              :level="0"
              @refresh="fetchAccounts"
            />
          </template>
          <tr v-if="accounts.length === 0">
            <td colspan="6" class="px-6 py-10 text-center text-muted">
              No accounts found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import accountService from "../../services/accountService";
import AccountRow from "./AccountRow.vue";
import BulkImportModal from "../../components/BulkImportModal.vue";

const router = useRouter();
const accounts = ref([]);
const showImportModal = ref(false);
const showMoreMenu = ref(false);

const toggleMoreMenu = () => {
  showMoreMenu.value = !showMoreMenu.value;
};

const closeMoreMenu = () => {
  showMoreMenu.value = false;
};

const fetchAccounts = async () => {
  try {
    // Fetch a large number to get most accounts for the hierarchy
    const response = await accountService.getAccounts({ per_page: 1000 });
    accounts.value = response.data.accounts;
  } catch (error) {
    console.error("Failed to fetch accounts:", error);
  }
};

const rootAccounts = computed(() => {
  const accountMap = {};
  accounts.value.forEach((acc) => {
    accountMap[acc.id] = { ...acc, children: [] };
  });

  const roots = [];
  accounts.value.forEach((acc) => {
    if (acc.parent_id && accountMap[acc.parent_id]) {
      accountMap[acc.parent_id].children.push(accountMap[acc.id]);
    } else {
      roots.push(accountMap[acc.id]);
    }
  });

  // Sort by code
  const sortAccounts = (list) => {
    list.sort((a, b) => a.code.localeCompare(b.code));
    list.forEach((acc) => {
      if (acc.children.length > 0) {
        sortAccounts(acc.children);
      }
    });
  };

  sortAccounts(roots);
  return roots;
});

onMounted(() => {
  fetchAccounts();
  window.addEventListener("click", closeMoreMenu);
});

onUnmounted(() => {
  window.removeEventListener("click", closeMoreMenu);
});
</script>
