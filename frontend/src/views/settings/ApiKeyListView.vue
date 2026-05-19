<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <router-link
          to="/settings/api-keys/new"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Create API Key"
        >
          <span class="material-icons text-[20px]">add</span>
          <span class="text-sm font-medium">Create API Key</span>
        </router-link>
      </div>
    </Teleport>

    <!-- Newly created key banner -->
    <div
      v-if="newlyCreatedKey"
      class="card border-2 border-warning/50 bg-warning/5"
    >
      <div class="flex items-start gap-3">
        <span class="material-icons text-warning text-[24px] mt-0.5"
          >warning</span
        >
        <div class="flex-1 min-w-0">
          <h3 class="m-0 mb-1 text-on-surface">
            Copy your API key now — it won't be shown again
          </h3>
          <div
            class="flex items-center gap-2 bg-surface-variant rounded-lg p-3 mt-2"
          >
            <code class="flex-1 text-sm break-all select-all font-mono">{{
              newlyCreatedKey
            }}</code>
            <button
              @click="copyKey"
              class="p-2 hover:bg-primary/8 rounded-full text-primary shrink-0"
              title="Copy to clipboard"
            >
              <span class="material-icons text-[20px]">{{
                copied ? "check" : "content_copy"
              }}</span>
            </button>
          </div>
          <button
            @click="newlyCreatedKey = null"
            class="mt-3 text-sm text-muted hover:text-on-surface"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Key Prefix</th>
            <th>Status</th>
            <th>Last Used</th>
            <th>Expires</th>
            <th>Created</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="key in apiKeys" :key="key.id" class="hover:bg-primary/8">
            <td class="whitespace-nowrap font-medium text-on-surface">
              {{ key.name }}
            </td>
            <td class="whitespace-nowrap text-muted font-mono">
              {{ key.key_prefix }}...
            </td>
            <td class="whitespace-nowrap">
              <span
                class="px-2 py-1 rounded-full text-xs font-bold"
                :class="statusClass(key)"
              >
                {{ statusLabel(key) }}
              </span>
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ key.last_used_at ? formatDate(key.last_used_at) : "Never" }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ key.expires_at ? formatDate(key.expires_at) : "Never" }}
            </td>
            <td class="whitespace-nowrap text-muted">
              {{ formatDate(key.created_at) }}
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <button
                  v-if="key.is_active"
                  @click.stop="confirmRevoke(key)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Revoke"
                >
                  <span class="material-icons text-[20px]">block</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="apiKeys.length === 0">
            <td colspan="7" class="px-6 py-10 text-center text-muted">
              No API keys yet. Create one to get started.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import apiKeyService from "../../services/apiKeyService";

const route = useRoute();
const apiKeys = ref([]);
const newlyCreatedKey = ref(null);
const copied = ref(false);

const fetchKeys = async () => {
  try {
    const response = await apiKeyService.getApiKeys();
    apiKeys.value = response.data;
  } catch (error) {
    console.error("Failed to fetch API keys:", error);
  }
};

const copyKey = async () => {
  try {
    await navigator.clipboard.writeText(newlyCreatedKey.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    // Fallback
    const el = document.createElement("textarea");
    el.value = newlyCreatedKey.value;
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  }
};

const confirmRevoke = async (key) => {
  if (confirm(`Are you sure you want to revoke API key "${key.name}"?`)) {
    try {
      await apiKeyService.revokeApiKey(key.id);
      fetchKeys();
    } catch (error) {
      console.error("Failed to revoke API key:", error);
      alert("Failed to revoke API key.");
    }
  }
};

const statusLabel = (key) => {
  if (!key.is_active) return "Revoked";
  if (key.is_expired) return "Expired";
  return "Active";
};

const statusClass = (key) => {
  if (!key.is_active) return "bg-error/20 text-error";
  if (key.is_expired) return "bg-warning/20 text-warning";
  return "bg-success/20 text-success";
};

const formatDate = (dateStr) => {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString();
};

onMounted(() => {
  if (route.query.newKey) {
    newlyCreatedKey.value = route.query.newKey;
    copied.value = false;
  }
  fetchKeys();
});
</script>
