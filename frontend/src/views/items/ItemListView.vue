<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/items/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Add Item"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">Add Item</span>
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
              @click="showImportModal = true; showMoreMenu = false"
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
      title="Bulk Import Products & Services"
      upload-url="/items/bulk-import"
      :template-fields="['name', 'description', 'price', 'sellable', 'income_account_code', 'purchaseable', 'expense_account_code']"
      @close="showImportModal = false"
      @success="fetchItems"
    />

    <!-- Filters -->
    <div class="card flex gap-6">
      <div class="flex-1 max-w-sm">
        <label class="form-label">Search by Name</label>
        <input
          v-model="filters.name"
          @input="handleFilter"
          type="text"
          placeholder="Filter by name..."
          class="form-input"
        />
      </div>
      <div class="flex items-end pb-1 gap-4">
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="filters.sellable" @change="handleFilter" class="form-checkbox" />
          <span class="text-sm font-medium">Sellable</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="filters.purchaseable" @change="handleFilter" class="form-checkbox" />
          <span class="text-sm font-medium">Purchaseable</span>
        </label>
      </div>
    </div>

    <!-- Table -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th class="text-right">Price</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="item in items" 
            :key="item.id"
            @click="editItem(item.id)"
            class="cursor-pointer hover:bg-primary/8"
          >
            <td class="whitespace-nowrap font-medium text-on-surface">{{ item.name }}</td>
            <td class="truncate max-w-xs text-muted">{{ item.description || '-' }}</td>
            <td class="whitespace-nowrap text-right">${{ Number(item.price).toFixed(2) }}</td>
            <td class="whitespace-nowrap">
              <span v-if="item.sellable" class="badge-success mr-1">Sellable</span>
              <span v-if="item.purchaseable" class="badge-info">Purchaseable</span>
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <RouterLink
                  :to="`/items/${item.id}/edit`"
                  @click.stop
                  class="p-2 hover:bg-primary/8 rounded-full text-primary"
                  title="Edit"
                >
                  <span class="material-icons text-[20px]">edit</span>
                </RouterLink>
                <button
                  @click.stop="confirmDelete(item)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="5" class="px-6 py-10 text-center text-muted">
              No products or services found.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="px-6 py-4 flex items-center justify-between border-t border-divider">
        <div class="flex-1 flex justify-between sm:hidden">
          <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1" class="btn-secondary py-1 px-4">Previous</button>
          <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages" class="btn-secondary py-1 px-4">Next</button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-muted">
              Showing page <span class="font-bold text-on-surface">{{ currentPage }}</span> of <span class="font-bold text-on-surface">{{ totalPages }}</span>
            </p>
          </div>
          <div>
            <nav class="flex gap-2" aria-label="Pagination">
              <button
                v-for="p in totalPages"
                :key="p"
                @click="changePage(p)"
                class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold transition-colors"
                :class="p === currentPage ? 'bg-primary text-white' : 'text-muted hover:bg-primary/8'"
              >
                {{ p }}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import itemService from '../../services/itemService';
import BulkImportModal from '../../components/BulkImportModal.vue';

const router = useRouter();

const items = ref([]);
const currentPage = ref(1);
const totalPages = ref(1);
const showImportModal = ref(false);
const showMoreMenu = ref(false);

const toggleMoreMenu = () => {
  showMoreMenu.value = !showMoreMenu.value;
};

const closeMoreMenu = () => {
  showMoreMenu.value = false;
};
const filters = reactive({
  name: '',
  sellable: false,
  purchaseable: false,
});

const editItem = (id) => {
  router.push(`/items/${id}/edit`);
};

const fetchItems = async () => {
  try {
    const params = {
      page: currentPage.value,
      per_page: 10,
      name: filters.name,
    };
    if (filters.sellable) params.sellable = true;
    if (filters.purchaseable) params.purchaseable = true;

    const response = await itemService.getItems(params);
    items.value = response.data.items;
    totalPages.value = response.data.pages;
    currentPage.value = response.data.current_page;
  } catch (error) {
    console.error('Failed to fetch items:', error);
  }
};

const handleFilter = () => {
  currentPage.value = 1;
  fetchItems();
};

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchItems();
};

const confirmDelete = async (item) => {
  if (confirm(`Are you sure you want to delete item "${item.name}"?`)) {
    try {
      await itemService.deleteItem(item.id);
      fetchItems();
    } catch (error) {
      console.error('Failed to delete item:', error);
      const message = error.response?.data?.message || error.response?.data?.msg || 'Failed to delete item.';
      alert(message);
    }
  }
};

onMounted(() => {
  fetchItems();
  window.addEventListener('click', closeMoreMenu);
});

onUnmounted(() => {
  window.removeEventListener('click', closeMoreMenu);
});
</script>
