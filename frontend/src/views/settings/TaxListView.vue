<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/settings/taxes/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Add Tax"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">Add Tax</span>
        </button>
      </div>
    </Teleport>

    <!-- Table -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Rate</th>
            <th>Description</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="tax in taxes"
            :key="tax.id"
            @click="editTax(tax.id)"
            class="cursor-pointer hover:bg-primary/8"
          >
            <td class="whitespace-nowrap font-medium text-on-surface">
              {{ tax.name }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ (Number(tax.rate) * 100).toFixed(2) }}%
            </td>
            <td class="text-muted truncate max-w-xs">
              {{ tax.description || "-" }}
            </td>
            <td class="whitespace-nowrap">
              <span
                class="px-2 py-1 rounded-full text-xs font-bold"
                :class="
                  tax.is_active
                    ? 'bg-success/20 text-success'
                    : 'bg-error/20 text-error'
                "
              >
                {{ tax.is_active ? "Active" : "Inactive" }}
              </span>
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <RouterLink
                  :to="`/settings/taxes/${tax.id}/edit`"
                  @click.stop
                  class="p-2 hover:bg-primary/8 rounded-full text-primary"
                  title="Edit"
                >
                  <span class="material-icons text-[20px]">edit</span>
                </RouterLink>
                <button
                  @click.stop="confirmDelete(tax)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="taxes.length === 0">
            <td colspan="5" class="px-6 py-10 text-center text-muted">
              No taxes defined.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="px-6 py-4 flex items-center justify-between border-t border-divider"
      >
        <div>
          <p class="text-sm text-muted">
            Showing page
            <span class="font-bold text-on-surface">{{ currentPage }}</span> of
            <span class="font-bold text-on-surface">{{ totalPages }}</span>
          </p>
        </div>
        <div>
          <nav class="flex gap-2" aria-label="Pagination">
            <button
              v-for="p in totalPages"
              :key="p"
              @click="changePage(p)"
              class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold transition-colors"
              :class="
                p === currentPage
                  ? 'bg-primary text-white'
                  : 'text-muted hover:bg-primary/8'
              "
            >
              {{ p }}
            </button>
          </nav>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import taxService from "../../services/taxService";

const router = useRouter();
const taxes = ref([]);
const currentPage = ref(1);
const totalPages = ref(1);

const fetchTaxes = async () => {
  try {
    const response = await taxService.getTaxes({
      page: currentPage.value,
      per_page: 10,
    });
    taxes.value = response.data.taxes;
    totalPages.value = response.data.pages;
    currentPage.value = response.data.current_page;
  } catch (error) {
    console.error("Failed to fetch taxes:", error);
  }
};

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchTaxes();
};

const editTax = (id) => {
  router.push(`/settings/taxes/${id}/edit`);
};

const confirmDelete = async (tax) => {
  if (confirm(`Are you sure you want to delete tax "${tax.name}"?`)) {
    try {
      await taxService.deleteTax(tax.id);
      fetchTaxes();
    } catch (error) {
      console.error("Failed to delete tax:", error);
      alert("Failed to delete tax. It may be in use.");
    }
  }
};

onMounted(() => {
  fetchTaxes();
});
</script>
